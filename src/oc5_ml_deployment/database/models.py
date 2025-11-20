"""
SQLAlchemy models for database tables.

Defines the schema for API requests and predictions logging.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from .database import Base


class APIRequest(Base):
    """
    Store metadata about API requests for audit and monitoring.

    Each request to prediction endpoints is logged here with metadata
    about the request and response.
    """

    __tablename__ = 'api_requests'

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Timestamps (UTC)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Request metadata
    endpoint = Column(String(100), nullable=False, index=True)
    request_data = Column(JSONB, nullable=False)  # Full request payload
    client_ip = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)

    # Response metadata
    http_status = Column(Integer, nullable=False, index=True)
    response_time_ms = Column(Integer, nullable=True)

    # Relationships (1:N - one request can have multiple predictions for batch)
    predictions = relationship(
        "Prediction",
        back_populates="request",
        cascade="all, delete-orphan",  # Delete predictions when request is deleted
        lazy="selectin"  # Eagerly load predictions with request
    )

    def __repr__(self):
        return f"<APIRequest(id={self.id}, endpoint={self.endpoint}, status={self.http_status})>"


class Prediction(Base):
    """
    Store prediction results for analytics and model monitoring.

    Each prediction (single or from batch) is stored here with the
    prediction result and model metadata.
    """

    __tablename__ = 'predictions'

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to API request
    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey('api_requests.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Timestamps (UTC)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    prediction_date = Column(DateTime(timezone=True), nullable=False)

    # Employee identifier (optional, from request if provided)
    employee_id = Column(String(50), nullable=True, index=True)

    # Prediction results
    attrition_prob = Column(Float, nullable=False)  # Probability of attrition (0-1)
    risk_level = Column(String(10), nullable=False, index=True)  # LOW, MEDIUM, HIGH
    model_version = Column(String(50), nullable=False, index=True)

    # Features snapshot (optional - for future analysis)
    features_snapshot = Column(JSONB, nullable=True)

    # Relationships (N:1 - each prediction belongs to one request)
    request = relationship("APIRequest", back_populates="predictions")

    # Constraints
    __table_args__ = (
        CheckConstraint('attrition_prob >= 0 AND attrition_prob <= 1', name='check_attrition_prob_range'),
        CheckConstraint("risk_level IN ('LOW', 'MEDIUM', 'HIGH')", name='check_risk_level_values'),
    )

    def __repr__(self):
        return f"<Prediction(id={self.id}, risk={self.risk_level}, prob={self.attrition_prob:.2f})>"
