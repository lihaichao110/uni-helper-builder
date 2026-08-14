"""initial schema"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Models are the single source of truth for the initial schema. This keeps
    # SQLite development and PostgreSQL deployment aligned.
    from app.database import Base
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=op.get_bind())


def downgrade():
    from app.database import Base
    from app import models  # noqa: F401
    Base.metadata.drop_all(bind=op.get_bind())

