# tools/nhtsa.py
import requests
from langchain.agents import tool

NHTSA_BASE_URL = "https://api.nhtsa.gov/SafetyRatings"


@tool("get_car_safety_details", return_direct=False)
def get_car_safety_details(year: str, make: str, model: str) -> str:
    """
    Retrieve NHTSA safety ratings for a given car make, model, and year.
    Args:
        year: e.g., "2020"
        make: e.g., "Toyota"
        model: e.g., "Corolla"
    Returns:
        A textual summary of safety ratings.
    """
    # Step 1: Search for the vehicle
    search_url = f"{NHTSA_BASE_URL}/modelyear/{year}/make/{make}/model/{model}?format=json"
    try:
        resp = requests.get(search_url, timeout=10)
        resp.raise_for_status()
        search_data = resp.json()
    except Exception as e:
        return f"Error fetching vehicle data: {e}"

    if not search_data.get("Results"):
        return f"No safety data for {year} {make} {model}."

    # Use first result
    vehicle_id = search_data["Results"][0].get("VehicleId")
    if not vehicle_id:
        return "Vehicle ID not found."

    # Step 2: Get the ratings
    ratings_url = f"{NHTSA_BASE_URL}/VehicleId/{vehicle_id}?format=json"
    try:
        resp = requests.get(ratings_url, timeout=10)
        resp.raise_for_status()
        ratings_data = resp.json()
    except Exception as e:
        return f"Error fetching ratings: {e}"

    if not ratings_data.get("Results"):
        return "Ratings unavailable."

    r = ratings_data["Results"][0]
    return (
        f"Safety ratings for {year} {make} {model}:\n"
        f"Overall: {r.get('OverallRating', 'N/A')}\n"
        f"Frontal Crash: {r.get('FrontalCrashRating', 'N/A')}\n"
        f"Side Crash: {r.get('SideCrashRating', 'N/A')}\n"
        f"Rollover: {r.get('RolloverRating', 'N/A')}"
    )
