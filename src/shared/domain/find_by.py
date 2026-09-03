from dataclasses import dataclass
from enum import StrEnum
from typing import Generic, TypeVar

from src.shared.domain.pagination import KeysetCursor


T = TypeVar("T")


class FindByOperator(StrEnum):
    """Operators supported by generated find-by endpoints."""

    EQUALS = "equals"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"


@dataclass(frozen=True)
class FindByCriteria:
    """Validated search input, independent of HTTP and the ORM."""

    field: str
    operator: FindByOperator
    value: object


@dataclass(frozen=True)
class FindByResult(Generic[T]):
    """Bounded or keyset-paginated search result."""

    items: list[T]
    next_position: KeysetCursor | None
    has_next: bool
