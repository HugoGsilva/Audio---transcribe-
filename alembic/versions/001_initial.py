"""Initial database schema

Revision ID: 001_initial
Revises: 
Create Date: 2025-12-13

This migration creates all base tables for the Careca.ai application:
- users: User accounts and authentication
- transcription_tasks: Transcription job tracking
- global_config: Application-wide settings
- analysis_rules: Dynamic analysis rule definitions
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('username', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('full_name', sa.String(200), nullable=True),
        sa.Column('hashed_password', sa.String(200), nullable=False),
        sa.Column('is_active', sa.Boolean, default=False),
        sa.Column('is_admin', sa.Boolean, default=False),
        sa.Column('transcription_limit', sa.Integer, default=100),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
    )
    
    # Transcription tasks table
    op.create_table(
        'transcription_tasks',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('task_id', sa.String(36), unique=True, nullable=False, index=True),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('status', sa.String(50), default='queued'),
        sa.Column('progress', sa.Integer, default=0),
        sa.Column('result_text', sa.Text, nullable=True),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('topics', sa.Text, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('duration', sa.Float, nullable=True),
        sa.Column('analysis_status', sa.String(50), default='Pendente de análise'),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('options', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('owner_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
    )
    
    # Global config table
    op.create_table(
        'global_config',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('key', sa.String(100), unique=True, nullable=False),
        sa.Column('value', sa.Text, nullable=True),
    )
    
    # Analysis rules table (Tier 3)
    op.create_table(
        'analysis_rules',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),  # positive, negative, critical
        sa.Column('keywords', sa.Text, nullable=False),  # JSON array
        sa.Column('product', sa.String(100), nullable=True),  # e.g., "Capitalização", "QLD"
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
    )


def downgrade() -> None:
    op.drop_table('analysis_rules')
    op.drop_table('global_config')
    op.drop_table('transcription_tasks')
    op.drop_table('users')
