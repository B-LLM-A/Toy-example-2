import os
import requests
from typing import Any, Dict, List, Optional
from langchain.tools import tool
import logging

AUTO_DEV_API_KEY = os.getenv("AUTO_DEV_API_KEY")  # keep your API key in env var
LOGGER = logging.getLogger("AutoDev")
_MAX_LOG_BODY = 1500

def _truncate(text: Optional[str], limit: int = _MAX_LOG_BODY) -> str:
    if not text:
        return ""
    return text if len(text) <= limit else text[:limit] + f"... [truncated {len(text) - limit} chars]"

@tool("auto_dev_inventory", return_direct=False)
def auto_dev_inventory_tool(make: str = None, model: str = None, location: str = None, budget: int = None, zipcode: int = None):
    """
    Query Auto.dev Vehicle Listings API to find cars for sale based on user preferences.
    Args:
        make (str, optional): Car brand (e.g. "Toyota")
        model (str, optional): Car model (e.g. "Camry")
        location (str, optional): City, state, or zipcode to search near
        budget (int, optional): Maximum price in USD
    Returns:
        str: Summary of available listings (with dealer links).
    """
    url = "https://auto.dev/api/listings"
    headers = {"Authorization": f"Bearer {AUTO_DEV_API_KEY}"}
    params = {
        "make": make,
        "model": model,
        "location": location,
        "price_max": budget,
        "zip": zipcode,
        "limit": 5  # just get a few results
    }
    LOGGER.info(f"HTTP GET {url} header{headers} params={params}")

    try:
        resp = requests.get(url, headers=headers, params=params)
        # resp.raise_for_status()
        data = resp.json()
        LOGGER.info(data)

        if "listings" not in data or not data["listings"]:
            # return f"No listings found for {make} {model} in {location} under ${budget}"
            return data
        
        results = []
        for car in data["data"]:
            vehicle = car.get("vehicle", {})
            retail = car.get("retailListing", {})

            title = f"{vehicle.get('year', '')} {vehicle.get('make', '')} {vehicle.get('model', '')} {vehicle.get('trim', '')}".strip()
            price = retail.get("price", "N/A")
            dealer = retail.get("dealer", "Unknown dealer")
            city = retail.get("city", "")
            state = retail.get("state", "")
            link = retail.get("vdp", "")
            img = retail.get("primaryImage", "")

            line = f"- {title} | Price: ${price} | Dealer: {dealer} ({city}, {state})"
            if link:
                line += f" | [Details]({link})"
            if img:
                line += f" | Image: {img}"

            results.append(line)

        return "\n".join(results)

    except Exception as e:
        return f"Error calling Auto.dev API: {str(e)}"
        return "\n".join(results)

    except Exception as e:
        return f"Error calling Auto.dev API: {str(e)}"
