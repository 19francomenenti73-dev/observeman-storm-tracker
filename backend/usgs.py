import requests

from datetime import (
    datetime,
    timezone
)


URL = (
    "https://earthquake.usgs.gov/"
    "earthquakes/feed/v1.0/"
    "summary/4.5_day.geojson"
)


def fetch(
    min_magnitude=4.5,
    hours=24
):

    response = requests.get(
        URL,
        timeout=30
    )

    response.raise_for_status()

    feed = response.json()

    now = datetime.now(
        timezone.utc
    )

    features = []

    for feature in feed.get(
        "features",
        []
    ):

        properties = feature.get(
            "properties",
            {}
        )

        geometry = (
            feature.get(
                "geometry"
            )
            or {}
        )

        coordinates = (
            geometry.get(
                "coordinates"
            )
            or []
        )

        timestamp = properties.get(
            "time"
        )

        magnitude = properties.get(
            "mag"
        )

        if (
            timestamp is None
            or magnitude is None
            or len(coordinates) < 3
        ):
            continue

        if magnitude < min_magnitude:
            continue

        age = (
            now
            -
            datetime.fromtimestamp(
                timestamp / 1000,
                tz=timezone.utc
            )
        ).total_seconds() / 3600

        if age > hours:
            continue

        features.append({

            "type":
                "Feature",

            "geometry": {

                "type":
                    "Point",

                "coordinates":
                    coordinates
            },

            "properties": {

                "id":
                    feature.get("id"),

                "magnitude":
                    magnitude,

                "place":
                    properties.get(
                        "place"
                    ),

                "time":
                    datetime.fromtimestamp(
                        timestamp / 1000,
                        tz=timezone.utc
                    ).isoformat(),

                "url":
                    properties.get(
                        "url"
                    ),

                "age_hours":
                    round(
                        age,
                        1
                    )
            }
        })

    return {

        "type":
            "FeatureCollection",

        "features":
            features,

        "metadata": {

            "source":
                "USGS",

            "filter":
                f"M>={min_magnitude}",

            "window_hours":
                hours
        }
  }
