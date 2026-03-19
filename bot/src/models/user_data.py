"""Pydantic model for validating data collected by AI agent."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator


class CollectedUserData(BaseModel):
    """Validated user data from AI agent's JSON output."""

    sex: Literal["male", "female"]
    weight: float
    height: float
    age: int
    activity_level: Literal["sedentary", "light", "moderate", "high", "extreme"]
    goal: Literal["weight_loss", "maintenance", "muscle_gain"]
    allergies: str = "none"
    excluded_foods: str = "none"

    @field_validator("weight")
    @classmethod
    def weight_in_range(cls, v: float) -> float:
        if not 20 <= v <= 300:
            raise ValueError(f"weight must be 20-300 kg, got {v}")
        return v

    @field_validator("height")
    @classmethod
    def height_in_range(cls, v: float) -> float:
        if not 80 <= v <= 250:
            raise ValueError(f"height must be 80-250 cm, got {v}")
        return v

    @field_validator("age")
    @classmethod
    def age_in_range(cls, v: int) -> int:
        if not 10 <= v <= 120:
            raise ValueError(f"age must be 10-120, got {v}")
        return v
