"""Initial schema for API requests and predictions logging

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-11-19 18:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create api_requests and predictions tables."""

    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create api_requests table
    op.create_table(
        'api_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('endpoint', sa.String(length=100), nullable=False),
        sa.Column('request_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('client_ip', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('http_status', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_api_requests')
    )

    # Create indexes for api_requests
    op.create_index('idx_api_requests_created_at', 'api_requests', ['created_at'])
    op.create_index('idx_api_requests_endpoint', 'api_requests', ['endpoint'])
    op.create_index('idx_api_requests_http_status', 'api_requests', ['http_status'])

    # Create predictions table
    op.create_table(
        'predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('prediction_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('employee_id', sa.String(length=50), nullable=True),
        sa.Column('attrition_prob', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(length=10), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('features_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint('attrition_prob >= 0 AND attrition_prob <= 1', name='check_attrition_prob_range'),
        sa.CheckConstraint("risk_level IN ('LOW', 'MEDIUM', 'HIGH')", name='check_risk_level_values'),
        sa.ForeignKeyConstraint(['request_id'], ['api_requests.id'], ondelete='CASCADE', name='fk_predictions_request'),
        sa.PrimaryKeyConstraint('id', name='pk_predictions')
    )

    # Create indexes for predictions
    op.create_index('idx_predictions_created_at', 'predictions', ['created_at'])
    op.create_index('idx_predictions_request_id', 'predictions', ['request_id'])
    op.create_index('idx_predictions_risk_level', 'predictions', ['risk_level'])
    op.create_index('idx_predictions_model_version', 'predictions', ['model_version'])
    op.create_index('idx_predictions_employee_id', 'predictions', ['employee_id'])


def downgrade() -> None:
    """Drop predictions and api_requests tables."""

    # Drop tables (reverse order due to FK constraint)
    op.drop_table('predictions')
    op.drop_table('api_requests')

    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
