"""Repositories package exporting BaseRepository and SalesRepository."""

from app.repositories.base import BaseRepository
from app.repositories.sales_repository import SalesRepository

__all__ = ["BaseRepository", "SalesRepository"]
