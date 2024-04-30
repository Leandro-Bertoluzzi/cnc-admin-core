"""remove rejected status from tasks

Revision ID: 5269cf543947
Revises: 3235826a58f1
Create Date: 2024-04-25 22:08:49.727388

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql.expression import literal


# revision identifiers, used by Alembic.
revision = '5269cf543947'
down_revision = '3235826a58f1'
branch_labels = None
depends_on = None


# Describing of enum
enum_name = "task_status"
temp_enum_name = f"temp_{enum_name}"
new_values = (
    "pending_approval",
    "on_hold",
    "in_progress",
    "finished",
    "cancelled",
    "failed"
)
old_values = ("rejected", *new_values)
old_type = sa.Enum(*old_values, name=enum_name)
new_type = sa.Enum(*new_values, name=enum_name)
temp_type = sa.Enum(*new_values, name=temp_enum_name)


# Describing of table
table_name = "tasks"
column_name = "status"


def upgrade() -> None:
    # Convert 'rejected' status into 'cancelled'
    table = sa.sql.table('tasks', sa.Column('status'))
    op.execute(
        table
        .update()
        .where(table.columns.status == 'rejected')
        .values(status=literal('cancelled', type_=old_type))
    )

    # temp type to use instead of old one
    temp_type.create(op.get_bind(), checkfirst=False)

    # changing of column type from old enum to new one.
    with op.batch_alter_table('tasks') as batch_op:
        batch_op.alter_column(
            column_name,
            existing_type=old_type,
            type_=temp_type,
            existing_nullable=False,
            postgresql_using=f"{column_name}::text::{temp_enum_name}"
        )

    # remove old enum, create new enum
    old_type.drop(op.get_bind(), checkfirst=False)
    new_type.create(op.get_bind(), checkfirst=False)

    # changing of column type from temp enum to new one.
    with op.batch_alter_table('tasks') as batch_op:
        batch_op.alter_column(
            column_name,
            existing_type=temp_type,
            type_=new_type,
            existing_nullable=False,
            postgresql_using=f"{column_name}::text::{enum_name}"
        )

    # remove temp enum
    temp_type.drop(op.get_bind(), checkfirst=False)


def downgrade() -> None:
    # Restore 'rejected' value in type
    temp_type.create(op.get_bind(), checkfirst=False)

    with op.batch_alter_table('tasks') as batch_op:
        batch_op.alter_column(
            column_name,
            existing_type=new_type,
            type_=temp_type,
            existing_nullable=False,
            postgresql_using=f"{column_name}::text::{temp_enum_name}"
        )

    new_type.drop(op.get_bind(), checkfirst=False)
    old_type.create(op.get_bind(), checkfirst=False)

    with op.batch_alter_table('tasks') as batch_op:
        batch_op.alter_column(
            column_name,
            existing_type=temp_type,
            type_=old_type,
            existing_nullable=False,
            postgresql_using=f"{column_name}::text::{enum_name}"
        )

    temp_type.drop(op.get_bind(), checkfirst=False)
