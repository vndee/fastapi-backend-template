import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

import orjson
from redis_data_structures import SerializableType
from sqlalchemy import Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class BaseModel(Base, SerializableType):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def to_dict(self) -> dict[str, Any]:
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_sa_"):
                if hasattr(value, "to_dict"):
                    result[key] = value.to_dict()
                elif isinstance(value, list) and value and hasattr(value[0], "to_dict"):
                    result[key] = [item.to_dict() for item in value]
                else:
                    result[key] = value

        return result

    def to_json(self) -> str:
        return orjson.dumps(self.to_dict()).decode("utf-8")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseModel":
        filtered_data = {k: v for k, v in data.items() if not k.startswith("_sa_")}
        return cls(**filtered_data)

    @classmethod
    def from_json(cls, data: str) -> "BaseModel":
        return cls.from_dict(orjson.loads(data))
