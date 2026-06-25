import math
from typing import Any

from app.config import settings
from app.services.document_analyzer import parse_page_range


def calculate_sheets(pages: int, double_sided: bool) -> int:
    if pages <= 0:
        return 0
    if double_sided:
        return math.ceil(pages / 2)
    return pages


def calculate_cost(pages: int, is_color: bool, is_double_sided: bool) -> tuple[float, dict[str, Any]]:
    if is_color:
        rate = settings.PRICE_COLOR_DOUBLE if is_double_sided else settings.PRICE_COLOR_SINGLE
        print_type = "color_double" if is_double_sided else "color_single"
    else:
        rate = settings.PRICE_BW_DOUBLE if is_double_sided else settings.PRICE_BW_SINGLE
        print_type = "bw_double" if is_double_sided else "bw_single"

    cost = round(pages * rate, 2)
    sheets = calculate_sheets(pages, is_double_sided)
    breakdown = {
        "pages": pages,
        "sheets": sheets,
        "rate_per_page": rate,
        "print_type": print_type,
        "is_color": is_color,
        "is_double_sided": is_double_sided,
    }
    return cost, breakdown


def get_optimization_suggestions(total_pages: int, is_color: bool, is_double_sided: bool) -> list[str]:
    suggestions: list[str] = []

    if not is_double_sided and total_pages >= 4:
        sheets_saved = total_pages - calculate_sheets(total_pages, True)
        suggestions.append(
            f"Printing {total_pages} pages double-sided will save {sheets_saved} sheet(s)."
        )

    if is_color and total_pages >= 10:
        bw_cost, _ = calculate_cost(total_pages, False, is_double_sided)
        color_cost, _ = calculate_cost(total_pages, True, is_double_sided)
        savings = round(color_cost - bw_cost, 2)
        suggestions.append(
            f"Switching to B&W would save ₹{savings} for this job."
        )

    if total_pages > 50 and not is_double_sided:
        suggestions.append("Consider printing in batches with double-sided for large documents.")

    return suggestions


def estimate_print(
    total_pages: int,
    page_range: str | None,
    is_color: bool,
    is_double_sided: bool,
) -> tuple[int, int, float, dict[str, Any], list[str]]:
    selected = parse_page_range(page_range, total_pages)
    pages_to_print = len(selected)
    sheets = calculate_sheets(pages_to_print, is_double_sided)
    cost, breakdown = calculate_cost(pages_to_print, is_color, is_double_sided)
    suggestions = get_optimization_suggestions(pages_to_print, is_color, is_double_sided)
    return pages_to_print, sheets, cost, breakdown, suggestions
