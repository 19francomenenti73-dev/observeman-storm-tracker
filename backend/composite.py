import numpy as np

from scipy.ndimage import label
from skimage.measure import find_contours
from pyproj import CRS, Transformer


def cartesian_grid(cart):

    data = cart["data"]
    where = cart["where"]

    proj = where.get("projdef")

    if not proj:
        raise ValueError(
            "ODIM composite has no projdef"
        )

    if str(proj).startswith("+"):
        crs = CRS.from_proj4(proj)
    else:
        crs = CRS.from_user_input(proj)

    to_ll = Transformer.from_crs(
        crs,
        4326,
        always_xy=True
    )

    from_ll = Transformer.from_crs(
        4326,
        crs,
        always_xy=True
    )

    ul_lon = float(
        where["UL_lon"]
    )

    ul_lat = float(
        where["UL_lat"]
    )

    x0, y0 = from_ll.transform(
        ul_lon,
        ul_lat
    )

    xs = float(
        where["xscale"]
    )

    ys = float(
        where["yscale"]
    )

    return (
        data,
        where,
        to_ll,
        x0,
        y0,
        xs,
        ys
    )


def detect_cells(
    cart,
    threshold=32,
    max_cells=120
):

    (
        data,
        where,
        to_ll,
        x0,
        y0,
        xs,
        ys
    ) = cartesian_grid(cart)

    mask = (
        np.isfinite(data)
        & (data >= threshold)
    )

    labels, count = label(
        mask,
        structure=np.ones(
            (3, 3),
            dtype=np.uint8
        )
    )

    cells = []

    for index in range(
        1,
        count + 1
    ):

        yy, xx = np.where(
            labels == index
        )

        if len(xx) < 6:
            continue

        values = data[
            yy,
            xx
        ]

        cy = float(
            np.mean(yy)
        )

        cx = float(
            np.mean(xx)
        )

        x = (
            x0
            + (cx + 0.5) * xs
        )

        y = (
            y0
            - (cy + 0.5) * ys
        )

        lon, lat = to_ll.transform(
            x,
            y
        )

        contours = find_contours(
            (
                labels == index
            ).astype("uint8"),
            0.5
        )

        ring = []

        if contours:

            contour = max(
                contours,
                key=len
            )

            step = max(
                1,
                len(contour) // 180
            )

            for row, col in contour[::step]:

                px = (
                    x0
                    + (col + 0.5) * xs
                )

                py = (
                    y0
                    - (row + 0.5) * ys
                )

                lo, la = to_ll.transform(
                    px,
                    py
                )

                ring.append([
                    lo,
                    la
                ])

            if (
                ring
                and ring[0]
                != ring[-1]
            ):
                ring.append(
                    ring[0]
                )

        cells.append({

            "id":
                f"EU-{index:04d}",

            "centroid":
                [lat, lon],

            "dbz_max":
                float(
                    np.nanmax(values)
                ),

            "dbz_mean":
                float(
                    np.nanmean(values)
                ),

            "pixel_count":
                int(len(values)),

            "area_km2":
                float(
                    len(values)
                    * abs(xs * ys)
                    / 1e6
                ),

            "footprint":
                ring,

            "bbox_pixels": [
                int(xx.min()),
                int(yy.min()),
                int(xx.max()),
                int(yy.max())
            ]
        })

    cells.sort(
        key=lambda c: (
            c["dbz_max"],
            c["pixel_count"]
        ),
        reverse=True
    )

    return cells[:max_cells]
