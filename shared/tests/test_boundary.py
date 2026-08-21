import json

from geoalchemy2.shape import to_shape
from shapely.geometry import Polygon, mapping

from shared.boundary import MAJALENGKA_KECAMATAN, dissolve_kelurahan_to_kecamatan


def test_dissolve_returns_all_45_kecamatan():
    rows = dissolve_kelurahan_to_kecamatan("data/kelurahan.geojson")

    assert len(rows) == 45
    ids = {row["kecamatan_id"] for row in rows}
    assert ids == {kec_id for kec_id, _ in MAJALENGKA_KECAMATAN}
    for row in rows:
        assert row["geom"] is not None


def test_multipolygon_dissolve_keeps_largest_sub_polygon(tmp_path):
    # Two disjoint squares sharing one kecamatan name -> dissolves to a
    # MultiPolygon; only the larger square should survive.
    small = Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])
    big = Polygon([(10, 10), (10, 13), (13, 13), (13, 10)])
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"WADMKC": "Argapura", "WADMKK": "Kabupaten Majalengka"}, "geometry": mapping(small)},
            {"type": "Feature", "properties": {"WADMKC": "Argapura", "WADMKK": "Kabupaten Majalengka"}, "geometry": mapping(big)},
        ],
    }
    path = tmp_path / "fragment.geojson"
    path.write_text(json.dumps(geojson))

    rows = dissolve_kelurahan_to_kecamatan(str(path))

    assert len(rows) == 1
    assert rows[0]["kecamatan_id"] == "KEC-01"
    geom = to_shape(rows[0]["geom"])
    assert geom.geom_type == "Polygon"
    assert geom.area == big.area
