"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-20

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "taxonomy_nodes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("taxonomy_type", sa.String(32), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("breadcrumb", sa.Text(), nullable=True),
        sa.Column("depth", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_taxonomy_nodes_taxonomy_type", "taxonomy_nodes", ["taxonomy_type"])
    op.create_index("ix_taxonomy_nodes_code", "taxonomy_nodes", ["code"])
    # HNSW index for fast cosine similarity search
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_taxonomy_nodes_embedding_hnsw "
        "ON taxonomy_nodes USING hnsw (embedding vector_cosine_ops)"
    )

    op.create_table(
        "classification_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.String(256), nullable=False),
        sa.Column("taxonomy_type", sa.String(32), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("code", sa.String(64), nullable=True),
        sa.Column("name", sa.String(256), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False, server_default=""),
        sa.Column("model_used", sa.String(64), nullable=False),
        sa.Column("hitl_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_classification_results_product_id", "classification_results", ["product_id"])

    op.create_table(
        "corrections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("result_id", sa.Integer(), nullable=False),
        sa.Column("correct_code", sa.String(64), nullable=False),
        sa.Column("correct_name", sa.String(256), nullable=False),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column("corrected_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["result_id"], ["classification_results.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_corrections_result_id", "corrections", ["result_id"])

    op.create_table(
        "classification_audit",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("result_id", sa.Integer(), nullable=True),
        sa.Column("event", sa.String(64), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_classification_audit_result_id", "classification_audit", ["result_id"])
    op.create_index("ix_classification_audit_timestamp", "classification_audit", ["timestamp"])


def downgrade() -> None:
    op.drop_table("classification_audit")
    op.drop_table("corrections")
    op.drop_table("classification_results")
    op.drop_index("ix_taxonomy_nodes_embedding_hnsw", table_name="taxonomy_nodes")
    op.drop_table("taxonomy_nodes")
