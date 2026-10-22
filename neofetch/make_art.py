"""Turn one frame of assets/output.gif into coloured ASCII art (neofetch/art.json).

Run once by hand; CI only reads art.json.

  pip install pillow numpy onnxruntime
  curl -LO https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx
  python neofetch/make_art.py --model u2netp.onnx [--frame 50] [--crop x0,y0,x1,y1] [--cols 48]

The U2-Net model cuts the person out of the city background so the art reads as a logo;
bright flame-coloured pixels are added back so the burning Python logo survives the cut.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parent
RAMP = " .:-=+*#%@"  # light to dense; the subject never drops below ":"
ASPECT = 10.6 / (8.8 * 0.6)  # character cell height / width (8.8px Plex Mono, 10.6px line height)


def person_mask(im, model):
    import onnxruntime as ort
    x = np.asarray(im.resize((320, 320), Image.LANCZOS), dtype=np.float32) / 255.0
    x = (x / x.max() - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    sess = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
    m = sess.run(None, {sess.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
    m = (m - m.min()) / (m.max() - m.min())
    return Image.fromarray((m * 255).astype(np.uint8)).resize(im.size, Image.LANCZOS)


def flame_mask(im):
    a = np.asarray(im, dtype=np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    hot = (r > 170) & (r - b > 70) | (r > 200) & (g > 170) & (b < 140)
    hot[200:] = False  # the flame sits in the top of the frame; lower neon signs are background
    return Image.fromarray((hot * 255).astype(np.uint8))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--src", default=str(ROOT.parent / "assets" / "output.gif"))
    p.add_argument("--frame", type=int, default=50)
    p.add_argument("--crop", default="165,0,525,450")
    p.add_argument("--cols", type=int, default=75)
    p.add_argument("--gamma", type=float, default=0.8)
    p.add_argument("--model", help="U2-Net .onnx file; omit to convert the whole frame")
    a = p.parse_args()

    im = Image.open(a.src)
    im.seek(a.frame)
    im = im.convert("RGB")
    cut = im.convert("RGBA")
    if a.model:
        cut.putalpha(ImageChops.lighter(person_mask(im, a.model), flame_mask(im)))
    box = tuple(int(v) for v in a.crop.split(","))
    cut = cut.crop(box)

    w, h = cut.size
    rows = round(h / (w / a.cols) / ASPECT)
    small = cut.resize((a.cols, rows), Image.LANCZOS)
    rgb = ImageEnhance.Brightness(ImageEnhance.Color(small.convert("RGB")).enhance(1.4)).enhance(1.35)
    lum = ImageOps.autocontrast(rgb.convert("L"), cutoff=1)
    alpha = small.getchannel("A")

    out = []
    for y in range(rows):
        chars, colors = "", []
        for x in range(a.cols):
            if alpha.getpixel((x, y)) < 70:
                chars += " "
                colors.append("#000000")
                continue
            v = (lum.getpixel((x, y)) / 255) ** a.gamma
            chars += RAMP[max(2, min(len(RAMP) - 1, int(v * len(RAMP))))]
            r, g, b = rgb.getpixel((x, y))
            # lift dark pixels so every character stays visible on a dark terminal
            lift = max(0, 135 - max(r, g, b))
            colors.append("#%02x%02x%02x" % tuple(min(255, c + lift) for c in (r, g, b)))
        out.append({"chars": chars, "colors": colors})
    # trim empty rows top and bottom
    while out and not out[0]["chars"].strip():
        out.pop(0)
    while out and not out[-1]["chars"].strip():
        out.pop()
    (ROOT / "art.json").write_text(json.dumps({"source": f"{Path(a.src).name} frame {a.frame}", "rows": out}))
    print("\n".join(r["chars"] for r in out))


if __name__ == "__main__":
    main()
