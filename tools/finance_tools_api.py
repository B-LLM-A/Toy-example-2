import requests
import os
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

AUTO_DEV_API_KEY = os.getenv("AUTO_DEV_API_KEY")

# ---------- Financing ----------
class CalculateFinancingInput(BaseModel):
    vin: str = Field(..., description="Vehicle VIN number")
    car_price: float = Field(..., description="Total price of the car in USD")
    down_payment: float = Field(..., description="Upfront payment reducing loan amount")
    loan_term_months: int = Field(..., description="Loan term in months (36, 48, 60, 72, 84)")
    year: int = Field(..., description="Vehicle year")
    make: str = Field(..., description="Vehicle make")
    model: str = Field(..., description="Vehicle model")
    zip: str = Field(..., description="ZIP code for borrower")
    credit_score: int = Field(..., description="Credit score of borrower")
    vehicle_age: int = Field(..., description="Age of vehicle in years")
    vehicle_mileage: int = Field(..., description="Mileage of vehicle")


def calculate_financing_func(
    vin, car_price, down_payment, loan_term_months,
    year, make, model, zip, credit_score, vehicle_age, vehicle_mileage
):
    loan_amount = car_price - down_payment
    url = f"https://api.auto.dev/apr/{vin}"
    headers = {
        "Authorization": f"Bearer {AUTO_DEV_API_KEY}",
        "Content-Type": "application/json"
    }
    params = {
        "year": year,
        "make": make,
        "model": model,
        "zip": zip,
        "creditScore": str(credit_score),
        "vehicleAge": vehicle_age,
        "vehicleMileage": str(vehicle_mileage)
    }

    resp = requests.get(url, headers=headers, params=params)
    data = resp.json()

    apr_data = data.get("apr", {})
    rate = apr_data.get(str(loan_term_months))
    if rate is None:
        return {"error": f"APR for {loan_term_months} months not available."}

    monthly_rate = rate / 12 / 100
    monthly_payment = (loan_amount * monthly_rate) / (1 - (1 + monthly_rate) ** (-loan_term_months))
    total_cost = monthly_payment * loan_term_months

    return {
        "vin": vin,
        "loan_amount": loan_amount,
        "apr": rate,
        "monthly_payment": round(monthly_payment, 2),
        "total_cost": round(total_cost, 2)
    }


calculate_financing = StructuredTool.from_function(
    name="calculate_financing",
    description="Calculate financing details using Auto.dev v2 Interest Rates API (VIN-based). Returns APR, monthly payment, and total cost.",
    func=calculate_financing_func,
    args_schema=CalculateFinancingInput
)

# ---------- Leasing ----------
class CalculateLeaseInput(BaseModel):
    car_price: float
    residual_value: float
    money_factor: float
    lease_term_months: int

def calculate_lease_func(car_price, residual_value, money_factor, lease_term_months):
    depreciation = (car_price - residual_value) / lease_term_months
    finance_charge = (car_price + residual_value) * money_factor
    monthly_payment = depreciation + finance_charge
    return {
        "monthly_payment": round(monthly_payment, 2),
        "depreciation": round(depreciation, 2),
        "finance_charge": round(finance_charge, 2)
    }

calculate_lease = StructuredTool.from_function(
    name="calculate_lease",
    description="Calculate lease payment details",
    func=calculate_lease_func,
    args_schema=CalculateLeaseInput
)

# ---------- Maintenance ----------
class GetMaintenanceInput(BaseModel):
    vin: str = Field(..., description="Vehicle VIN number")
    zip: str = Field(..., description="ZIP code where ownership cost is calculated")
    from_zip: str = Field(..., description="ZIP code from where the vehicle is transported to the owner")

def get_maintenance_cost_func(vin, zip, from_zip):
    url = f"https://api.auto.dev/tco/{vin}"
    params = {"zip": zip, "fromZip": from_zip}
    headers = {
        "Authorization": f"Bearer {AUTO_DEV_API_KEY}",
        "Content-Type": "application/json"
    }
    resp = requests.get(url, params=params, headers=headers)
    data = resp.json()

    tco_data = data.get("tco", {})
    return {
        "annual_maintenance_cost": tco_data.get("maintenance"),
        "repair_cost": tco_data.get("repairs"),
        "total_5yr_cost": tco_data.get("total", {}).get("tcoPrice")
    }

get_maintenance_cost = StructuredTool.from_function(
    name="get_maintenance_cost",
    description="Fetch maintenance, repair costs and total 5-year cost using Auto.dev TCO API",
    func=get_maintenance_cost_func,
    args_schema=GetMaintenanceInput
)


# ---------- Depreciation ----------
class GetDepreciationInfoInput(BaseModel):
    vin: str
    zip: str
    from_zip: str
    ownership_years: int

def get_depreciation_info_func(vin, zip, from_zip, ownership_years):
    url = f"https://api.auto.dev/tco/{vin}"
    params = {"zip": zip, "fromZip": from_zip}
    headers = {
        "Authorization": f"Bearer {AUTO_DEV_API_KEY}",
        "Content-Type": "application/json"
    }
    resp = requests.get(url, params=params, headers=headers)
    data = resp.json()

    tco_data = data.get("tco", {})
    annual_dep = tco_data.get("depreciation")
    if annual_dep is None:
        return {"error": "Depreciation data not available."}

    depreciation_total = annual_dep * ownership_years
    return {
        "annual_depreciation": annual_dep,
        "total_depreciation": depreciation_total,
        "total_5yr_cost": tco_data.get("total", {}).get("tcoPrice")
    }

get_depreciation_info = StructuredTool.from_function(
    name="get_depreciation_info",
    description="Estimate annual and total depreciation using Auto.dev TCO API",
    func=get_depreciation_info_func,
    args_schema=GetDepreciationInfoInput
)

from typing import Dict, Any, List

CURRENT_YEAR = 2025

def enrich_listings_with_finance_and_tco(listings: List[Dict[str, Any]], 
                                         down_payment: float, 
                                         loan_term_months: int, 
                                         credit_score: int) -> List[Dict[str, Any]]:
    enriched_results = []
    for listing in listings:
        try:
            vin = listing["vin"]
            year = listing["year"]
            make = listing["make"]
            model = listing["model"]
            car_price = listing["price"]
            dealer_zip = listing["zip"]
            vehicle_age = CURRENT_YEAR - year if year else None
            vehicle_mileage = listing.get("vehicle_mileage") or 0

            # --- Financing ---
            finance_data = calculate_financing_func(
                vin=vin,
                car_price=car_price,
                down_payment=down_payment,
                loan_term_months=loan_term_months,
                year=year,
                make=make,
                model=model,
                zip=dealer_zip,
                credit_score=credit_score,
                vehicle_age=vehicle_age,
                vehicle_mileage=vehicle_mileage
            )

            # --- Maintenance / TCO ---
            tco_data = get_maintenance_cost_func(
                vin=vin,
                zip=dealer_zip,
                from_zip=dealer_zip  # assuming same as target location
            )

            depreciation_data = get_depreciation_info_func(
                vin=vin,
                zip=dealer_zip,
                from_zip=dealer_zip,
                ownership_years=5
            )

            enriched_results.append({
                **listing,
                "financing": finance_data,
                "maintenance_tco": tco_data,
                "depreciation": depreciation_data
            })

        except Exception as e:
            enriched_results.append({
                **listing,
                "error": str(e)
            })
    return enriched_results
