"""Add indexes for library queries."""
from alembic import op
import sqlalchemy as sa

revision = "91a2b3c4d5e6"
down_revision = "457a88d383a3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_books_author", "books", ["author"])
    op.create_index("ix_loans_member_id", "loans", ["member_id"])
    op.create_index("ix_loans_book_id", "loans", ["book_id"])
    op.create_index("ix_loans_active_borrowed_at", "loans", ["borrowed_at"], postgresql_where=sa.text("returned_at IS NULL"))


def downgrade():
    op.drop_index("ix_loans_active_borrowed_at", table_name="loans")
    op.drop_index("ix_loans_book_id", table_name="loans")
    op.drop_index("ix_loans_member_id", table_name="loans")
    op.drop_index("ix_books_author", table_name="books")
