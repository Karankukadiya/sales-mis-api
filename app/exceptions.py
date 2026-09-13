"""Domain and application exceptions.

Provides custom exception hierarchies for clean error propagation across
the service and web layers.
"""


class AppException(Exception):
    """Base exception for all domain and application-level errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class EntityNotFoundException(AppException):
    """Exception raised when an entity requested by ID does not exist."""

    def __init__(self, entity_name: str, entity_id: int) -> None:
        message = f"{entity_name} with ID {entity_id} was not found"
        super().__init__(message)
        self.entity_name = entity_name
        self.entity_id = entity_id


class BusinessRuleViolationException(AppException):
    """Exception raised when an operation violates domain business rules."""
    pass
