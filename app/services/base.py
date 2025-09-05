import uuid
from typing import Any, Dict, Generic, Optional, Type, TypeVar

from pydantic import BaseModel as PydanticBaseModel

from app.core.logger import get_logger
from app.models.base import BaseModel
from app.repositories.base import BaseRepository
from app.schemas.base import PaginatedResponseSchema, PaginationSchema

logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=PydanticBaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=PydanticBaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=PydanticBaseModel)


class BaseService(
    Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]
):
    """
    Base service class that provides common CRUD operations for domain entities.

    This class acts as an intermediary between the API layer and the repository layer,
    implementing business logic, validation, and data transformation.

    Type Parameters:
        ModelType: The SQLAlchemy model type
        CreateSchemaType: Pydantic schema for creation requests
        UpdateSchemaType: Pydantic schema for update requests
        ResponseSchemaType: Pydantic schema for responses
    """

    def __init__(
        self,
        repository: BaseRepository[ModelType],
        response_schema: Type[ResponseSchemaType],
    ):
        self.repository = repository
        self.response_schema = response_schema

    async def get_by_id(self, id: uuid.UUID) -> Optional[ResponseSchemaType]:
        """
        Get an entity by its ID.

        Args:
            id: The unique identifier of the entity

        Returns:
            The entity if found, None otherwise
        """
        logger.info(
            f"Getting {self.repository.model.__name__} by ID: {id}",
            operation="get_by_id",
        )

        entity = self.repository.get(id)
        if entity:
            return self.response_schema.model_validate(entity.to_dict())

        logger.warning(
            f"{self.repository.model.__name__} with ID {id} not found",
            operation="get_by_id",
        )
        return None

    async def get_by_filters(
        self, filters: Dict[str, Any]
    ) -> Optional[ResponseSchemaType]:
        """
        Get an entity by applying filters.

        Args:
            filters: Dictionary of filters to apply

        Returns:
            The first entity matching the filters, None if not found
        """
        logger.info(
            f"Getting {self.repository.model.__name__} by filters: {filters}",
            operation="get_by_filters",
        )

        entity = self.repository.get_by_filters(filters)
        if entity:
            return self.response_schema.model_validate(entity.to_dict())

        logger.warning(
            f"{self.repository.model.__name__} with filters {filters} not found",
            operation="get_by_filters",
        )
        return None

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[Dict[str, str]] = None,
        include_count: bool = False,
    ) -> PaginatedResponseSchema[ResponseSchemaType]:
        """
        Get multiple entities with optional pagination, filtering, and searching.

        Args:
            skip: Number of records to skip (pagination offset)
            limit: Maximum number of records to return
            filters: Dictionary of exact match filters
            search: Dictionary of search terms for fuzzy matching
            include_count: Whether to return paginated response with total count

        Returns:
            List of entities or paginated response with total count
        """
        logger.info(
            f"Getting multiple {self.repository.model.__name__} - "
            f"skip: {skip}, limit: {limit}, filters: {filters}, search: {search}",
            operation="get_multi",
        )

        if include_count:
            result = self.repository.get_multi(
                skip=skip, limit=limit, filters=filters, search=search, count=True
            )
            entities, total = result
            items = [
                self.response_schema.model_validate(entity.to_dict())
                for entity in entities
            ]

            return PaginatedResponseSchema(
                items=items,
                pagination=PaginationSchema(
                    offset=skip,
                    limit=limit,
                    total=total,
                ),
            )
        else:
            result = self.repository.get_multi(
                skip=skip, limit=limit, filters=filters, search=search, count=False
            )
            # Type check to ensure we got a list, not a tuple
            if isinstance(result, tuple):
                entities, _ = result
            else:
                entities = result
            return PaginatedResponseSchema(
                items=[
                    self.response_schema.model_validate(entity.to_dict())
                    for entity in entities
                ],
                pagination=PaginationSchema(
                    offset=skip, limit=limit, total=len(entities)
                ),
            )

    async def create(
        self, obj_in: CreateSchemaType, current_user_id: Optional[uuid.UUID] = None
    ) -> ResponseSchemaType:
        """
        Create a new entity.

        Args:
            obj_in: The creation schema with entity data
            current_user_id: ID of the user creating the entity (for audit trail)

        Returns:
            The created entity

        Raises:
            Any validation or business logic exceptions
        """
        logger.info(
            f"Creating new {self.repository.model.__name__}", operation="create"
        )

        # Prepare creation data
        obj_data = obj_in.model_dump(exclude_unset=True)

        # Add audit information if provided
        if current_user_id:
            obj_data["created_by"] = current_user_id
            obj_data["updated_by"] = current_user_id

        # Perform pre-creation validation/business logic
        await self._validate_create(obj_data)

        # Create the entity
        entity = self.repository.create(obj_data)

        # Perform post-creation actions
        await self._post_create(entity)

        logger.info(
            f"Successfully created {self.repository.model.__name__} with ID: {entity.id}",
            operation="create",
        )
        return self.response_schema.model_validate(entity.to_dict())

    async def update(
        self,
        id: uuid.UUID,
        obj_in: UpdateSchemaType,
        current_user_id: Optional[uuid.UUID] = None,
    ) -> Optional[ResponseSchemaType]:
        """
        Update an existing entity.

        Args:
            id: The ID of the entity to update
            obj_in: The update schema with new entity data
            current_user_id: ID of the user updating the entity (for audit trail)

        Returns:
            The updated entity if found and updated, None if not found

        Raises:
            Any validation or business logic exceptions
        """
        logger.info(
            f"Updating {self.repository.model.__name__} with ID: {id}",
            operation="update",
        )

        # Check if entity exists
        existing_entity = self.repository.get(id)
        if not existing_entity:
            logger.warning(
                f"{self.repository.model.__name__} with ID {id} not found for update",
                operation="update",
            )
            return None

        # Prepare update data
        obj_data = obj_in.model_dump(exclude_unset=True)

        # Add audit information if provided
        if current_user_id:
            obj_data["updated_by"] = current_user_id

        # Perform pre-update validation/business logic
        await self._validate_update(id, obj_data, existing_entity)

        # Update the entity
        updated_entity = self.repository.update(id, obj_data)

        if updated_entity:
            # Perform post-update actions
            await self._post_update(updated_entity, existing_entity)

            logger.info(
                f"Successfully updated {self.repository.model.__name__} with ID: {id}",
                operation="update",
            )
            return self.response_schema.model_validate(updated_entity.to_dict())

        return None

    async def delete(
        self, id: uuid.UUID, current_user_id: Optional[uuid.UUID] = None
    ) -> bool:
        """
        Delete an entity.

        Args:
            id: The ID of the entity to delete
            current_user_id: ID of the user deleting the entity (for audit trail)

        Returns:
            True if the entity was deleted, False if not found

        Raises:
            Any validation or business logic exceptions
        """
        logger.info(
            f"Deleting {self.repository.model.__name__} with ID: {id}",
            operation="delete",
        )

        # Check if entity exists and get it for potential post-delete actions
        existing_entity = self.repository.get(id)
        if not existing_entity:
            logger.warning(
                f"{self.repository.model.__name__} with ID {id} not found for deletion",
                operation="delete",
            )
            return False

        # Perform pre-delete validation/business logic
        await self._validate_delete(id, existing_entity)

        # Delete the entity
        deleted = self.repository.delete(id)

        if deleted:
            # Perform post-delete actions
            await self._post_delete(existing_entity)

            logger.info(
                f"Successfully deleted {self.repository.model.__name__} with ID: {id}",
                operation="delete",
            )

        return deleted

    async def soft_delete(
        self, id: uuid.UUID, current_user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResponseSchemaType]:
        """
        Soft delete an entity by setting is_active to False.

        Args:
            id: The ID of the entity to soft delete
            current_user_id: ID of the user soft deleting the entity

        Returns:
            The soft deleted entity if found and updated, None if not found
        """
        logger.info(
            f"Soft deleting {self.repository.model.__name__} with ID: {id}",
            operation="soft_delete",
        )

        # Check if entity exists
        existing_entity = self.repository.get(id)
        if not existing_entity:
            logger.warning(
                f"{self.repository.model.__name__} with ID {id} not found for soft deletion",
                operation="soft_delete",
            )
            return None

        # Perform pre-soft-delete validation
        await self._validate_soft_delete(id, existing_entity)

        # Prepare update data for soft delete
        update_data: Dict[str, Any] = {"is_active": False}
        if current_user_id:
            update_data["updated_by"] = current_user_id

        # Update the entity
        updated_entity = self.repository.update(id, update_data)

        if updated_entity:
            # Perform post-soft-delete actions
            await self._post_soft_delete(updated_entity)

            logger.info(
                f"Successfully soft deleted {self.repository.model.__name__} with ID: {id}",
                operation="soft_delete",
            )
            return self.response_schema.model_validate(updated_entity.to_dict())

        return None

    async def restore(
        self, id: uuid.UUID, current_user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResponseSchemaType]:
        """
        Restore a soft deleted entity by setting is_active to True.

        Args:
            id: The ID of the entity to restore
            current_user_id: ID of the user restoring the entity

        Returns:
            The restored entity if found and updated, None if not found
        """
        logger.info(
            f"Restoring {self.repository.model.__name__} with ID: {id}",
            operation="restore",
        )

        # Get entity including soft deleted ones
        existing_entity = self.repository.get(id)
        if not existing_entity:
            logger.warning(
                f"{self.repository.model.__name__} with ID {id} not found for restoration",
                operation="restore",
            )
            return None

        # Perform pre-restore validation
        await self._validate_restore(id, existing_entity)

        # Prepare update data for restore
        update_data: Dict[str, Any] = {"is_active": True}
        if current_user_id:
            update_data["updated_by"] = current_user_id

        # Update the entity
        updated_entity = self.repository.update(id, update_data)

        if updated_entity:
            # Perform post-restore actions
            await self._post_restore(updated_entity)

            logger.info(
                f"Successfully restored {self.repository.model.__name__} with ID: {id}",
                operation="restore",
            )
            return self.response_schema.model_validate(updated_entity.to_dict())

        return None

    async def exists(self, id: uuid.UUID) -> bool:
        """
        Check if an entity exists.

        Args:
            id: The ID of the entity to check

        Returns:
            True if the entity exists, False otherwise
        """
        return self.repository.get(id) is not None

    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[Dict[str, str]] = None,
    ) -> int:
        """
        Count entities matching the given criteria.

        Args:
            filters: Dictionary of exact match filters
            search: Dictionary of search terms for fuzzy matching

        Returns:
            Number of entities matching the criteria
        """
        result = self.repository.get_multi(
            skip=0, limit=1, filters=filters, search=search, count=True
        )
        _, total = result
        return total

    # Hook methods for subclasses to override for custom business logic

    async def _validate_create(self, obj_data: Dict[str, Any]) -> None:
        """
        Override this method to add custom validation logic before creating an entity.

        Args:
            obj_data: The data to be used for creation

        Raises:
            ValidationError or any custom exception for validation failures
        """
        pass

    async def _validate_update(
        self, id: uuid.UUID, obj_data: Dict[str, Any], existing_entity: ModelType
    ) -> None:
        """
        Override this method to add custom validation logic before updating an entity.

        Args:
            id: The ID of the entity being updated
            obj_data: The data to be used for update
            existing_entity: The current entity from the database

        Raises:
            ValidationError or any custom exception for validation failures
        """
        pass

    async def _validate_delete(self, id: uuid.UUID, existing_entity: ModelType) -> None:
        """
        Override this method to add custom validation logic before deleting an entity.

        Args:
            id: The ID of the entity being deleted
            existing_entity: The entity to be deleted

        Raises:
            ValidationError or any custom exception for validation failures
        """
        pass

    async def _validate_soft_delete(
        self, id: uuid.UUID, existing_entity: ModelType
    ) -> None:
        """
        Override this method to add custom validation logic before soft deleting an entity.

        Args:
            id: The ID of the entity being soft deleted
            existing_entity: The entity to be soft deleted

        Raises:
            ValidationError or any custom exception for validation failures
        """
        pass

    async def _validate_restore(
        self, id: uuid.UUID, existing_entity: ModelType
    ) -> None:
        """
        Override this method to add custom validation logic before restoring an entity.

        Args:
            id: The ID of the entity being restored
            existing_entity: The entity to be restored

        Raises:
            ValidationError or any custom exception for validation failures
        """
        pass

    async def _post_create(self, entity: ModelType) -> None:
        """
        Override this method to add custom logic after creating an entity.

        Args:
            entity: The newly created entity
        """
        pass

    async def _post_update(self, entity: ModelType, previous_entity: ModelType) -> None:
        """
        Override this method to add custom logic after updating an entity.

        Args:
            entity: The updated entity
            previous_entity: The entity before the update
        """
        pass

    async def _post_delete(self, entity: ModelType) -> None:
        """
        Override this method to add custom logic after deleting an entity.

        Args:
            entity: The deleted entity
        """
        pass

    async def _post_soft_delete(self, entity: ModelType) -> None:
        """
        Override this method to add custom logic after soft deleting an entity.

        Args:
            entity: The soft deleted entity
        """
        pass

    async def _post_restore(self, entity: ModelType) -> None:
        """
        Override this method to add custom logic after restoring an entity.

        Args:
            entity: The restored entity
        """
        pass
