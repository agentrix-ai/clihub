"""Unified Operation model — the atomic unit every CLI tool maps to."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Operation(BaseModel):
    """A single invokable tool across any provider."""

    id: str = Field(description="Fully qualified id: provider.category.name")
    provider: str
    category: str
    name: str
    description: str = ""
    description_en: str = ""
    keywords: list[str] = Field(default_factory=list)
    argv_template: list[str] = Field(
        default_factory=list,
        description="Command argv, e.g. ['lark-cli','calendar','+agenda']",
    )
    input_schema: dict | None = Field(
        default=None, description="JSON Schema for arguments"
    )
    example: str = ""
    auth_required: bool = True

    @property
    def search_text(self) -> str:
        """Concatenated text blob used by the search engine."""
        parts = [
            self.id,
            self.description,
            self.description_en,
            self.category,
            self.name,
            *self.keywords,
        ]
        return " ".join(parts)
