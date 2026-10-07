import numpy as np

from scipy.ndimage import (
    label,
    find_objects
)

from math import (
    radians,
    asin,
    sin,
    cos,
    sqrt,
    atan2,
    degrees
)

EARTH_R = 6371.0


def polar_to_xyz(scan):

    elevation = np.deg2rad(
        scan["elangle_deg"]
    )

    azimuth = np.deg2rad(
        np.arange(
            scan["nrays"]
        )
        * 360.0
        / scan["nrays"]
    )

    ranges = (
        scan["rstart_m"]
        + np.arange(
            scan["nbins"]
        )
        * scan["rscale_m"]
    ) / 1000.0

    rr, aa = np.meshgrid(
        ranges,
        azimuth
    )

    effective_radius = (
        4.0 / 3.0
    ) * EARTH_R

    z = (
        np.sqrt(
            rr**2
            + effective_radius**2
            + 2
            * rr
            * effective_radius
            * np.sin(elevation)
        )
        - effective_radius
    )

    ground = (
        effective_radius
        * np.arcsin(
            (
                rr
                * np.cos(elevation)
            )
            /
            (
                effective_radius
                + z
            )
        )
    )

    x = (
        ground
        * np.sin(aa)
    )

    y = (
        ground
        * np.cos(aa)
    )

    return (
        x,
        y,
        z,
        scan["dbzh"]
    )


def build_volume(
    scans,
    dbz_min=32,
    xy_km=1,
    z_km=1,
    max_km=220
):

    points = []
    site = None

    for scan in scans:

        if site is None:

            site = {
                "lat":
                    scan["lat"],

                "lon":
                    scan["lon"],

                "height_m":
                    scan["height_m"]
            }

        x, y, z, values = (
            polar_to_xyz(scan)
        )

        valid = (
            np.isfinite(values)
            & (values >= dbz_min)
            & (np.abs(x) <= max_km)
            & (np.abs(y) <= max_km)
            & (z >= 0)
            & (z <= 20)
        )

        if np.any(valid):

            points.append(
                (
                    x[valid],
                    y[valid],
                    z[valid],
                    values[valid]
                )
            )

    if not points:
        return None

    x = np.concatenate(
        [p[0] for p in points]
    )

    y = np.concatenate(
        [p[1] for p in points]
    )

    z = np.concatenate(
        [p[2] for p in points]
    )

    values = np.concatenate(
        [p[3] for p in points]
    )

    origin_x = float(
        np.floor(
            x.min() / xy_km
        )
        * xy_km
    )

    origin_y = float(
        np.floor(
            y.min() / xy_km
        )
        * xy_km
    )

    nx = int(
        np.ceil(
            (x.max() - origin_x)
            / xy_km
        )
    ) + 1

    ny = int(
        np.ceil(
            (y.max() - origin_y)
            / xy_km
        )
    ) + 1

    nz = int(
        np.ceil(
            z.max() / z_km
        )
    ) + 1

    volume = np.full(
        (
            nz,
            ny,
            nx
        ),
        np.nan,
        dtype=np.float32
    )

    ix = np.clip(
        np.rint(
            (x - origin_x)
            / xy_km
        ).astype(int),
        0,
        nx - 1
    )

    iy = np.clip(
        np.rint(
            (y - origin_y)
            / xy_km
        ).astype(int),
        0,
        ny - 1
    )

    iz = np.clip(
        np.rint(
            z / z_km
        ).astype(int),
        0,
        nz - 1
    )

    for a, b, c, d in zip(
        ix,
        iy,
        iz,
        values
    ):

        if (
            not np.isfinite(
                volume[c, b, a]
            )
            or d > volume[c, b, a]
        ):

            volume[
                c, b, a
            ] = d

    return {

        "volume":
            volume,

        "origin_xy":
            [origin_x, origin_y],

        "xy_km":
            xy_km,

        "z_km":
            z_km,

        "site":
            site
    }


def extract_cells(
    volume,
    min_voxels=8
):

    array = np.nan_to_num(
        volume["volume"],
        nan=-999
    )

    labels, count = label(
        array >= 32,
        structure=np.ones(
            (3, 3, 3),
            dtype=np.uint8
        )
    )

    cells = []

    for index, sl in enumerate(
        find_objects(labels),
        1
    ):

        if sl is None:
            continue

        positions = np.argwhere(
            labels[sl] == index
        )

        if len(positions) < min_voxels:
            continue

        z0 = sl[0].start
        y0 = sl[1].start
        x0 = sl[2].start

        iz = (
            positions[:, 0]
            + z0
        )

        iy = (
            positions[:, 1]
            + y0
        )

        ix = (
            positions[:, 2]
            + x0
        )

        values = array[
            iz,
            iy,
            ix
        ]

        voxels = []

        for j in range(
            len(values)
        ):

            voxels.append(
                (
                    int(ix[j]),
                    int(iy[j]),
                    int(iz[j]),
                    round(
                        float(values[j]),
                        1
                    )
                )
            )

        cells.append({

            "voxel_count":
                int(len(values)),

            "dbz_max":
                float(
                    values.max()
                ),

            "dbz_mean":
                float(
                    values.mean()
                ),

            "centroid_local_km": [

                float(
                    volume[
                        "origin_xy"
                    ][0]
                    + ix.mean()
                    * volume["xy_km"]
                ),

                float(
                    volume[
                        "origin_xy"
                    ][1]
                    + iy.mean()
                    * volume["xy_km"]
                ),

                float(
                    iz.mean()
                    * volume["z_km"]
                )
            ],

            "echo_top_km":
                float(
                    iz.max()
                    * volume["z_km"]
                ),

            "voxels":
                voxels
        })

    return sorted(
        cells,
        key=lambda c:
            c["dbz_max"],
        reverse=True
    )


def local_to_latlon(
    x,
    y,
    site
):

    lat0 = radians(
        site["lat"]
    )

    lon0 = radians(
        site["lon"]
    )

    distance = (
        sqrt(x*x + y*y)
        / EARTH_R
    )

    bearing = atan2(
        x,
        y
    )

    lat = asin(
        sin(lat0)
        * cos(distance)
        +
        cos(lat0)
        * sin(distance)
        * cos(bearing)
    )

    lon = (
        lon0
        +
        atan2(
            sin(bearing)
            * sin(distance)
            * cos(lat0),

            cos(distance)
            -
            sin(lat0)
            * sin(lat)
        )
    )

    return (
        degrees(lat),
        (
            degrees(lon)
            + 540
        ) % 360 - 180
  )
