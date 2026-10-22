"""Explicitly provision fictional local fixtures. Never used at application startup."""
import json
from uuid import uuid4
import pyotp
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import GateConfig, User
from .security import normalize, passwords
from .config import Settings
from .secret_box import load_box


def seed(engine, box=None):
    settings = Settings.from_env()
    if settings.secure:
        raise RuntimeError("Demo seeding is forbidden in secure mode")
    box = box or load_box(settings)
    with Session(engine) as db:
        if db.scalar(select(User.id).limit(1)) or db.get(GateConfig, 1):
            raise RuntimeError("Refusing to overwrite an initialized database")
        for role in ("OWNER", "READER"):
            user_id = str(uuid4())
            db.add(User(id=user_id, username="demo-" + role.lower(), role=role, is_demo=True,
                        password_hash=passwords.hash("fictional-demo-only"),
                        totp_secret=box.encrypt("JBSWY3DPEHPK3PXP", user_id)))
        questions = [
            {"id": "planet", "prompt": "Demo: which planet has rings?", "weight": 2, "answer": "saturn"},
            {"id": "drink", "prompt": "Demo: tea or coffee?", "weight": 1, "answer": "tea"},
        ]
        for question in questions:
            question["hash"] = passwords.hash(normalize(question.pop("answer")))
        db.add(GateConfig(id=1, questions_json=json.dumps(questions), threshold=3,
                          anniversary_hash=passwords.hash("2020-01-01"),
                          name_hash=passwords.hash("alex example")))
        db.commit()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["seed", "code"])
    args = parser.parse_args()
    if args.action == "seed":
        from .main import app
        seed(app.state.engine)
        print("Fictional accounts created. See docs/local-development.md.")
    else:
        print(pyotp.TOTP("JBSWY3DPEHPK3PXP").now())
