from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.persistence.database import Base


class ApiKeyModel(Base):
    __tablename__ = "api_keys"
    __table_args__ = (
        Index(
            "ix_api_keys_prefix",
            "key_prefix",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )

    id_api_key: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    key_prefix: Mapped[str] = mapped_column(String(11), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="active"
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )