import pytest

from app.services.cost_calculator import calculate_cost, calculate_sheets, get_optimization_suggestions
from app.services.document_analyzer import parse_page_range


def test_parse_page_range_all():
    assert parse_page_range(None, 10) == list(range(1, 11))
    assert parse_page_range("all", 5) == [1, 2, 3, 4, 5]


def test_parse_page_range_specific():
    assert parse_page_range("1-3, 5", 10) == [1, 2, 3, 5]


def test_calculate_sheets():
    assert calculate_sheets(10, False) == 10
    assert calculate_sheets(10, True) == 5
    assert calculate_sheets(11, True) == 6


def test_calculate_cost_bw():
    cost, breakdown = calculate_cost(10, False, False)
    assert cost == 20.0
    assert breakdown["print_type"] == "bw_single"


def test_calculate_cost_color_double():
    cost, _ = calculate_cost(4, True, True)
    assert cost == 32.0


def test_optimization_suggestions():
    suggestions = get_optimization_suggestions(120, False, False)
    assert any("double-sided" in s for s in suggestions)
