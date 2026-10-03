"""Initial Ani-Watch schema."""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "anime",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("anilist_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("native_title", sa.String(length=255)),
        sa.Column("status", sa.String(length=50)),
        sa.Column("episodes", sa.Integer()),
        sa.Column("score", sa.Float()),
        sa.Column("genres", sa.Text(), nullable=False, server_default=""),
        sa.Column("cover_url", sa.Text()),
        sa.Column("site_url", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_anime_anilist_id", "anime", ["anilist_id"], unique=False)

    op.create_table(
        "episode",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("anime_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255)),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("source_uri", sa.Text()),
        sa.Column("local_path", sa.Text()),
        sa.Column("watched", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["anime_id"], ["anime.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_episode_anime_id", "episode", ["anime_id"], unique=False)

    op.create_table(
        "watch_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("anime_id", sa.Integer(), nullable=False),
        sa.Column("episode_id", sa.Integer(), nullable=False),
        sa.Column("progress_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("watched_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["anime_id"], ["anime.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["episode_id"], ["episode.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_watch_history_episode_id", "watch_history", ["episode_id"], unique=False)
    op.create_index("ix_watch_history_watched_at", "watch_history", ["watched_at"], unique=False)

    op.create_table(
        "favorite",
        sa.Column("anime_id", sa.Integer(), primary_key=True),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["anime_id"], ["anime.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "setting",
        sa.Column("key", sa.String(length=255), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("setting")
    op.drop_table("favorite")
    op.drop_index("ix_watch_history_watched_at", table_name="watch_history")
    op.drop_index("ix_watch_history_episode_id", table_name="watch_history")
    op.drop_table("watch_history")
    op.drop_index("ix_episode_anime_id", table_name="episode")
    op.drop_table("episode")
    op.drop_index("ix_anime_anilist_id", table_name="anime")
    op.drop_table("anime")
