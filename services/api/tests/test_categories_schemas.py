import pytest
from pydantic import ValidationError

from app.features.categories.schemas import CategoryCreate, CategoryUpdate


class TestCategoryCreateName:
    def test_strips_whitespace(self) -> None:
        schema = CategoryCreate(name="  Food  ", color="#FF0000", expense_group="card")
        assert schema.name == "Food"

    def test_blank_raises(self) -> None:
        with pytest.raises(ValidationError):
            CategoryCreate(name="   ", color="#FF0000", expense_group="card")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValidationError):
            CategoryCreate(name="", color="#FF0000", expense_group="card")


class TestCategoryCreateColor:
    def test_valid_hex(self) -> None:
        schema = CategoryCreate(name="Food", color="#1A2B3C", expense_group="card")
        assert schema.color == "#1A2B3C"

    def test_invalid_hex_raises(self) -> None:
        with pytest.raises(ValidationError):
            CategoryCreate(name="Food", color="red", expense_group="card")

    def test_missing_hash_raises(self) -> None:
        with pytest.raises(ValidationError):
            CategoryCreate(name="Food", color="FF0000", expense_group="card")

    def test_short_hex_raises(self) -> None:
        with pytest.raises(ValidationError):
            CategoryCreate(name="Food", color="#FFF", expense_group="card")


class TestCategoryUpdateName:
    def test_strips_whitespace(self) -> None:
        schema = CategoryUpdate(name="  Transport  ")
        assert schema.name == "Transport"

    def test_none_allowed(self) -> None:
        assert CategoryUpdate(name=None).name is None

    def test_omitted_is_none(self) -> None:
        assert CategoryUpdate().name is None

    def test_blank_raises(self) -> None:
        with pytest.raises(ValidationError):
            CategoryUpdate(name="  ")


class TestCategoryUpdateColor:
    def test_valid_hex(self) -> None:
        assert CategoryUpdate(color="#AABBCC").color == "#AABBCC"

    def test_none_allowed(self) -> None:
        assert CategoryUpdate(color=None).color is None

    def test_invalid_hex_raises(self) -> None:
        with pytest.raises(ValidationError):
            CategoryUpdate(color="blue")
