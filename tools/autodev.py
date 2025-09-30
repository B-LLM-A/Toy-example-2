import os
import requests
import logging
from typing import Dict
from langchain.tools import tool
from dotenv import load_dotenv

# --- Load environment ---
load_dotenv()  # ensures .env values are loaded before we run anything

LOGGER = logging.getLogger("AutoDev")

@tool("auto_dev_inventory", return_direct=False)
def auto_dev_inventory_tool(make: str = None, model: str = None, location: str = None,
                            budget: int = None, zipcode: int = None) -> Dict:
    """LangChain tool-compatible version — returns listings + summary."""
    return _auto_dev_inventory_raw(make, model, location, budget, zipcode)


def _auto_dev_inventory_raw(make: str = None, model: str = None, location: str = None,
                            budget: int = None, zipcode: int = None) -> Dict:
    """Plain Python callable — fetches inventory from Auto.dev, fallback to offline demo if no API key."""

    # Re-fetch API key at call time
    api_key = os.getenv("AUTO_DEV_API_KEY")

    if not api_key:
        LOGGER.warning("AUTO_DEV_API_KEY missing — using offline demo data.")
        demo_listings = [{
            "year": 2022,
            "make": make or "Toyota",
            "model": model or "Tacoma",
            "trim": "SR",
            "price": 32000,
            "dealer": "Demo Dealer",
            "city": location or "Orlando",
            "state": "FL",
            "vehicle_age": 3,
        }]
        return {
            "listings": demo_listings,
            "summary": "Offline mode demo listing — no live API call.",
            "raw_api": {}
        }

    url = "https://auto.dev/api/listings"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "make": make, "model": model, "location": location,
        "price_max": budget, "zip": zipcode, "limit": 5
    }
    LOGGER.info(f"HTTP GET {url} headers={headers} params={params}")

    try:
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()
        LOGGER.info(data)

        listings = data.get("listings") or data.get("data", [])
        if not listings:
            return {
                "listings": [],
                "summary": f"No listings found for {make} {model} in {location} under ${budget}",
                "raw_api": data
            }

        results = []
        for car in listings:
            vehicle = car.get("vehicle", {})
            retail = car.get("retailListing", {})

            title = f"{vehicle.get('year', '')} {vehicle.get('make', '')} " \
                    f"{vehicle.get('model', '')} {vehicle.get('trim', '')}".strip()
            price = retail.get("price", "N/A")
            dealer = retail.get("dealer", "Unknown dealer")
            city = retail.get("city", "")
            state = retail.get("state", "")
            link = retail.get("vdp", "")
            img = retail.get("primaryImage", "")

            line = f"- {title} | Price: ${price} | Dealer: {dealer} ({city}, {state})"
            if link: line += f" | [Details]({link})"
            if img: line += f" | Image: {img}"
            results.append(line)

        return {
            "listings": listings,
            "summary": "\n".join(results),
            "raw_api": data
        }

    except Exception as e:
        return {
            "listings": [],
            "summary": f"Error calling Auto.dev API: {str(e)}",
            "raw_api": {}
        }

# Raw function for internal direct calls
auto_dev_inventory_tool_raw = _auto_dev_inventory_raw
