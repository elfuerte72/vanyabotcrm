from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class User:
    chat_id: int
    username: str | None = None
    first_name: str | None = None
    sex: str | None = None
    age: int | None = None
    weight: float | None = None
    height: float | None = None
    activity_level: str | None = None
    goal: str | None = None
    allergies: str | None = None
    excluded_foods: str | None = None
    calories: int | None = None
    protein: int | None = None
    fats: int | None = None
    carbs: int | None = None
    get_food: bool = False
    is_buyer: bool = False
    funnel_stage: int = 0
    language: str = "en"
    id_ziina: str | None = None
    type_ziina: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    funnel_start_at: datetime | None = None
    last_funnel_msg_at: datetime | None = None
    next_funnel_msg_at: datetime | None = None

    @classmethod
    def from_row(cls, row: Any) -> User:
        return cls(
            chat_id=int(row["chat_id"]),
            username=row.get("username"),
            first_name=row.get("first_name"),
            sex=row.get("sex"),
            age=row.get("age"),
            weight=float(row["weight"]) if row.get("weight") is not None else None,
            height=float(row["height"]) if row.get("height") is not None else None,
            activity_level=row.get("activity_level"),
            goal=row.get("goal"),
            allergies=row.get("allergies"),
            excluded_foods=row.get("excluded_foods"),
            calories=row.get("calories"),
            protein=row.get("protein"),
            fats=row.get("fats"),
            carbs=row.get("carbs"),
            get_food=bool(row.get("get_food", False)),
            is_buyer=bool(row.get("is_buyer", False)),
            funnel_stage=int(row.get("funnel_stage", 0)),
            language=row.get("language", "en"),
            id_ziina=row.get("id_ziina"),
            type_ziina=row.get("type_ziina"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            funnel_start_at=row.get("funnel_start_at"),
            last_funnel_msg_at=row.get("last_funnel_msg_at"),
            next_funnel_msg_at=row.get("next_funnel_msg_at"),
        )
