# finance_tools.py — Free/local replacement for Auto.dev finance & TCO calls
import math
from typing import List, Dict

def _get_apr_for_credit_score(credit_score: int) -> float:
    """
    Rough APR table based on public data (Bankrate, Experian).
    These are averages — values may differ by lender and location.
    """
    apr_table = [
        (750, 4.5),
        (700, 6.0),
        (650, 8.0),
        (600, 12.0)
    ]
    for threshold, apr in apr_table:
        if credit_score >= threshold:
            return apr
    return 15.0  # worst case for very low scores


def _calculate_monthly_payment(price: float, down_payment: float, term_months: int, apr: float) -> float:
    """
    Calculate the monthly payment using the fixed-rate loan formula.
    P = (r * L) / (1 - (1 + r)^-n)
    """
    loan_amount = max(price - down_payment, 0)
    monthly_rate = apr / 100 / 12
    if monthly_rate == 0:
        return loan_amount / term_months
    return (monthly_rate * loan_amount) / (1 - math.pow(1 + monthly_rate, -term_months))


def _estimate_maintenance_cost(vehicle_age: int) -> float:
    """
    Annual maintenance estimate from AAA averages:
    ~ $600 per year for newer vehicles, rising with age.
    """
    base = 600
    # Add $50/year after year 5
    if vehicle_age > 5:
        base += (vehicle_age - 5) * 50
    return base


def _estimate_depreciation(price: float, years: int = 5) -> float:
    """
    Estimate total depreciation over N years using average truck/SUV curve.
    Trucks/SUVs typically lose about 45-50% of value in 5 years.
    """
    rate_drop = 0.45 if years >= 5 else 0.09 * years
    return round(price * rate_drop, 2)


def enrich_listings_with_finance_and_tco(
    listings: List[Dict],
    down_payment: float,
    loan_term_months: int,
    credit_score: int
) -> List[Dict]:
    """
    Enrich inventory listings with offline financing, maintenance, and depreciation data.
    This replaces the paid Auto.dev TCO API.
    """
    apr = _get_apr_for_credit_score(credit_score)

    enriched = []
    for car in listings:
        price = car.get("price") or 0
        vehicle_age = car.get("vehicle_age", 0) or 0

        monthly_payment = round(
            _calculate_monthly_payment(price, down_payment, loan_term_months, apr),
            2
        )
        annual_maintenance = _estimate_maintenance_cost(vehicle_age)
        depreciation_5yr = _estimate_depreciation(price, years=5)

        enriched.append({
            **car,
            "apr": apr,
            "monthly_payment": monthly_payment,
            "annual_maintenance_est": annual_maintenance,
            "depreciation_5yr_est": depreciation_5yr,
            "total_5yr_cost": round(
                (monthly_payment * 12 * 5) + (annual_maintenance * 5) + depreciation_5yr,
                2
            )
        })

    return enriched
