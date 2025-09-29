from langchain_core.tools import tool
from pydantic import BaseModel, Field
import math
import csv
import os
import requests

# -----------------------
# Input schema
# -----------------------
class DistanceCheckInput(BaseModel):
    user_city: str = Field(..., description="User's city name")
    user_state: str = Field(..., description="User's state name")
    dealer_city: str = Field(..., description="Dealer's city name")
    dealer_state: str = Field(..., description="Dealer's state name")
    threshold_miles: float = Field(..., description="Max allowed distance in miles")

# -----------------------
# Helpers
# -----------------------
def haversine(lat1, lon1, lat2, lon2):
    """Returns distance in miles between two lat/lon points."""
    R = 3959.87433  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def load_city_coords():
    """Load city/state → coordinates from uscities.csv"""
    coords_map = {}
    csv_path = "recommender/data/uscities.csv"
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            coords_map[(row["city"].strip().lower(), row["state_name"].strip().lower())] = (
                float(row["lat"]), float(row["lng"])
            )
    return coords_map

LOCAL_COORDS = load_city_coords()

def lookup_coords_local(city, state):
    """Check local dataset for coordinates."""
    return LOCAL_COORDS.get((city.strip().lower(), state.strip().lower()))

def lookup_coords_api(city, state):
    """Fallback to Nominatim OpenStreetMap API."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "city": city,
        "state": state,
        "country": "USA",
        "format": "json",
        "limit": 1
    }
    try:
        resp = requests.get(url, params=params, headers={"User-Agent": "dealer-eval-agent"})
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"[DEBUG] Geocoding API error for ({city}, {state}): {e}")
    return None

def get_coordinates(city, state):
    """Get coordinates from local data or API fallback."""
    # coords = lookup_coords_local(city, state)
    # if coords:
    #     return coords
    # print(f"[DEBUG] No local match for: ({city}, {state}) — querying API...")
    return lookup_coords_api(city, state)

# -----------------------
# LangChain tool
# -----------------------
@tool(args_schema=DistanceCheckInput)
def distance_check(user_city, user_state, dealer_city, dealer_state, threshold_miles):
    """
    Check if dealer is within a threshold distance (miles) from user.
    Uses local dataset first, then falls back to Nominatim API.
    """
    print(f"[DEBUG] distance_check called:\n"
          f"  User -> City: '{user_city}', State: '{user_state}'\n"
          f"  Dealer -> City: '{dealer_city}', State: '{dealer_state}'\n"
          f"  Threshold: {threshold_miles} miles")

    user_coords = get_coordinates(user_city, user_state)
    dealer_coords = get_coordinates(dealer_city, dealer_state)

    if not user_coords:
        print(f"[DEBUG] Coordinates not found for: ({user_city}, {user_state})")
    if not dealer_coords:
        print(f"[DEBUG] Coordinates not found for: ({dealer_city}, {dealer_state})")

    if not user_coords or not dealer_coords:
        return False

    distance = haversine(user_coords[0], user_coords[1], dealer_coords[0], dealer_coords[1])
    nearby = distance <= threshold_miles

    print(f"[DEBUG] Computed distance: {distance:.2f} miles -> Nearby? {nearby}")
    return nearby
