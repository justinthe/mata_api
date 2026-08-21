import numpy as np
import rasterio
from PIL import Image

from ingest.rasterize import GREEN, RED, YELLOW, rasterize

W31 = "data/2026_w31"


def test_fire_grid_tier_colors(tmp_path):
    out = tmp_path / "fire_grid.png"
    bounds = rasterize(f"{W31}/fire_risk_2026-W31_grid.tif", "fire_grid", str(out))

    with rasterio.open(f"{W31}/fire_risk_2026-W31_grid.tif") as ds:
        assert bounds == [[ds.bounds.bottom, ds.bounds.left], [ds.bounds.top, ds.bounds.right]]

    img = np.array(Image.open(out))
    assert tuple(img[4, 5][:3]) == RED       # tier=3 (HIGH)
    assert tuple(img[0, 8][:3]) == GREEN     # tier=1 (LOW)
    assert img[0, 0][3] == 0                 # nodata -9999 -> transparent


def test_landslide_risk_category_colors(tmp_path):
    out = tmp_path / "landslide.png"
    rasterize(f"{W31}/landslide_risk_2026-W31.tif", "landslide_risk", str(out))

    img = np.array(Image.open(out))
    assert tuple(img[552, 126][:3]) == RED     # category=2
    assert tuple(img[550, 131][:3]) == YELLOW  # category=3
    assert tuple(img[562, 120][:3]) == GREEN   # category=4


def test_burned_area_gradient_endpoints(tmp_path):
    out = tmp_path / "burned.png"
    rasterize(f"{W31}/fire_sar_burned_area_2026-W31.tif", "burned_area", str(out))

    with rasterio.open(f"{W31}/fire_sar_burned_area_2026-W31.tif") as ds:
        band = ds.read(1)
    img = np.array(Image.open(out))

    zero_px = np.argwhere(band == 0)[0]
    one_px = np.argwhere(band == 1)[0]
    assert tuple(img[tuple(zero_px)][:3]) == RED
    assert tuple(img[tuple(one_px)][:3]) == GREEN
