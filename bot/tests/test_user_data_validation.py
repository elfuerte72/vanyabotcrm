"""Tests for CollectedUserData Pydantic validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models.user_data import CollectedUserData


class TestCollectedUserData:
    """Test CollectedUserData validation."""

    def test_valid_data(self, sample_user_data: dict) -> None:
        data = CollectedUserData.model_validate(sample_user_data)
        assert data.sex == "male"
        assert data.weight == 80
        assert data.height == 180
        assert data.age == 30
        assert data.activity_level == "moderate"
        assert data.goal == "weight_loss"
        assert data.allergies == "none"
        assert data.excluded_foods == "none"

    def test_defaults_for_optional_fields(self) -> None:
        data = CollectedUserData(
            sex="female",
            weight=60,
            height=165,
            age=25,
            activity_level="light",
            goal="maintenance",
        )
        assert data.allergies == "none"
        assert data.excluded_foods == "none"

    def test_weight_too_low(self) -> None:
        with pytest.raises(ValidationError, match="weight must be 20-300"):
            CollectedUserData(
                sex="male", weight=5, height=180, age=30,
                activity_level="moderate", goal="weight_loss",
            )

    def test_weight_too_high(self) -> None:
        with pytest.raises(ValidationError, match="weight must be 20-300"):
            CollectedUserData(
                sex="male", weight=400, height=180, age=30,
                activity_level="moderate", goal="weight_loss",
            )

    def test_height_too_low(self) -> None:
        with pytest.raises(ValidationError, match="height must be 80-250"):
            CollectedUserData(
                sex="male", weight=80, height=50, age=30,
                activity_level="moderate", goal="weight_loss",
            )

    def test_age_too_low(self) -> None:
        with pytest.raises(ValidationError, match="age must be 10-120"):
            CollectedUserData(
                sex="male", weight=80, height=180, age=5,
                activity_level="moderate", goal="weight_loss",
            )

    def test_age_too_high(self) -> None:
        with pytest.raises(ValidationError, match="age must be 10-120"):
            CollectedUserData(
                sex="male", weight=80, height=180, age=150,
                activity_level="moderate", goal="weight_loss",
            )

    def test_invalid_sex(self) -> None:
        with pytest.raises(ValidationError):
            CollectedUserData(
                sex="other", weight=80, height=180, age=30,
                activity_level="moderate", goal="weight_loss",
            )

    def test_invalid_activity_level(self) -> None:
        with pytest.raises(ValidationError):
            CollectedUserData(
                sex="male", weight=80, height=180, age=30,
                activity_level="super", goal="weight_loss",
            )

    def test_invalid_goal(self) -> None:
        with pytest.raises(ValidationError):
            CollectedUserData(
                sex="male", weight=80, height=180, age=30,
                activity_level="moderate", goal="bulk",
            )

    def test_missing_required_field(self) -> None:
        with pytest.raises(ValidationError):
            CollectedUserData(
                sex="male", weight=80, height=180,
                activity_level="moderate", goal="weight_loss",
            )

    def test_boundary_weight_valid(self) -> None:
        data = CollectedUserData(
            sex="male", weight=20, height=80, age=10,
            activity_level="sedentary", goal="maintenance",
        )
        assert data.weight == 20
        assert data.height == 80
        assert data.age == 10

    def test_all_activity_levels(self) -> None:
        for level in ("sedentary", "light", "moderate", "high", "extreme"):
            data = CollectedUserData(
                sex="female", weight=60, height=165, age=25,
                activity_level=level, goal="maintenance",
            )
            assert data.activity_level == level

    def test_all_goals(self) -> None:
        for goal in ("weight_loss", "maintenance", "muscle_gain"):
            data = CollectedUserData(
                sex="female", weight=60, height=165, age=25,
                activity_level="moderate", goal=goal,
            )
            assert data.goal == goal
