"""
FuelEconomy.gov API tools

Lightweight tools for accessing the FuelEconomy.gov Web Services:
https://www.fueleconomy.gov/feg/ws/index.shtml

These tools expose the common "menu" navigation to find a vehicle by
year → make → model → options, as well as endpoints to retrieve vehicle
details. Responses are normalized to JSON using the API's `format=json`
parameter where supported to avoid XML parsing and additional deps.

No external HTTP libraries are required; uses urllib from the stdlib.
"""

from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import logging
import json
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool


BASE = "https://www.fueleconomy.gov/ws/rest/"
LOGGER = logging.getLogger("fueleconomy")
_MAX_LOG_BODY = 1500

LOGGER.info("STARTING")


def _truncate(text: str, limit: int = _MAX_LOG_BODY) -> str:
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [truncated {len(text) - limit} chars]"


def _get_json(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    params = params.copy() if params else {}
    # Ask the API for JSON instead of XML
    if "format" not in params:
        params["format"] = "json"
    query = f"?{urlencode(params)}" if params else ""
    url = urljoin(BASE, path) + query
    req = Request(url, headers={"Accept": "application/json"})

    LOGGER.info(f"HTTP GET {url} params={params}")
    try:
        with urlopen(req, timeout=20) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            raw = resp.read()
            text = raw.decode("utf-8", errors="replace")
            LOGGER.info(
                f"HTTP {status} {url} len={len(raw)} body={_truncate(text)}"
            )
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        LOGGER.error(
            f"HTTPError during GET {url}: code={getattr(e, 'code', None)} reason={getattr(e, 'reason', None)} body={_truncate(body)}"
        )
        raise
    except URLError as e:
        LOGGER.error(f"URLError during GET {url}: reason={getattr(e, 'reason', e)}")
        raise
    except Exception:
        LOGGER.exception(f"Unexpected error during GET {url}")
        raise

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        LOGGER.warning("JSON decoding failed; returning raw text payload")
        # Fallback to raw text if API didn't return JSON as expected
        return {"raw": text}


# ---------- Menu Tools ----------


class YearMenuInput(BaseModel):
    """No fields required; returns available model years."""


def fe_menu_years() -> List[int]:
    """Return a list of available model years (descending)."""
    LOGGER.info("fe_menu_years: start")
    try:
        data = _get_json("vehicle/menu/year")
        # Normalized response: list of {text: "2024", value: "2024"}
        items = data.get("menuItem", []) if isinstance(data, dict) else []
        if isinstance(items, dict):
            items = [items]
        years: List[int] = []
        for item in items:
            try:
                years.append(int(item.get("value") or item.get("text")))
            except Exception:
                continue
        result = sorted(list(set(years)), reverse=True)
        LOGGER.info(f"fe_menu_years: {len(result)} years; sample={result[:5]}")
        return result
    except Exception:
        LOGGER.exception("fe_menu_years: failed")
        raise


class MakeMenuInput(BaseModel):
    year: int = Field(..., description="Model year, e.g., 2022")


def fe_menu_makes(year: int) -> List[str]:
    """Return makes for a given model year."""
    LOGGER.info(f"fe_menu_makes: start year={year}")
    try:
        data = _get_json("vehicle/menu/make", {"year": year})
        items = data.get("menuItem", []) if isinstance(data, dict) else []
        if isinstance(items, dict):
            items = [items]
        makes = [str(i.get("text") or i.get("value") or "").strip() for i in items]
        result = [m for m in makes if m]
        LOGGER.info(f"fe_menu_makes: {len(result)} makes; sample={result[:5]}")
        return result
    except Exception:
        LOGGER.exception("fe_menu_makes: failed")
        raise


class ModelMenuInput(BaseModel):
    year: int = Field(..., description="Model year, e.g., 2022")
    make: str = Field(..., description="Vehicle make, e.g., Toyota")


def fe_menu_models(year: int, make: str) -> List[str]:
    """Return models for a given year and make."""
    LOGGER.info(f"fe_menu_models: start year={year} make={make}")
    try:
        data = _get_json("vehicle/menu/model", {"year": year, "make": make})
        items = data.get("menuItem", []) if isinstance(data, dict) else []
        if isinstance(items, dict):
            items = [items]
        models = [str(i.get("text") or i.get("value") or "").strip() for i in items]
        result = [m for m in models if m]
        LOGGER.info(f"fe_menu_models: {len(result)} models; sample={result[:5]}")
        return result
    except Exception:
        LOGGER.exception("fe_menu_models: failed")
        raise


class OptionsMenuInput(BaseModel):
    year: int = Field(..., description="Model year, e.g., 2022")
    make: str = Field(..., description="Vehicle make, e.g., Toyota")
    model: str = Field(..., description="Vehicle model, e.g., Camry")


def fe_menu_options(year: int, make: str, model: str) -> List[Dict[str, Any]]:
    """Return available options (trims) for a year/make/model with ids.

    Each item contains at least: {id: int, text: str}
    """
    LOGGER.info(f"fe_menu_options: start year={year} make={make} model={model}")
    try:
        data = _get_json("vehicle/menu/options", {"year": year, "make": make, "model": model})
        items = data.get("menuItem", []) if isinstance(data, dict) else []
        if isinstance(items, dict):
            items = [items]
        out: List[Dict[str, Any]] = []
        for i in items:
            text = str(i.get("text") or "").strip()
            try:
                vid = int(i.get("value"))
            except Exception:
                vid = None
            if text and vid:
                out.append({"id": vid, "text": text})
        LOGGER.info(
            f"fe_menu_options: {len(out)} options; sample={[o['id'] for o in out[:5]]}"
        )
        return out
    except Exception:
        LOGGER.exception("fe_menu_options: failed")
        raise


# ---------- Data Endpoints ----------


class VehicleInput(BaseModel):
    vehicle_id: int = Field(..., description="FuelEconomy.gov vehicle id (from options)")


def fe_vehicle_details(vehicle_id: int) -> Dict[str, Any]:
    """Return detailed vehicle data for a given vehicle id."""
    LOGGER.info(f"fe_vehicle_details: start vehicle_id={vehicle_id}")
    try:
        data = _get_json(f"vehicle/{vehicle_id}")
        if isinstance(data, dict):
            LOGGER.info(
                f"fe_vehicle_details: keys={list(data.keys())[:10]}"
            )
            return data
        LOGGER.info("fe_vehicle_details: non-dict response, wrapping in {data}")
        return {"data": data}
    except Exception:
        LOGGER.exception("fe_vehicle_details: failed")
        raise


# Optional helper: search and return options in one call
class SearchOptionsInput(BaseModel):
    year: int = Field(..., description="Model year")
    make: str = Field(..., description="Make")
    model: str = Field(..., description="Model")


# Export as LangChain StructuredTools
FE_TOOLS = [
    StructuredTool.from_function(
        name="fe_menu_years",
        description="List available model years from FuelEconomy.gov",
        func=fe_menu_years,
        args_schema=YearMenuInput,
    ),
    StructuredTool.from_function(
        name="fe_menu_makes",
        description="List makes for a given year from FuelEconomy.gov",
        func=fe_menu_makes,
        args_schema=MakeMenuInput,
    ),
    StructuredTool.from_function(
        name="fe_menu_models",
        description="List models for a given year and make from FuelEconomy.gov",
        func=fe_menu_models,
        args_schema=ModelMenuInput,
    ),
    StructuredTool.from_function(
        name="fe_menu_options",
        description="List trims/options with ids for a year/make/model from FuelEconomy.gov",
        func=fe_menu_options,
        args_schema=OptionsMenuInput,
    ),
    StructuredTool.from_function(
        name="fe_vehicle_details",
        description="Get detailed vehicle information by FuelEconomy.gov vehicle id",
        func=fe_vehicle_details,
        args_schema=VehicleInput,
    )
]
