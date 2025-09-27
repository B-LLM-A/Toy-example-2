from langchain_core.tools import tool
from pydantic import BaseModel, Field
import csv
import math
import os

# ===== LOAD DATASET =====
CITY_STATE_COORDS = {}

def load_city_state_coords(csv_path="recommender/data/uscities.csv"):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at {csv_path}")
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["city"].strip().title(), row["state_id"].strip().upper())
            CITY_STATE_COORDS[key] = (float(row["lat"]), float(row["lng"]))

# Call this on module import
load_city_state_coords()

# ===== HELPER FUNCTIONS =====
def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8  # Earth radius in miles
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def get_lat_lon_for_user(city, state, zip_code=None, zip_coords=None):
    # Optional: zip_coords dict if you add ZIP lookup from another dataset
    if zip_code and zip_coords and zip_code in zip_coords:
        return zip_coords[zip_code]
    return CITY_STATE_COORDS.get((city.strip().title(), state.strip().upper()))

def get_lat_lon_for_dealer(city, state):
    return CITY_STATE_COORDS.get((city.strip().title(), state.strip().upper()))

# ===== TOOL SCHEMA =====
class DistanceCheckInput(BaseModel):
    user_city: str = Field(..., description="City where the user is located")
    user_state: str = Field(..., description="State where the user is located")
    user_zip: str = Field(None, description="Optional ZIP code for the user")
    dealer_city: str = Field(..., description="City where the dealer is located")
    dealer_state: str = Field(..., description="State where the dealer is located")
    threshold_miles: float = Field(50, description="Max distance in miles to consider 'nearby'")

@tool("distance_check", args_schema=DistanceCheckInput)
def distance_check(user_city, user_state, user_zip, dealer_city, dealer_state, threshold_miles):
    """Check if a dealer is within the given distance threshold from the user using city/state mapping."""
    user_coords = get_lat_lon_for_user(user_city, user_state)
    dealer_coords = get_lat_lon_for_dealer(dealer_city, dealer_state)

    if not user_coords or not dealer_coords:
        return {"error": "Coordinates not found for one or both locations."}

    dist = haversine(*user_coords, *dealer_coords)
    return {
        "distance_miles": round(dist, 2),
        "nearby": dist <= threshold_miles
    }
