import io
import h5py
import numpy as np


def _val(group, key, default=None):

    if group is None:
        return default

    if key not in group.attrs:
        return default

    value = group.attrs[key]

    if isinstance(value, bytes):
        return value.decode(
            "utf-8",
            "ignore"
        )

    if (
        isinstance(value, np.ndarray)
        and value.size == 1
    ):
        return value.reshape(-1)[0].item()

    return value


def read_odim(
    blob,
    quantity="DBZH"
):

    scans = []
    cartesian = []

    with h5py.File(
        io.BytesIO(blob),
        "r"
    ) as f:

        root_what = f.get("what")
        root_where = f.get("where")

        root_source = _val(
            root_what,
            "source",
            ""
        )

        for name in sorted(
            k for k in f.keys()
            if k.startswith("dataset")
        ):

            group = f[name]

            where = group.get("where")
            what = group.get("what")

            if "data1" not in group:
                continue

            data_group = group["data1"]

            quantity_name = str(
                _val(
                    data_group.get("what"),
                    "quantity",
                    ""
                )
            )

            if (
                quantity
                and quantity_name
                and quantity_name.upper()
                != quantity.upper()
            ):
                continue

            raw = data_group["data"][()]

            gain = float(
                _val(
                    data_group.get("what"),
                    "gain",
                    1.0
                )
            )

            offset = float(
                _val(
                    data_group.get("what"),
                    "offset",
                    0.0
                )

            data = (
                raw.astype("float32")
                * gain
                + offset
            )

            nodata = _val(
                data_group.get("what"),
                "nodata"
            )

            undetect = _val(
                data_group.get("what"),
                "undetect"
            )

            if nodata is not None:
                data[raw == nodata] = np.nan

            if undetect is not None:
                data[
                    raw == undetect
                ] = np.nan

            object_name = str(
                _val(
                    what,
                    "object",
                    ""
                )
            )

            # Cartesian/composite
            if (
                object_name
                in ("COMP", "IMAGE", "")
                and where is not None
                and "xscale" in where.attrs
            ):

                cartesian.append({
                    "name": name,
                    "data": data,
                    "where": {
                        key: _val(where, key)
                        for key in where.attrs.keys()
                    },

                    "what": {
                        key: _val(what, key)
                        for key in what.attrs.keys()
                    }
                    if what else {}
                })

            # Polar scans
            elif where is not None:

                scans.append({

                    "name": name,

                    "dbzh": data,

                    "elangle_deg":
                        float(
                            _val(
                                where,
                                "elangle",
                                0.5
                            )
                        ),

                    "nrays":
                        int(
                            _val(
                                where,
                                "nrays",
                                data.shape[0]
                            )
                        ),

                    "nbins":
                        int(
                            _val(
                                where,
                                "nbins",
                                data.shape[1]
                            )
                        ),

                    "rstart_m":
                        float(
                            _val(
                                where,
                                "rstart",
                                0.0
                            )
                        ),

                    "rscale_m":
                        float(
                            _val(
                                where,
                                "rscale",
                                1000.0
                            )
                        ),

                    "lon":
                        float(
                            _val(
                                where,
                                "lon",
                                _val(
                                    root_where,
                                    "lon",
                                    0.0
                                )
                            )
                        ),

                    "lat":
                        float(
                            _val(
                                where,
                                "lat",
                                _val(
                                    root_where,
                                    "lat",
                                    0.0
                                )
                            )
                        ),

                    "height_m":
                        float(
                            _val(
                                where,
                                "height",
                                _val(
                                    root_where,
                                    "height",
                                    0.0
                                )
                            )
                        ),

                    "what": {
                        key: _val(what, key)
                        for key in what.attrs.keys()
                    }
                    if what else {},

                    "source":
                        root_source
                })

    return {
        "scans": scans,
        "cartesian": cartesian,
        "root": {
            "source": root_source
        }
    }


def latest_cartesian(
    blob,
    quantity="DBZH"
):

    result = read_odim(
        blob,
        quantity
    )

    if not result["cartesian"]:

        raise ValueError(
            "No Cartesian/composite ODIM dataset found"
        )

    return result["cartesian"][0]
