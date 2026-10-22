"""Mark demo accounts and add single-use recovery code storage."""
from alembic import op
import sqlalchemy as sa

revision = "b1a2c3d4e5f6"
down_revision = "af167aab1877"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_users_role", "users", ["role"], unique=True)
    op.add_column("users", sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()))
    # Existing unencrypted accounts cannot silently become real accounts.
    op.execute("UPDATE users SET is_demo = true WHERE totp_secret NOT LIKE 'fernet:v1:%'")
    op.create_table("recovery_codes",
                    sa.Column("code_hash", sa.String(64), primary_key=True),
                    sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False))
    op.create_index("ix_recovery_codes_user_id", "recovery_codes", ["user_id"])


def downgrade():
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_recovery_codes_user_id", table_name="recovery_codes")
    op.drop_table("recovery_codes")
    op.drop_column("users", "is_demo")
