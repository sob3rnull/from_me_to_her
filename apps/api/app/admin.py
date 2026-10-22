"""Local operator commands. Passwords, answers and recovery codes never use argv."""
import argparse
import getpass
import json
from uuid import uuid4

import pyotp
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from .accounts import enroll, replace_factor
from .config import Settings
from .models import AuditEvent, BrowserSession, GateConfig, User
from .secret_box import PREFIX, load_box
from .security import normalize, now, passwords


def encrypt_legacy_secrets(db, box):
    changed = 0
    for user in db.scalars(select(User)):
        if user.totp_secret.startswith(PREFIX):
            box.decrypt(user.totp_secret, user.id)  # Wrong key must fail, not overwrite.
        else:
            pyotp.TOTP(user.totp_secret).now()  # Reject malformed legacy secrets.
            user.totp_secret = box.encrypt(user.totp_secret, user.id)
            changed += 1
    if changed:
        db.execute(delete(BrowserSession))
    db.commit()
    return changed


def configure_gates(db, questions, threshold, anniversary, full_name):
    if not 1 <= len(questions) <= 10 or not 1 <= threshold <= sum(q["weight"] for q in questions):
        raise ValueError("Invalid question count or threshold")
    encoded = []
    for index, question in enumerate(questions):
        if not 1 <= question["weight"] <= 10 or not question["prompt"].strip() or not 1 <= len(normalize(question["answer"])) <= 200:
            raise ValueError("Each question needs a prompt, answer and weight between 1 and 10")
        encoded.append({"id": str(index + 1), "prompt": question["prompt"], "weight": question["weight"],
                        "hash": passwords.hash(normalize(question["answer"]))})
    from datetime import date
    date.fromisoformat(anniversary)
    if not 1 <= len(normalize(full_name)) <= 200:
        raise ValueError("Full name must contain 1–200 characters")
    row = db.get(GateConfig, 1) or GateConfig(id=1)
    row.questions_json = json.dumps(encoded)
    row.threshold = threshold
    row.anniversary_hash = passwords.hash(normalize(anniversary))
    row.name_hash = passwords.hash(normalize(full_name))
    db.add(row)
    db.execute(delete(BrowserSession).where(BrowserSession.user_id.is_(None)))
    db.add(AuditEvent(id=str(uuid4()), action="GATES_CONFIGURED", created_at=now()))
    db.commit()


def confirmed_secret(username):
    secret = pyotp.random_base32()
    print("Add this URI to your authenticator privately (do not share or commit it):")
    print(pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name="from_me_to_her"))
    return secret, getpass.getpass("Code from the new authenticator: ").strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("keygen", help="Print a fresh Fernet key; store outside Git")
    commands.add_parser("encrypt-secrets", help="Encrypt legacy demo secrets and revoke old sessions")
    commands.add_parser("configure-gates", help="Enter private gate questions and answers interactively")
    create = commands.add_parser("enroll", help="Create one owner or reader after TOTP confirmation")
    create.add_argument("--username", required=True)
    create.add_argument("--role", choices=["OWNER", "READER"], required=True)
    replace = commands.add_parser("replace-factor", help="Replace lost TOTP using password and an unused recovery code")
    replace.add_argument("--username", required=True)
    args = parser.parse_args()
    if args.command == "keygen":
        print(Fernet.generate_key().decode())
        return
    settings = Settings.from_env()
    box = load_box(settings)
    engine = create_engine(settings.database_url)
    try:
        with Session(engine) as db:
            if args.command == "encrypt-secrets":
                print(f"Encrypted {encrypt_legacy_secrets(db, box)} legacy secrets.")
            elif args.command == "configure-gates":
                count = int(input("Number of questions (1–10): "))
                if not 1 <= count <= 10:
                    raise ValueError("Question count must be 1–10")
                questions = [{"prompt": input(f"Question {index + 1}: "),
                              "answer": getpass.getpass("Answer: "),
                              "weight": int(input("Weight (1–10): "))} for index in range(count)]
                threshold = int(input("Passing score: "))
                anniversary = getpass.getpass("Anniversary (YYYY-MM-DD): ")
                full_name = getpass.getpass("His full name: ")
                configure_gates(db, questions, threshold, anniversary, full_name)
                print("Gate configuration saved; previous gate progress invalidated.")
            else:
                password = getpass.getpass("Password: ")
                if args.command == "enroll" and password != getpass.getpass("Confirm password: "):
                    raise ValueError("Passwords do not match")
                recovery = getpass.getpass("Unused recovery code: ").strip() if args.command == "replace-factor" else None
                secret, confirmation = confirmed_secret(args.username)
                if args.command == "enroll":
                    codes = enroll(db, box, args.username, args.role, password, secret, confirmation)
                else:
                    codes = replace_factor(db, box, args.username, password, recovery, secret, confirmation)
                print("Save these recovery codes privately. They are displayed only once:")
                print("\n".join(codes))
                print("Wait for the next authenticator code before signing in.")
    except ValueError as error:
        parser.exit(1, f"{error}\n")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
