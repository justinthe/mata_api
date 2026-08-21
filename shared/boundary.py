import json

from geoalchemy2.shape import from_shape
from shapely import force_2d
from shapely.geometry import shape
from shapely.ops import unary_union

# Authoritative kecamatan_id -> name roster, taken verbatim from the real sample
# data's fire_risk_*.json `by_kecamatan` array (identical across weeks — the
# roster is a fixed reference set, not week-scoped). KEC-01..26 are real
# Majalengka kecamatan; KEC-27..45 are real Indonesian kecamatan names the
# synthetic data generator borrowed from neighboring regencies (Sumedang,
# Kuningan, Cirebon, Indramayu, Tasikmalaya/Ciamis) to pad the roster to 45 —
# every kecamatan_id any real sample file references gets a boundary row here.
MAJALENGKA_KECAMATAN = [
    ("KEC-01", "Argapura"), ("KEC-02", "Bantarujeg"), ("KEC-03", "Cikijing"),
    ("KEC-04", "Cingambul"), ("KEC-05", "Dawuan"), ("KEC-06", "Jati Tujuh"),
    ("KEC-07", "Jatiwangi"), ("KEC-08", "Kadipaten"), ("KEC-09", "Kasokandel"),
    ("KEC-10", "Kertajati"), ("KEC-11", "Lemah Sugih"), ("KEC-12", "Leuwi Munding"),
    ("KEC-13", "Ligung"), ("KEC-14", "Maja"), ("KEC-15", "Majalengka"),
    ("KEC-16", "Malausma"), ("KEC-17", "Palasah"), ("KEC-18", "Panyingkiran"),
    ("KEC-19", "Pembantu Banjaran"), ("KEC-20", "Pembantu Cigasong"),
    ("KEC-21", "Rajagaluh"), ("KEC-22", "Sindang"), ("KEC-23", "Sindangwangi"),
    ("KEC-24", "Sukahaji"), ("KEC-25", "Sumber Jaya"), ("KEC-26", "Talaga"),
    ("KEC-27", "Bagodua"), ("KEC-28", "Cigugur"), ("KEC-29", "Cikedung"),
    ("KEC-30", "Ciwaringin"), ("KEC-31", "Darma"), ("KEC-32", "Dukupuntang"),
    ("KEC-33", "Gempol"), ("KEC-34", "Jatinuggal"), ("KEC-35", "Kartasemaya"),
    ("KEC-36", "Pagerageung"), ("KEC-37", "Panawangan"), ("KEC-38", "Pesawahan"),
    ("KEC-39", "Sindang Ampar"), ("KEC-40", "Sukamantri"), ("KEC-41", "Susukan"),
    ("KEC-42", "Terisi"), ("KEC-43", "Tomo"), ("KEC-44", "Ujungjaya"),
    ("KEC-45", "Wado"),
]


def dissolve_kelurahan_to_kecamatan(geojson_path: str) -> list[dict]:
    with open(geojson_path) as f:
        data = json.load(f)

    polygons_by_name: dict[str, list] = {}
    for feature in data["features"]:
        name = feature["properties"]["WADMKC"]
        polygons_by_name.setdefault(name, []).append(shape(feature["geometry"]))

    rows = []
    for kecamatan_id, kecamatan_name in MAJALENGKA_KECAMATAN:
        parts = polygons_by_name.get(kecamatan_name)
        if not parts:
            continue
        dissolved = unary_union(parts)
        if dissolved.geom_type == "MultiPolygon":
            # DATABASE.md workaround: kecamatan_boundary.geom is typed Polygon,
            # so a dissolved border-fragment kecamatan keeps only its largest part.
            dissolved = max(dissolved.geoms, key=lambda p: p.area)
        rows.append({
            "kecamatan_id": kecamatan_id,
            "kecamatan_name": kecamatan_name,
            # source kelurahan.geojson polygons carry a Z dimension; the DB
            # column is 2D geometry(Polygon, 4326).
            "geom": from_shape(force_2d(dissolved), srid=4326),
        })
    return rows
