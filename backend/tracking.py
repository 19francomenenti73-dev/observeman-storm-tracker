from math import (
    radians,
    sin,
    cos,
    asin,
    sqrt,
    atan2,
    degrees
)

R = 6371.0


def dist(a, b):

    p1 = radians(a[0])
    p2 = radians(b[0])

    dp = radians(
        b[0] - a[0]
    )

    dl = radians(
        b[1] - a[1]
    )

    h = (
        sin(dp / 2) ** 2
        +
        cos(p1)
        * cos(p2)
        * sin(dl / 2) ** 2
    )

    return (
        2
        * R
        * asin(sqrt(h))
    )


def bearing(a, b):

    p1 = radians(a[0])
    p2 = radians(b[0])

    dl = radians(
        b[1] - a[1]
    )

    value = atan2(
        sin(dl) * cos(p2),

        cos(p1) * sin(p2)
        -
        sin(p1)
        * cos(p2)
        * cos(dl)
    )

    return (
        degrees(value)
        + 360
    ) % 360


def project(
    lat,
    lon,
    br,
    km
):

    p = radians(lat)
    l = radians(lon)
    b = radians(br)

    d = km / R

    p2 = asin(
        sin(p)
        * cos(d)
        +
        cos(p)
        * sin(d)
        * cos(b)
    )

    l2 = (
        l
        +
        atan2(
            sin(b)
            * sin(d)
            * cos(p),

            cos(d)
            -
            sin(p)
            * sin(p2)
        )
    )

    return [
        degrees(p2),

        (
            degrees(l2)
            + 540
        ) % 360 - 180
    ]


def update_tracks(
    previous,
    current,
    dt_minutes,
    max_speed,
    prediction_hours,
    match_radius
):

    previous = previous or []

    used = set()

    result = []

    for cell in current:

        best = None

        for index, old in enumerate(
            previous
        ):

            if index in used:
                continue

            distance = dist(
                old["centroid"],
                cell["centroid"]
            )

            speed = (
                distance
                /
                (dt_minutes / 60)
            )

            if (
                distance <= match_radius
                and
                speed <= max_speed
            ):

                if (
                    best is None
                    or
                    distance
                    < best[0]
                ):

                    best = (
                        distance,
                        speed,
                        index,
                        old
                    )

        if best:

            distance, speed, index, old = best

            used.add(index)

            direction = bearing(
                old["centroid"],
                cell["centroid"]
            )

            prediction = []

            for hour in range(
                1,
                prediction_hours + 1
            ):

                prediction.append(
                    project(
                        cell["centroid"][0],
                        cell["centroid"][1],
                        direction,
                        speed * hour
                    )
                )

            previous_dbz = old.get(
                "dbz_max",
                cell["dbz_max"]
            )

            if (
                cell["dbz_max"]
                > previous_dbz + 2
            ):

                trend = "intensifying"

            elif (
                cell["dbz_max"]
                < previous_dbz - 2
            ):

                trend = "weakening"

            else:

                trend = "steady"

            cell["motion"] = {

                "speed_kmh":
                    round(speed, 1),

                "bearing_deg":
                    round(direction, 1),

                "observed_from":
                    old["centroid"],

                "prediction_4h":
                    prediction,

                "trend":
                    trend
            }

        else:

            cell["motion"] = None

        result.append(cell)

    return result
