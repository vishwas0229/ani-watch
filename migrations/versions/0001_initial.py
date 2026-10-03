"""Initial Ani-Watch schema."""

import sqlalchemy as sa  # noqa: I001
from alembic import op


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "anime",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("native_title", sa.String(length=300)),
        sa.Column("status", sa.String(length=50)),
        sa.Column("episodes", sa.Integer()),
        sa.Column("score", sa.Float()),
        sa.Column("genres", sa.Text(), nullable=False, server_default=""),
        sa.Column("season", sa.String(length=30)),
        sa.Column("year", sa.Integer()),
        sa.Column("format", sa.String(length=30)),
        sa.Column("description", sa.Text()),
        sa.Column("cover_url", sa.String(length=1000)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "episode",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "anime_id",
            sa.Integer(),
            sa.ForeignKey("anime.id", ondelete="CASCADE"),
        ),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500)),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("media_uri", sa.String(length=2000)),
        sa.Column("watched", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("anime_id", "number", name="uq_episode_anime_number"),
    )
    op.create_table(
        "favorite",
        sa.Column(
            "anime_id",
            sa.Integer(),
            sa.ForeignKey("anime.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "watch_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "anime_id",
            sa.Integer(),
            sa.ForeignKey("anime.id", ondelete="CASCADE"),
        ),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column("watched_at", sa.DateTime(timezone=True)),
        sa.Column(
            "progress_seconds",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("duration_seconds", sa.Integer()),
    )
    op.create_table(
        "progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "anime_id",
            sa.Integer(),
            sa.ForeignKey("anime.id", ondelete="CASCADE"),
        ),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column(
            "position_seconds",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint(
            "anime_id",
            "episode_number",
            name="uq_progress_episode",
        ),
    )
    op.create_table(
        "settings",
        sa.Column("key", sa.String(length=120), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    for table in (
        "settings",
        "progress",
        "watch_history",
        "favorite",
        "episode",
        "anime",
    ):
        op.drop_table(table)
