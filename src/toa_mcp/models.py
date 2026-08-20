"""Pydantic output schemas. Returning these from tools gives MCP structured output."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class StandardSummary(BaseModel):
    key: str
    title: str


class StandardList(BaseModel):
    count: int
    standards: list[StandardSummary]


class StandardDoc(BaseModel):
    key: str
    title: str
    section: str | None = None
    content: str
    lines: int


class RoutedCategory(BaseModel):
    category: str
    guidance: str


class TaskRouting(BaseModel):
    task: str
    matched: int
    categories: list[RoutedCategory]
    hint: str | None = None


class InfraProfile(BaseModel):
    app: str
    content: str


class AppList(BaseModel):
    count: int
    apps: list[str]


class EnvDoc(BaseModel):
    host: str
    content: str


class Brand(BaseModel):
    brand: str
    data: dict[str, Any]


class BrandList(BaseModel):
    count: int
    brands: list[str]


class TokenScale(BaseModel):
    name: str
    css: str


class TokenScaleList(BaseModel):
    count: int
    scales: list[str]


class Finding(BaseModel):
    rule: str
    line: int
    text: str
    message: str


class ValidationResult(BaseModel):
    framework: str
    clean: bool
    violation_count: int
    findings: list[Finding]


class DesignStylesPointer(BaseModel):
    """Where the 14 named web design styles live (toa-agents, not this server)."""

    count: int = 14
    home: str
    styles: list[str]
    note: str
