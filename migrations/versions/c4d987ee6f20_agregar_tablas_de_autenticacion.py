"""Agregar tablas de autenticación y recuperación.

Revision ID: c4d987ee6f20
Revises: b6d93cba1993
"""

from alembic import op
import sqlalchemy as sa


revision = "c4d987ee6f20"
down_revision = "b6d93cba1993"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("rol", sa.String(30), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("token_version", sa.Integer(), nullable=False),
        sa.Column("intentos_fallidos", sa.Integer(), nullable=False),
        sa.Column("bloqueado_hasta", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_usuarios_id", "usuarios", ["id"])
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("familia_id", sa.String(36), nullable=False),
        sa.Column("revocado", sa.Boolean(), nullable=False),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_tokens_id", "refresh_tokens", ["id"])
    op.create_index("ix_refresh_tokens_usuario_id", "refresh_tokens", ["usuario_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_familia_id", "refresh_tokens", ["familia_id"])

    op.create_table(
        "tokens_recuperacion_usados",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jti", sa.String(36), nullable=False),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("consumido_en", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tokens_recuperacion_usados_id", "tokens_recuperacion_usados", ["id"])
    op.create_index("ix_tokens_recuperacion_usados_jti", "tokens_recuperacion_usados", ["jti"], unique=True)
    op.create_index("ix_tokens_recuperacion_usados_usuario_id", "tokens_recuperacion_usados", ["usuario_id"])


def downgrade() -> None:
    op.drop_table("tokens_recuperacion_usados")
    op.drop_table("refresh_tokens")
    op.drop_table("usuarios")
