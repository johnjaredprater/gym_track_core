"""Create tables

Revision ID: fed9de2bd443
Revises:
Create Date: 2024-12-12 20:58:44.951140

"""

from typing import Sequence, Union

import sqlalchemy as sa
from advanced_alchemy.types import GUID, DateTimeUTC

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fed9de2bd443"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "exercises",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("video_link", sa.String(length=100), nullable=True),
        sa.Column(
            "id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exercises")),
        sa.UniqueConstraint("name", name=op.f("uq_exercises_name")),
    )
    op.create_table(
        "workouts",
        sa.Column("user_id", sa.String(length=100), nullable=False),
        sa.Column("exercise_id", sa.BigInteger(), nullable=True),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("rpe", sa.Integer(), nullable=True),
        sa.Column("date", DateTimeUTC(timezone=True), nullable=False),
        sa.Column("id", GUID(length=16), nullable=False),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", DateTimeUTC(timezone=True), nullable=False),
        sa.Column("updated_at", DateTimeUTC(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercises.id"],
            name=op.f("fk_workouts_exercise_id_exercises"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_workouts")),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("workouts")
    op.drop_table("exercises")
    # ### end Alembic commands ###