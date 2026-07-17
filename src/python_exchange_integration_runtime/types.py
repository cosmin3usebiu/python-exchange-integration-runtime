"""Shared type aliases for the exchange integration runtime."""

from __future__ import annotations

from typing import Mapping, TypeAlias

QueryParameterValue: TypeAlias = str | int | float | bool
PathParameterValue: TypeAlias = str | int
HeaderMapping: TypeAlias = Mapping[str, str]
QueryParameterMapping: TypeAlias = Mapping[str, QueryParameterValue]
PathParameterMapping: TypeAlias = Mapping[str, PathParameterValue]
PayloadType: TypeAlias = object | None
