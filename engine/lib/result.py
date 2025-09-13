from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")


@dataclass
class Ok(Generic[T]):
    """Represents a successful result."""

    value: T


@dataclass
class Err(Generic[E]):
    """Represents a failed result."""

    error: E


Result = Union[Ok[T], Err[E]]

__all__ = ["Ok", "Err", "Result"]
