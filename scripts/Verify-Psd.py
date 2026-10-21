"""Independent PSD validation. Dev-only dependencies: psd-tools==1.26.0, Pillow, numpy."""
from pathlib import Path
import sys
import numpy as np
from psd_tools import PSDImage

root = Path(sys.argv[1] if len(sys.argv) > 1 else "artifacts/validation")
occlusion = PSDImage.open(root / "occlusion.psd")
assert occlusion.size == (96, 64)
assert len(occlusion) == 2
names = {layer.name for layer in occlusion}
assert "#E65032 建筑 / 墙面" in names and "#3282C8 铺装" in names, names
merged = occlusion.topil().convert("RGBA")
assert merged.getpixel((48, 32)) == (230, 80, 50, 255)
assert merged.getpixel((15, 32)) == (50, 130, 200, 255)
assert merged.getpixel((0, 0))[3] == 0

psd = PSDImage.open(root / "antialias.psd")
reference = np.fromfile(root / "antialias.rgba", dtype=np.uint8).reshape(65, 97, 4)
stored = np.asarray(psd.topil().convert("RGBA"))
assert np.array_equal(stored[:, :, 3], reference[:, :, 3]), "Stored composite alpha differs from reference"
recomposed = np.asarray(psd.composite(force=True).convert("RGBA"))
# Compare premultiplied RGB: invisible RGB values are not meaningful.
def premul(data):
    result = data.astype(float)
    result[:, :, :3] *= result[:, :, 3:4] / 255
    return result
stored_error = float(np.abs(premul(stored) - premul(reference)).max())
assert stored_error <= 2, f"Stored composite mismatch: {stored_error}"
error = float(np.abs(premul(recomposed) - premul(reference)).max())
assert error <= 2, f"Layer recomposition mismatch: {error}"
psd.composite(force=True).save(root / "antialias-preview.png")
print(f"PASS: independent PSD parser, Unicode names, occlusion, RGBA, layer recomposition (max error {error:.3f}/255).")
