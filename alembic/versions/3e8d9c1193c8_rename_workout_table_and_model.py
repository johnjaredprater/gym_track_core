"""rename_workout_table_and_model

Revision ID: 3e8d9c1193c8
Revises: fed9de2bd443
Create Date: 2025-04-18 21:02:21.263856

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3e8d9c1193c8"
down_revision: Union[str, None] = "fed9de2bd443"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("workouts", "exercise_results")


def downgrade() -> None:
    op.rename_table("exercise_results", "workouts")
