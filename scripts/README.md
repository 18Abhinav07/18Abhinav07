# Profile asset scripts

Reproducible builders for the assets embedded in the profile `README.md`.

## `build_certs_svg.py` — certifications carousel
Rasterizes a curated set of certificates (PDF/PNG) with macOS-native
`qlmanage` + `sips`, base64-embeds them, and emits an auto-scrolling
SMIL-animated SVG marquee at `assets/certs.svg`.

```bash
python3 scripts/build_certs_svg.py
```
Edit the `CERTS` list to change which certificates appear. Keep the output
under ~1.5 MB (GitHub renders the SVG inline).

## Hero GIF — `assets/hero.gif`
When the Gemini 8-bit clip (`hero.mp4`) is ready, convert with a palette pass
for clean color at small size, then uncomment the HERO SLOT block at the top of
`README.md`.

```bash
# requires ffmpeg (brew install ffmpeg)
ffmpeg -i hero.mp4 -vf "fps=15,scale=900:-1:flags=lanczos,palettegen=stats_mode=diff" -y palette.png
ffmpeg -i hero.mp4 -i palette.png \
  -lavfi "fps=15,scale=900:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3" \
  -y assets/hero.gif
```
Target < 5 MB. If larger, drop `fps=15`→`12` or `scale=900`→`720`.
