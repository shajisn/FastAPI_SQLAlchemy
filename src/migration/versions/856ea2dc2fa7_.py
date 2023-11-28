"""empty message

Revision ID: 856ea2dc2fa7
Revises: 177979a1ffd0
Create Date: 2023-11-24 21:14:49.762987

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '856ea2dc2fa7'
down_revision: Union[str, None] = '177979a1ffd0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE VIEW dashboard_view AS
        SELECT task.task_id, task.file_name, project.project_name,
               task.task_status, task.created_at, task.task_duration,
               task.preprocess_path, task.destination_path
        FROM task
        JOIN project ON task.project = project.project_id
    """)


def downgrade() -> None:
     op.execute("DROP VIEW IF EXISTS dashboard_view")
    
