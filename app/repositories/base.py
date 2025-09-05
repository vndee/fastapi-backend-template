import uuid
from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.models.base import BaseModel

logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db
        self.model = model

    def get(self, id: uuid.UUID) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_by_filters(self, filters: Dict[str, Any]) -> Optional[ModelType]:
        return self.db.query(self.model).filter_by(**filters).first()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[Dict[str, str]] = None,
        count: bool = False,
    ) -> List[ModelType] | Tuple[List[ModelType], int]:
        query = self.db.query(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.filter(getattr(self.model, key) == value)

        if search:
            for key, value in search.items():
                if hasattr(self.model, key) and value is not None:
                    column = getattr(self.model, key)
                    like_pattern = f"%{value}%"
                    # Case-insensitive and accent-insensitive search using unaccent + ILIKE
                    query = query.filter(
                        func.unaccent(column).ilike(func.unaccent(like_pattern))
                    )

        if count:
            total = query.count()
            items = query.offset(skip).limit(limit).all()
            return items, total

        return query.offset(skip).limit(limit).all()

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, id: uuid.UUID, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        db_obj = self.get(id)
        if db_obj:
            for key, value in obj_in.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)

            self.db.commit()
            self.db.refresh(db_obj)

        return db_obj

    def delete(self, id: uuid.UUID) -> bool:
        db_obj = self.get(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True

        return False
