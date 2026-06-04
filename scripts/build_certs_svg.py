#!/usr/bin/env python3
"""Build an auto-scrolling, base64-embedded animated SVG carousel of certificates.

Pipeline (macOS-native, no poppler/ffmpeg needed):
  1. qlmanage -t  -> rasterize each cert (PDF/PNG) to a thumbnail PNG.
  2. sips         -> downscale + re-encode to small JPEG (q50, 360px wide).
  3. base64 embed -> inline each card image into one SVG.
  4. SMIL animateTransform -> seamless horizontal marquee (track duplicated x2).

The SVG references nothing external, so it renders on the GitHub profile README
via <img src="assets/certs.svg">. Re-run after adding/removing certs.

Usage:  python3 scripts/build_certs_svg.py
Output: assets/certs.svg
"""

import base64
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CERT_DIR = REPO / "Certificates"
OUT = REPO / "assets" / "certs.svg"

# Curated, recognizable marquee set: (filename, short label)
CERTS = [
    ("Deep_Learning_specialization.pdf", "Deep Learning Specialization"),
    ("Machine_Larning_Specialisation.pdf", "Machine Learning Specialization"),
    ("TF_developer.pdf", "TensorFlow Developer"),
    ("Generative_AI.pdf", "Generative AI"),
    ("CS50AI.pdf", "CS50 · AI with Python"),
    ("CS50P.pdf", "CS50 · Python"),
    ("CS50WEB.pdf", "CS50 · Web"),
    ("CS50_SQL.pdf", "CS50 · SQL"),
    ("CS50Cybersecurity.pdf", "CS50 · Cybersecurity"),
    ("Data_Analytics.pdf", "Google Data Analytics"),
    ("FullStack.pdf", "Full-Stack Development"),
    ("Leetcode_50.png", "LeetCode · 50 Days"),
]

# Card geometry
CARD_W = 240
CARD_H = 150
IMG_H = 118          # image area height; rest is the label bar
GAP = 18
PAD = 8
LABEL_H = CARD_H - IMG_H
TRACK_GAP = GAP
SVG_H = CARD_H + 24  # breathing room top/bottom
SPEED_PX_PER_S = 36  # marquee velocity


def rasterize(src: Path, tmp: Path) -> Path:
    """Rasterize a PDF/PNG cert to a small JPEG, return its path."""
    thumb = tmp / (src.stem + ".png")
    subprocess.run(
        ["qlmanage", "-t", "-s", "640", "-o", str(tmp), str(src)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    # qlmanage names the thumb "<originalname>.png"
    produced = tmp / (src.name + ".png")
    if not produced.exists():
        # PNG sources: qlmanage may skip; fall back to the source itself
        produced = src
    jpg = tmp / (src.stem + "_card.jpg")
    subprocess.run(
        ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "50",
         "-Z", "360", str(produced), "--out", str(jpg)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return jpg


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build():
    if not CERT_DIR.is_dir():
        sys.exit(f"cert dir missing: {CERT_DIR}")
    OUT.parent.mkdir(parents=True, exist_ok=True)

    cards = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for fname, label in CERTS:
            src = CERT_DIR / fname
            if not src.exists():
                print(f"  skip (missing): {fname}", file=sys.stderr)
                continue
            jpg = rasterize(src, tmp)
            cards.append((b64(jpg), label))
            print(f"  embedded: {label}")

    if not cards:
        sys.exit("no cert cards produced")

    n = len(cards)
    step = CARD_W + GAP
    track_w = n * step                      # one full pass width
    total_w = track_w * 2                    # duplicated for seamless loop
    duration = track_w / SPEED_PX_PER_S      # seconds for one pass

    def card_group(idx, data_uri_b64, label, x):
        return f'''    <g transform="translate({x},12)">
      <rect width="{CARD_W}" height="{CARD_H}" rx="12" ry="12" fill="#11151c" stroke="#222b36" stroke-width="1"/>
      <clipPath id="clip{idx}"><rect x="{PAD}" y="{PAD}" width="{CARD_W-2*PAD}" height="{IMG_H-PAD}" rx="8" ry="8"/></clipPath>
      <image x="{PAD}" y="{PAD}" width="{CARD_W-2*PAD}" height="{IMG_H-PAD}" clip-path="url(#clip{idx})" preserveAspectRatio="xMidYMid slice" href="data:image/jpeg;base64,{data_uri_b64}"/>
      <rect x="{PAD}" y="{IMG_H}" width="{CARD_W-2*PAD}" height="{LABEL_H-PAD}" rx="6" ry="6" fill="#0d1117"/>
      <text x="{CARD_W/2}" y="{IMG_H+LABEL_H/2}" fill="#c9d4e0" font-family="'Segoe UI',Helvetica,Arial,sans-serif" font-size="11.5" font-weight="600" text-anchor="middle" dominant-baseline="middle">{esc(label)}</text>
    </g>'''

    groups = []
    # two identical passes back-to-back
    for pass_i in range(2):
        base_x = pass_i * track_w
        for i, (uri, label) in enumerate(cards):
            x = base_x + i * step
            groups.append(card_group(f"{pass_i}_{i}", uri, label, x))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="100%" viewBox="0 0 {track_w} {SVG_H}" role="img" aria-label="Certificate carousel">
  <defs>
    <linearGradient id="fadeL" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0" stop-color="#0d1117" stop-opacity="1"/>
      <stop offset="1" stop-color="#0d1117" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="fadeR" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0" stop-color="#0d1117" stop-opacity="0"/>
      <stop offset="1" stop-color="#0d1117" stop-opacity="1"/>
    </linearGradient>
  </defs>
  <g>
    <animateTransform attributeName="transform" type="translate"
      from="0 0" to="-{track_w} 0" dur="{duration:.1f}s"
      repeatCount="indefinite" additive="sum"/>
{chr(10).join(groups)}
  </g>
  <rect x="0" y="0" width="64" height="{SVG_H}" fill="url(#fadeL)"/>
  <rect x="{track_w-64}" y="0" width="64" height="{SVG_H}" fill="url(#fadeR)"/>
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    kb = len(svg.encode("utf-8")) / 1024
    print(f"\nwrote {OUT.relative_to(REPO)}  ({n} cards, {kb:.0f} KB, loop {duration:.1f}s)")
    if kb > 1500:
        print("WARNING: SVG over 1.5 MB — reduce cert count or quality", file=sys.stderr)


if __name__ == "__main__":
    build()
