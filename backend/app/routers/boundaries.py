from fastapi import APIRouter
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping

from shared.db import read_rows

router = APIRouter()


@router.get("/boundaries")
def list_boundaries() -> dict:
    rows = read_rows("kecamatan_boundary")
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"kecamatan_id": r["kecamatan_id"], "kecamatan_name": r["kecamatan_name"]},
                "geometry": mapping(to_shape(r["geom"])),
            }
            for r in rows
        ],
    }
