import os

import numpy as np
import rasterio
from PIL import Image

RED = (220, 38, 38)
YELLOW = (234, 179, 8)
GREEN = (34, 197, 94)
TRANSPARENT = (0, 0, 0, 0)

# fire_risk_*_grid.tif / fire_risk_*_kecamatan.tif, band 1: tier ordinal
# (1=LOW, 2=MEDIUM, 3=HIGH). PRD §5/F4: red=high, yellow=mid, green=low.
FIRE_TIER_COLORS = {1: GREEN, 2: YELLOW, 3: RED}

# landslide_risk_*.tif, band 2: PRD §5/F4 documents exactly 3 values
# (2=red, 3=yellow, 4=green) out of the table's 5 risk_category + "masked"
# range -- real samples show other values too (e.g. w30 has a 1). Anything
# outside the documented 3 renders transparent rather than guessing a color
# the spec never assigned.
LANDSLIDE_RISK_COLORS = {2: RED, 3: YELLOW, 4: GREEN}


def _discrete_rgba(band: np.ndarray, colors: dict[int, tuple]) -> np.ndarray:
    rgba = np.zeros((*band.shape, 4), dtype=np.uint8)
    for value, color in colors.items():
        rgba[band == value] = (*color, 255)
    return rgba


def _burned_area_rgba(band: np.ndarray) -> np.ndarray:
    """band 1, 0.0-1.0: 0=red, 0.5=yellow, 1=green (linear gradient)."""
    valid = (band >= 0) & (band <= 1)
    v = np.clip(band, 0, 1)
    xp = [0, 0.5, 1]
    r = np.interp(v, xp, [RED[0], YELLOW[0], GREEN[0]])
    g = np.interp(v, xp, [RED[1], YELLOW[1], GREEN[1]])
    b = np.interp(v, xp, [RED[2], YELLOW[2], GREEN[2]])
    rgba = np.stack([r, g, b, np.where(valid, 255, 0)], axis=-1)
    return rgba.astype(np.uint8)


_fire_tier_rgba = lambda band: _discrete_rgba(band, FIRE_TIER_COLORS)

RASTER_LAYERS = {
    "fire_grid": (1, _fire_tier_rgba),
    "fire_kecamatan": (1, _fire_tier_rgba),
    "burned_area": (1, _burned_area_rgba),
    "landslide_risk": (2, lambda band: _discrete_rgba(band, LANDSLIDE_RISK_COLORS)),
}


def rasterize(tif_path: str, layer_type: str, out_path: str) -> list:
    """Colorize tif_path's relevant band per layer_type's PRD §5/F4 scheme,
    write a PNG to out_path, return bounds as [[south,west],[north,east]]
    (Leaflet ImageOverlay convention)."""
    band_index, color_fn = RASTER_LAYERS[layer_type]
    with rasterio.open(tif_path) as ds:
        band = ds.read(band_index)
        west, south, east, north = ds.bounds
        if ds.crs is not None and ds.crs.to_epsg() != 4326:
            from rasterio.warp import transform_bounds
            west, south, east, north = transform_bounds(ds.crs, "EPSG:4326", west, south, east, north)

    rgba = color_fn(band)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    Image.fromarray(rgba, mode="RGBA").save(out_path)
    return [[south, west], [north, east]]
