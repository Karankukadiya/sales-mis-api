"""Base service defining the standard structure for domain services.

Demonstrates OOP Abstraction by encapsulating the relationship between
services and their underlying repositories.
"""

from typing import Generic, TypeVar

RepoType = TypeVar("RepoType")


class BaseService(Generic[RepoType]):
    """Generic base service class encapsulating repository access.

    Attributes:
        repository (RepoType): Strongly typed repository instance.
    """

    def __init__(self, repository: RepoType) -> None:
        """Initialize service with injected repository dependency."""
        self._repository = repository

    @property
    def repository(self) -> RepoType:
        """Expose repository for service methods."""
        return self._repository
