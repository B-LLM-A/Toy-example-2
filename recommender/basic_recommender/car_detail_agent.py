from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Dict, Any
import datetime
from tools.autodev import auto_dev_inventory_tool_raw
from tools.finance_tools import enrich_listings_with_finance_and_tco


class CarDetailAgentInput(BaseModel):
    make: str = Field(..., description="Car make to search inventory for")
    model: str = Field(..., description="Car model to search inventory for")
    location: str = Field(..., description="City or state to search inventory for")
    zipcode: int = Field(..., description="ZIP code to narrow dealer results")
    budget: int = Field(..., description="Maximum price in USD")
    down_payment: float = Field(..., description="Down payment in USD")
    loan_term_months: int = Field(..., description="Loan term in months")
    credit_score: int = Field(..., description="Credit score for financing calculations")
    desired_year: int = Field(None, description="Preferred production year (e.g., 2025)")


def car_detail_agent_func(
    make: str,
    model: str,
    location: str,
    zipcode: int,
    budget: int,
    down_payment: float,
    loan_term_months: int,
    credit_score: int,
    desired_year: int = None
) -> Dict[str, Any]:
    inventory_result = auto_dev_inventory_tool_raw(
        make=make,
        model=model,
        location=location,
        budget=budget,
        zipcode=zipcode
    )

    listings = inventory_result.get("listings")

    # --- Fallback: extract from raw_api.records ---
    if (not listings) and "raw_api" in inventory_result:
        raw_records = inventory_result["raw_api"].get("records", [])
        listings = []
        for rec in raw_records:
            listings.append({
                "year": rec.get("year"),
                "make": rec.get("make"),
                "model": rec.get("model"),
                "price": rec.get("priceUnformatted") or rec.get("price_unformatted"),
                "mileage": rec.get("mileageUnformatted"),
                "dealer": rec.get("dealerName"),
                "city": rec.get("city"),
                "state": rec.get("state"),
                "photo": rec.get("primaryPhotoUrl"),
                "lat": rec.get("lat"),
                "lon": rec.get("lon"),
                "url": rec.get("vdpUrl"),
                # keep any extra fields you need for enrichment downstream…
            })

    if not listings:
        print("OH NO!!!!!")
        return {
            "listings": [],
            "note": inventory_result.get("summary", "No listings found matching criteria."),
            "raw_api": inventory_result.get("raw_api", {})
        }

    # --- Desired year filtering ---
    matching_listings = listings
    note = ""
    if desired_year:
        matching_listings = [car for car in listings if str(car.get("year")) == str(desired_year)]
        if not matching_listings:
            note = f"No {desired_year} {make} {model} found in {location} within budget."
            alt_years = sorted({car.get("year") for car in listings if car.get("year")})
            note += f" Closest available years: {', '.join(map(str, alt_years))}."
            matching_listings = listings

    # --- Vehicle age calculation ---
    current_year = datetime.datetime.now().year
    for car in matching_listings:
        if car.get("year"):
            car["vehicle_age"] = current_year - int(car["year"])
        else:
            car["vehicle_age"] = None

    # --- Finance/TCO enrichment ---
    # print("Reached Here!!!!!")
    enriched_listings = enrich_listings_with_finance_and_tco(
        listings=matching_listings,
        down_payment=down_payment,
        loan_term_months=loan_term_months,
        credit_score=credit_score
    )

    return {
        "zipcode": zipcode,
        "listings": enriched_listings,
        "summary": inventory_result.get("summary", ""),
        "note": note or inventory_result.get("note", ""),
        # raw_api omitted if you want to avoid large dumps to user
    }



CAR_DETAIL_AGENT_TOOL = StructuredTool.from_function(
    func=car_detail_agent_func,
    name="car_detail_agent",
    description=(
        "Fetch inventory for a car by make/model/location/ZIP, "
        "optionally filter by desired production year, "
        "then enrich each result with financing terms, "
        "maintenance costs, and depreciation estimates."
    ),
    args_schema=CarDetailAgentInput,
    return_direct=False
)

