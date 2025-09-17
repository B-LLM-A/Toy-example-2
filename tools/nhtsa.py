"""
NHTSA SafetyRatings API tools

Implements lightweight tools for accessing the NHTSA Safety Ratings API:
https://www.nhtsa.gov/nhtsa-datasets-and-apis

Approach endpoints used:
- /SafetyRatings                         -> list model years
- /SafetyRatings/modelyear/{year}        -> list makes for year
- /SafetyRatings/modelyear/{year}/make/{make} -> list models for year/make
- /SafetyRatings/modelyear/{year}/make/{make}/model/{model} -> list variants with VehicleId
- /SafetyRatings/VehicleId/{id}          -> safety ratings for a vehicle id

Responses are normalized to JSON. Uses urllib (stdlib) and includes structured logging.
"""

from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urljoin, quote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json
import logging
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool


BASE = "https://api.nhtsa.gov/"
LOGGER = logging.getLogger("nhtsa")
_MAX_LOG_BODY = 1500


def _truncate(text: Optional[str], limit: int = _MAX_LOG_BODY) -> str:
    if not text:
        return ""
    return text if len(text) <= limit else text[:limit] + f"... [truncated {len(text) - limit} chars]"


def _get_json(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    params = params.copy() if params else {}
    # Ask the API for JSON.
    if "format" not in params:
        params["format"] = "json"
    query = f"?{urlencode(params)}" if params else ""
    url = urljoin(BASE, path.lstrip("/")) + query

    req = Request(url, headers={"Accept": "application/json"})
    LOGGER.info(f"HTTP GET {url} params={params}")
    try:
        with urlopen(req, timeout=20) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            raw = resp.read()
            text = raw.decode("utf-8", errors="replace")
            LOGGER.info(f"HTTP {status} {url} len={len(raw)} body={_truncate(text)}")
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
        return {"raw": text}


# ---------- Tools: list model years, makes, models, variants, and ratings ----------


class YearsInput(BaseModel):
    """No args; list available model years."""


def nhtsa_years() -> List[int]:
    LOGGER.info("nhtsa_years: start")
    try:
        data = _get_json("SafetyRatings")
        # The API typically returns Results: [{ModelYear: 2023}, ...]
        items = data.get("Results", []) if isinstance(data, dict) else []
        years = []
        for i in items:
            try:
                y = int(i.get("ModelYear"))
                years.append(y)
            except Exception:
                continue
        result = sorted(list(set(years)), reverse=True)
        LOGGER.info(f"nhtsa_years: {len(result)} years; sample={result[:5]}")
        return result
    except Exception:
        LOGGER.exception("nhtsa_years: failed")
        raise


class MakesInput(BaseModel):
    year: int = Field(..., description="Model year, e.g., 2019")


def nhtsa_makes(year: int) -> List[str]:
    LOGGER.info(f"nhtsa_makes: start year={year}")
    try:
        data = _get_json(f"SafetyRatings/modelyear/{year}")
        items = data.get("Results", []) if isinstance(data, dict) else []
        makes = [str(i.get("Make", "")).strip() for i in items]
        result = sorted(list(set([m for m in makes if m])))
        LOGGER.info(f"nhtsa_makes: {len(result)} makes; sample={result[:5]}")
        return result
    except Exception:
        LOGGER.exception("nhtsa_makes: failed")
        raise


class ModelsInput(BaseModel):
    year: int = Field(..., description="Model year")
    make: str = Field(..., description="Vehicle make")


def nhtsa_models(year: int, make: str) -> List[str]:
    LOGGER.info(f"nhtsa_models: start year={year} make={make}")
    try:
        data = _get_json(f"SafetyRatings/modelyear/{year}/make/{quote(make)}")
        items = data.get("Results", []) if isinstance(data, dict) else []
        models = [str(i.get("Model", "")).strip() for i in items]
        result = sorted(list(set([m for m in models if m])))
        LOGGER.info(f"nhtsa_models: {len(result)} models; sample={result[:5]}")
        return result
    except Exception:
        LOGGER.exception("nhtsa_models: failed")
        raise


class VariantsInput(BaseModel):
    year: int = Field(..., description="Model year")
    make: str = Field(..., description="Vehicle make")
    model: str = Field(..., description="Vehicle model")


def nhtsa_variants(year: int, make: str, model: str) -> List[Dict[str, Any]]:
    """Return vehicle variants with their VehicleId and description."""
    LOGGER.info(f"nhtsa_variants: start year={year} make={make} model={model}")
    try:
        data = _get_json(
            f"SafetyRatings/modelyear/{year}/make/{quote(make)}/model/{quote(model)}"
        )
        items = data.get("Results", []) if isinstance(data, dict) else []
        out: List[Dict[str, Any]] = []
        for i in items:
            try:
                vid = int(i.get("VehicleId"))
            except Exception:
                vid = None
            desc = str(i.get("VehicleDescription", "")).strip()
            if vid and desc:
                out.append({"id": vid, "text": desc})
        LOGGER.info(f"nhtsa_variants: {len(out)} variants; sample={[o['id'] for o in out[:5]]}")
        return out
    except Exception:
        LOGGER.exception("nhtsa_variants: failed")
        raise


class RatingsInput(BaseModel):
    vehicle_id: int = Field(..., description="NHTSA VehicleId")


def nhtsa_ratings(vehicle_id: int) -> Dict[str, Any]:
    LOGGER.info(f"nhtsa_ratings: start vehicle_id={vehicle_id}")
    try:
        data = _get_json(f"SafetyRatings/VehicleId/{int(vehicle_id)}")
        if isinstance(data, dict):
            LOGGER.info(f"nhtsa_ratings: keys={list(data.keys())[:10]}")
            return data
        LOGGER.info("nhtsa_ratings: non-dict response, wrapping")
        return {"data": data}
    except Exception:
        LOGGER.exception("nhtsa_ratings: failed")
        raise


# Export StructuredTools for NHTSA
NHTSA_TOOLS = [
    StructuredTool.from_function(
        name="nhtsa_years",
        description="List available model years from NHTSA SafetyRatings",
        func=nhtsa_years,
        args_schema=YearsInput,
    ),
    StructuredTool.from_function(
        name="nhtsa_makes",
        description="List vehicle makes for a given year from NHTSA",
        func=nhtsa_makes,
        args_schema=MakesInput,
    ),
    StructuredTool.from_function(
        name="nhtsa_models",
        description="List vehicle models for a given year and make from NHTSA",
        func=nhtsa_models,
        args_schema=ModelsInput,
    ),
    StructuredTool.from_function(
        name="nhtsa_variants",
        description="List vehicle variants (with VehicleId) for year/make/model from NHTSA",
        func=nhtsa_variants,
        args_schema=VariantsInput,
    ),
    StructuredTool.from_function(
        name="nhtsa_ratings",
        description="Get safety ratings for a variant by VehicleId from NHTSA",
        func=nhtsa_ratings,
        args_schema=RatingsInput,
    ),
]

