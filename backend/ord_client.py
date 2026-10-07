import os
import requests
from datetime import datetime, timedelta, timezone

BASE = os.getenv(
    "ORD_BASE_URL",
    "https://api.meteogate.eu/eu-eumetnet-weather-radar"
)

def _headers():
    headers = {
        "Accept": "application/json, application/octet-stream"
    }

    key = os.getenv("ORD_API_KEY")

    if key:
        headers["Authorization"] = f"Bearer {key}"

    return headers


def _iso(dt):
    return (
        dt.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _get(url, params=None, timeout=90):
    r = requests.get(
        url,
        params=params,
        headers=_headers(),
        timeout=timeout
    )

    r.raise_for_status()
    return r


def _extract_download_url(obj):

    if isinstance(obj, dict):

        for key in (
            "href",
            "data",
            "url",
            "download_url"
        ):

            value = obj.get(key)

            if (
                isinstance(value, str)
                and value.startswith("http")
            ):
                return value

        for value in obj.values():

            result = _extract_download_url(value)

            if result:
                return result

    if isinstance(obj, list):

        for value in obj:

            result = _extract_download_url(value)

            if result:
                return result

    return None


def fetch_product(
    standard_name="DBZH",
    minutes=20
):

    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=minutes)

    url = (
        f"{BASE}/collections/observations/"
        f"locations/0-20010-0-OPERA"
    )

    params = {
        "datetime":
            f"{_iso(start)}/{_iso(end)}",

        "standard_name":
            standard_name,

        "format":
            "ODIM",

        "method":
            "comp"
    }

    response = _get(url, params)

    # HDF5 direttamente
    if response.content[:4] == b"\x89HDF":
        return response.content

    try:
        obj = response.json()

    except Exception:

        raise RuntimeError(
            "ORD did not return HDF5 or JSON"
        )

    href = _extract_download_url(obj)

    if not href:

        raise RuntimeError(
            "ORD response contained no downloadable ODIM URL"
        )

    return _get(
        href,
        timeout=120
    ).content


def discover_radars(
    minutes=20,
    bbox="-30,30,50,72",
    limit=250
):

    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=minutes)

    url = (
        f"{BASE}/collections/"
        f"observations/items"
    )

    params = {
        "bbox": bbox,
        "datetime":
            f"{_iso(start)}/{_iso(end)}",

        "standard_name": "DBZH",
        "format": "ODIM",
        "method": "scan",
        "limit": limit
    }

    response = _get(
        url,
        params,
        timeout=120
    )

    data = response.json()

    result = []
    seen = set()

    for feature in data.get(
        "features",
        []
    ):

        properties = feature.get(
            "properties",
            {}
        )

        geometry = feature.get(
            "geometry",
            {}
        )

        coordinates = geometry.get(
            "coordinates",
            [None, None]
        )

        platform = (
            properties.get("platform")
            or properties.get("platform_name")
        )

        if not platform:
            continue

        if platform in seen:
            continue

        if len(coordinates) < 2:
            continue

        seen.add(platform)

        result.append({
            "platform": platform,
            "lon": float(coordinates[0]),
            "lat": float(coordinates[1]),
            "data": properties.get("data"),
            "parameter_name":
                properties.get(
                    "parameter_name"
                ),
            "level":
                properties.get("level"),

            "license":
                properties.get("license")
        })

    return result


def fetch_volume(
    platform,
    minutes=20,
    max_elevation=6.5
):

    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=minutes)

    url = (
        f"{BASE}/collections/"
        f"observations/locations/"
        f"{platform}"
    )

    params = {
        "datetime":
            f"{_iso(start)}/{_iso(end)}",

        "standard_name":
            "DBZH",

        "level":
            f"../{max_elevation}",

        "format":
            "ODIM",

        "method":
            "scan"
    }

    response = _get(
        url,
        params,
        timeout=120
    )

    if response.content[:4] == b"\x89HDF":
        return response.content

    try:
        obj = response.json()

    except Exception:

        raise RuntimeError(
            f"Volume response for {platform} "
            "was not HDF5/JSON"
        )

    href = _extract_download_url(obj)

    if not href:

        raise RuntimeError(
            f"No volume URL for {platform}"
        )

    return _get(
        href,
        timeout=120
    ).content
