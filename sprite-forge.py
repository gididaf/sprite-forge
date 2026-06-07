#!/usr/bin/env python3
"""
sprite-forge.py — Convert animated SVGs to PNG sprite sheets.

Bakes SMIL animation keyframes into static frames, renders each via
rsvg-convert, and stitches them into a horizontal sprite sheet PNG.

Usage:
    sprite-forge hero_walk_left.svg
    sprite-forge hero_walk_left.svg --frames 8 --size 128 --preview
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

try:
    from PIL import Image, ImageOps, ImageChops, ImageStat
except ImportError:
    print("Error: Pillow is required. Install with: pip3 install Pillow", file=sys.stderr)
    sys.exit(1)

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)


# ── Stage 1: Parse & detect duration ─────────────────────────────────────────

def detect_duration(svg_text: str) -> float:
    """Find the most common animation duration in the SVG (the primary cycle)."""
    durs = re.findall(r'dur="([\d.]+)s?"', svg_text)
    if not durs:
        return 0.6
    counts = Counter(float(d) for d in durs)
    return counts.most_common(1)[0][0]


# ── Stage 2: Animation baking engine ─────────────────────────────────────────

def lerp_string(a: str, b: str, t: float) -> str:
    """Interpolate all numeric values between two keyframe strings."""
    nums_a = re.findall(r"-?[\d.]+", a)
    nums_b = re.findall(r"-?[\d.]+", b)

    if len(nums_a) != len(nums_b) or not nums_a:
        return a if t < 0.5 else b

    idx = 0

    def replacer(match):
        nonlocal idx
        va = float(nums_a[idx])
        vb = float(nums_b[idx])
        idx += 1
        return f"{va + (vb - va) * t:.3f}"

    return re.sub(r"-?[\d.]+", replacer, a)


def get_value_at_time(anim_el: ET.Element, time: float) -> str | None:
    """Compute the interpolated animation value at a given time."""
    dur_attr = anim_el.get("dur")
    values_attr = anim_el.get("values")
    if not dur_attr or not values_attr:
        return None

    dur = float(re.search(r"[\d.]+", dur_attr).group())
    keyframes = [v.strip() for v in values_attr.split(";")]
    n = len(keyframes)
    if n < 2:
        return keyframes[0] if keyframes else None

    progress = (time % dur) / dur
    segments = n - 1
    pos = progress * segments
    seg = min(int(pos), segments - 1)
    frac = pos - seg

    return lerp_string(keyframes[seg], keyframes[seg + 1], frac)


def bake_frame(svg_text: str, time: float) -> str:
    """Parse SVG, bake animation state at `time` into static attributes, return SVG string."""
    root = ET.fromstring(svg_text)

    removals = []

    for parent in root.iter():
        for child in list(parent):
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag not in ("animate", "animateTransform"):
                continue

            val = get_value_at_time(child, time)
            if val is None:
                removals.append((parent, child))
                continue

            if tag == "animateTransform":
                transform_type = child.get("type", "translate")
                additive = child.get("additive", "replace")
                new_transform = f"{transform_type}({val})"
                existing = parent.get("transform", "")
                if additive == "sum" and existing:
                    parent.set("transform", f"{existing} {new_transform}")
                else:
                    parent.set("transform", new_transform)
            else:
                attr_name = child.get("attributeName")
                if attr_name:
                    parent.set(attr_name, val)

            removals.append((parent, child))

    for parent, child in removals:
        parent.remove(child)

    return ET.tostring(root, encoding="unicode", xml_declaration=True)


# ── Stage 3: Render SVG to PNG via rsvg-convert ─────────────────────────────

def check_rsvg():
    """Verify rsvg-convert is available."""
    if shutil.which("rsvg-convert") is None:
        print("Error: rsvg-convert not found. Install with: brew install librsvg", file=sys.stderr)
        sys.exit(1)


def render_svg_to_png(svg_string: str, output_path: str, size: int):
    """Render an SVG string to a PNG file using rsvg-convert."""
    result = subprocess.run(
        ["rsvg-convert", "-w", str(size), "-h", str(size), "-o", output_path],
        input=svg_string.encode("utf-8"),
        capture_output=True,
    )
    if result.returncode != 0:
        print(f"rsvg-convert error: {result.stderr.decode()}", file=sys.stderr)
        raise RuntimeError(f"rsvg-convert failed for {output_path}")


# ── Stage 4: Stitch frames into sprite sheet ─────────────────────────────────

def stitch_frames(frame_paths: list[str], size: int, output_path: str):
    """Combine individual frame PNGs into a horizontal sprite sheet."""
    count = len(frame_paths)
    sheet = Image.new("RGBA", (size * count, size), (0, 0, 0, 0))

    for i, path in enumerate(frame_paths):
        frame = Image.open(path).convert("RGBA")
        sheet.paste(frame, (i * size, 0))

    sheet.save(output_path, "PNG")
    return sheet


def generate_mirror(sheet: Image.Image, size: int, frame_count: int, output_path: str):
    """Create a horizontally-flipped sprite sheet (flip each frame individually)."""
    mirrored = Image.new("RGBA", sheet.size, (0, 0, 0, 0))

    for i in range(frame_count):
        frame = sheet.crop((i * size, 0, (i + 1) * size, size))
        frame = ImageOps.mirror(frame)
        mirrored.paste(frame, (i * size, 0))

    mirrored.save(output_path, "PNG")
    return mirrored


def flip_frames(frame_paths: list[str], tmp_dir: str) -> list[str]:
    """Horizontally flip each frame PNG, writing the results to new files."""
    flipped_paths = []
    for i, path in enumerate(frame_paths):
        frame = ImageOps.mirror(Image.open(path).convert("RGBA"))
        out = os.path.join(tmp_dir, f"flip_frame_{i:03d}.png")
        frame.save(out, "PNG")
        flipped_paths.append(out)
    return flipped_paths


def write_silhouette(frame_path: str, output_path: str):
    """Convert a frame to a pure black-on-white silhouette for readability inspection."""
    src = Image.open(frame_path).convert("RGBA")
    bg = Image.new("RGBA", src.size, (255, 255, 255, 255))
    alpha = src.split()[3]
    silhouette = Image.new("RGBA", src.size, (0, 0, 0, 255))
    bg.paste(silhouette, mask=alpha)
    bg.convert("RGB").save(output_path, "PNG")


def write_gif(frame_paths: list[str], duration: float, output_path: str):
    """Stitch individual frame PNGs into an animated GIF with transparent background."""
    frames = [Image.open(p).convert("RGBA") for p in frame_paths]
    frame_ms = int(round((duration / len(frames)) * 1000))
    frames[0].save(
        output_path,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=frame_ms,
        loop=0,
        disposal=2,
        transparency=0,
    )


def write_metadata(output_path: str, source: str, frame_count: int, size: int,
                   duration: float, mirror_path: str | None,
                   facing: str | None = None, mirror_of: str | None = None):
    """Write a JSON metadata file for game engine import."""
    meta = {
        "source": source,
        "frameCount": frame_count,
        "frameWidth": size,
        "frameHeight": size,
        "sheetWidth": size * frame_count,
        "sheetHeight": size,
        "animationDuration": duration,
        "fps": round(frame_count / duration, 2),
    }
    if facing:
        meta["facing"] = facing
    if mirror_of:
        meta["mirrorOf"] = mirror_of
    if mirror_path:
        meta["mirror"] = os.path.basename(mirror_path)

    with open(output_path, "w") as f:
        json.dump(meta, f, indent=2)


# ── Preview HTML generation ──────────────────────────────────────────────────

def generate_preview(svg_path: str, sheet_path: str, mirror_path: str | None,
                     frame_count: int, size: int, duration: float, output_path: str):
    """Generate a self-contained preview HTML for visual inspection."""
    svg_name = os.path.basename(svg_path)
    sheet_name = os.path.basename(sheet_path)
    mirror_name = os.path.basename(mirror_path) if mirror_path else None
    fps = frame_count / duration

    mirror_section = ""
    if mirror_name:
        mirror_section = f"""
    <div class="section">
      <h3>Mirrored Sprite Sheet</h3>
      <img src="{mirror_name}" class="sheet checkerboard"/>
      <h3>Mirrored Playback</h3>
      <canvas id="mirror-preview" class="checkerboard" width="{size}" height="{size}"></canvas>
    </div>"""

    mirror_js = ""
    if mirror_name:
        mirror_js = f"""
      const mirrorImg = new Image();
      mirrorImg.src = "{mirror_name}";
      mirrorImg.onload = () => {{
        const mc = document.getElementById("mirror-preview");
        const mctx = mc.getContext("2d");
        let mi = 0;
        setInterval(() => {{
          mctx.clearRect(0, 0, {size}, {size});
          mctx.drawImage(mirrorImg, mi * {size}, 0, {size}, {size}, 0, 0, {size}, {size});
          mi = (mi + 1) % {frame_count};
        }}, {int(1000 / fps)});
      }};"""

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Preview: {svg_name}</title>
  <style>
    body {{ background: #1a1a2e; color: #eee; font-family: 'Segoe UI', sans-serif; padding: 30px; }}
    h1 {{ color: #e94560; }}
    h3 {{ color: #0f3460; margin-top: 25px; }}
    .section {{ margin: 20px 0; }}
    .sheet {{ display: block; margin: 10px 0; border: 2px solid #0f3460; }}
    .checkerboard {{ background-image: repeating-conic-gradient(#222 0% 25%, #2a2a2a 0% 50%); background-size: 16px 16px; }}
    .info {{ color: #888; font-size: 13px; }}
    .side-by-side {{ display: flex; gap: 30px; align-items: flex-start; }}
    canvas {{ border: 1px solid #333; image-rendering: pixelated; }}
    object {{ border: 1px solid #333; background: #16213e; }}
  </style>
</head>
<body>
  <h1>Sprite Preview: {svg_name}</h1>
  <p class="info">{frame_count} frames | {size}x{size}px | {duration}s cycle | {fps:.1f} fps</p>

  <div class="side-by-side">
    <div class="section">
      <h3>Live SVG Animation</h3>
      <object data="{svg_name}" type="image/svg+xml" width="{size*2}" height="{size*2}"></object>
    </div>
    <div class="section">
      <h3>Extracted Playback</h3>
      <canvas id="frame-preview" class="checkerboard" width="{size}" height="{size}"></canvas>
    </div>
  </div>

  <div class="section">
    <h3>Sprite Sheet</h3>
    <img src="{sheet_name}" class="sheet checkerboard"/>
  </div>
  {mirror_section}

  <script>
    const sheetImg = new Image();
    sheetImg.src = "{sheet_name}";
    sheetImg.onload = () => {{
      const c = document.getElementById("frame-preview");
      const ctx = c.getContext("2d");
      let i = 0;
      setInterval(() => {{
        ctx.clearRect(0, 0, {size}, {size});
        ctx.drawImage(sheetImg, i * {size}, 0, {size}, {size}, 0, 0, {size}, {size});
        i = (i + 1) % {frame_count};
      }}, {int(1000 / fps)});
    }};
    {mirror_js}
  </script>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)


# ── Pipeline ────────────────────────────────────────────────────────────────

def run_pipeline(svg_path: Path, args):
    """Run the sprite sheet pipeline on an SVG file."""
    check_rsvg()

    input_path = svg_path.resolve()
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    stem = input_path.stem
    out_dir = input_path.parent

    sheet_path = Path(args.output) if args.output else out_dir / f"{stem}_spritesheet.png"
    mirror_path = out_dir / f"{stem}_spritesheet_mirror.png" if args.mirror else None
    meta_path = out_dir / f"{stem}_spritesheet.json" if args.meta else None
    preview_path = out_dir / f"{stem}_preview.html" if args.preview else None
    gif_path = out_dir / f"{stem}.gif" if args.gif else None
    silhouette_path = out_dir / f"{stem}_silhouette.png" if args.silhouette else None

    svg_text = input_path.read_text(encoding="utf-8")
    duration = args.duration or detect_duration(svg_text)
    print(f"[parse] {input_path.name} | duration: {duration}s | extracting {args.frames} frames at {args.size}x{args.size}px")

    tmp_dir = tempfile.mkdtemp(prefix="spriteforge_")
    frame_paths = []

    for i in range(args.frames):
        t = (i / args.frames) * duration
        baked_svg = bake_frame(svg_text, t)
        frame_path = os.path.join(tmp_dir, f"frame_{i:03d}.png")
        render_svg_to_png(baked_svg, frame_path, args.size)
        frame_paths.append(frame_path)

    print(f"[render] {args.frames} frames rendered via rsvg-convert")

    sheet = stitch_frames(frame_paths, args.size, str(sheet_path))
    print(f"[spritesheet] {sheet_path.name} ({args.frames} frames, {args.size}x{args.size}, {sheet.width}x{sheet.height})")

    if mirror_path:
        generate_mirror(sheet, args.size, args.frames, str(mirror_path))
        print(f"[mirror] {mirror_path.name} ({args.frames} frames, {args.size}x{args.size}, flipped)")

    if gif_path:
        write_gif(frame_paths, duration, str(gif_path))
        print(f"[gif] {gif_path.name} ({args.frames} frames, {duration}s loop)")

    if silhouette_path:
        write_silhouette(frame_paths[0], str(silhouette_path))
        print(f"[silhouette] {silhouette_path.name} (frame 0, black-on-white)")

    if meta_path:
        write_metadata(str(meta_path), input_path.name, args.frames, args.size,
                       duration, str(mirror_path) if mirror_path else None,
                       facing=args.facing)
        print(f"[metadata] {meta_path.name}")

    # --flip-to: emit a complete horizontally-flipped sibling deliverable
    # (sheet + gif + meta) under the given NAME. This is how the right-facing
    # direction of a set is derived from the left-facing source without redrawing.
    if args.flip_to:
        flip_stem = Path(args.flip_to).stem
        flip_frame_paths = flip_frames(frame_paths, tmp_dir)

        flip_sheet_path = out_dir / f"{flip_stem}_spritesheet.png"
        stitch_frames(flip_frame_paths, args.size, str(flip_sheet_path))
        print(f"[flip-to] {flip_sheet_path.name} (flipped from {sheet_path.name})")

        if gif_path:
            flip_gif_path = out_dir / f"{flip_stem}.gif"
            write_gif(flip_frame_paths, duration, str(flip_gif_path))
            print(f"[flip-to] {flip_gif_path.name}")

        if meta_path:
            flip_meta_path = out_dir / f"{flip_stem}_spritesheet.json"
            write_metadata(str(flip_meta_path), input_path.name, args.frames, args.size,
                           duration, None, mirror_of=sheet_path.name)
            print(f"[flip-to] {flip_meta_path.name}")

    if preview_path:
        generate_preview(
            str(input_path), str(sheet_path), str(mirror_path) if mirror_path else None,
            args.frames, args.size, duration, str(preview_path),
        )
        print(f"[preview] {preview_path.name}")

    if args.keep_frames:
        frames_dir = out_dir / f"{stem}_frames"
        if frames_dir.exists():
            shutil.rmtree(frames_dir)
        shutil.move(tmp_dir, str(frames_dir))
        print(f"[frames] {frames_dir.name}/ ({args.frames} PNGs)")
    else:
        shutil.rmtree(tmp_dir)

    print("[done]")


# ── Texture pipeline (tileable surfaces) ─────────────────────────────────────
#
# Textures are a different artifact from sprites: static (or, later, looping),
# seamlessly tileable, no facing/direction, no sprite sheet. Seamlessness comes
# from edge-wrapped GEOMETRY — librsvg's feTurbulence stitchTiles is not
# pixel-perfect, so noise is only ever a diluted overlay, never load-bearing.
# This path reuses the sprite leaf helpers (check_rsvg, bake_frame,
# render_svg_to_png) and adds texture-specific composition + checks.

SEAM_THRESHOLD = 8.0  # mean edge-wrap diff (0-255) below which a tile reads as seamless.
# Flat edge-wrapped geometry measures ~0; a tuned low-opacity feTurbulence overlay
# sits ~4-8; a genuinely broken wrap measures ~20+. 8.0 cleanly separates them.

LOOP_RATIO_MAX = 2.5  # an animated texture loops cleanly when the wrap step (last->first
# frame) is no more than this multiple of the average inter-frame step; above it the loop "pops".


def parse_sizes(sizes_arg: str) -> list[int]:
    """Parse a comma-separated --sizes list into a sorted, de-duplicated list of ints."""
    sizes = []
    for tok in sizes_arg.split(","):
        tok = tok.strip()
        if not tok:
            continue
        try:
            sizes.append(int(tok))
        except ValueError:
            print(f"Error: invalid size '{tok}' in --sizes", file=sys.stderr)
            sys.exit(1)
    if not sizes:
        print("Error: --sizes produced no valid sizes", file=sys.stderr)
        sys.exit(1)
    return sorted(set(sizes))


def check_svg_filters() -> bool:
    """One-time self-test that rsvg-convert can render SVG filter primitives.

    Renders a tiny feTurbulence probe to stdout. Flat-geometry textures don't
    need this, but noise overlays do — so we warn early rather than fail silently.
    """
    probe = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8" viewBox="0 0 8 8">'
        '<filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.5" '
        'numOctaves="2" stitchTiles="stitch"/></filter>'
        '<rect width="8" height="8" filter="url(#n)"/></svg>'
    )
    try:
        result = subprocess.run(
            ["rsvg-convert", "-w", "8", "-h", "8"],
            input=probe.encode("utf-8"), capture_output=True,
        )
        return result.returncode == 0 and len(result.stdout) > 0
    except Exception:
        return False


def has_transparency(png_path: str) -> bool:
    """True if the rendered tile has any non-opaque pixel (i.e. it is a decal/overlay)."""
    img = Image.open(png_path).convert("RGBA")
    return img.split()[3].getextrema()[0] < 255


def seam_error(png_path: str) -> tuple[float, int]:
    """Measure how cleanly a tile wraps when placed edge-to-edge.

    Compares the right edge against the left edge and the bottom edge against the
    top edge, pixel-by-pixel across RGBA. Returns (mean, max) absolute channel
    difference on a 0-255 scale; 0 means a pixel-perfect seamless wrap.
    """
    img = Image.open(png_path).convert("RGBA")
    w, h = img.size
    px = img.load()
    diffs = []
    for y in range(h):  # right column meets left column when tiled horizontally
        a, b = px[w - 1, y], px[0, y]
        diffs.extend(abs(a[c] - b[c]) for c in range(4))
    for x in range(w):  # bottom row meets top row when tiled vertically
        a, b = px[x, h - 1], px[x, 0]
        diffs.extend(abs(a[c] - b[c]) for c in range(4))
    return round(sum(diffs) / len(diffs), 2), max(diffs)


def tile_grid(tile_path: str, n: int, output_path: str, has_alpha: bool = False):
    """Tile a single rendered texture into an NxN grid so seams become obvious."""
    tile = Image.open(tile_path).convert("RGBA")
    w, h = tile.size
    bg = (0, 0, 0, 0) if has_alpha else (0, 0, 0, 255)
    grid = Image.new("RGBA", (w * n, h * n), bg)
    for row in range(n):
        for col in range(n):
            grid.paste(tile, (col * w, row * h), tile if has_alpha else None)
    grid.save(output_path, "PNG")


def write_texture_metadata(output_path: str, source: str, material: str | None,
                           sizes: list[int], variants: dict, tile_check: str | None,
                           seam: tuple[float, int], has_alpha: bool, animated: bool = False,
                           frame_count: int | None = None, duration: float | None = None,
                           loop: dict | None = None, gif: str | None = None,
                           tile_check_gif: str | None = None):
    """Write a texture metadata JSON (distinct schema from the sprite sheet metadata).

    For an animated texture, `variants` maps each size to its flipbook sprite SHEET,
    and the extra fields record the frame count, duration, fps, and loop quality.
    `seamError` is always the SPATIAL (edge-wrap) error — for animated textures it is
    averaged across frames.
    """
    meta = {
        "type": "texture",
        "source": source,
        "material": material,
        "tilingMethod": "edge-wrap",
        "sizes": sizes,
        "variants": variants,
        "seamless": seam[0] <= SEAM_THRESHOLD,
        "seamError": {"mean": seam[0], "max": seam[1]},
        "hasAlpha": has_alpha,
        "surface": "decal" if has_alpha else "opaque",
        "animated": animated,
    }
    if animated:
        meta["frameCount"] = frame_count
        meta["animationDuration"] = duration
        meta["fps"] = round(frame_count / duration, 2) if (frame_count and duration) else None
        if loop is not None:
            meta["loopError"] = loop
            meta["loops"] = loop.get("ratio", 0) <= LOOP_RATIO_MAX
        if gif:
            meta["gif"] = os.path.basename(gif)
        if tile_check_gif:
            meta["tileCheckAnimated"] = os.path.basename(tile_check_gif)
    if tile_check:
        meta["tileCheck"] = os.path.basename(tile_check)
    with open(output_path, "w") as f:
        json.dump(meta, f, indent=2)


def _frame_diff(path_a: str, path_b: str) -> float:
    """Mean absolute RGBA channel difference (0-255) between two equally-sized PNGs."""
    a = Image.open(path_a).convert("RGBA")
    b = Image.open(path_b).convert("RGBA")
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 4


def temporal_loop_error(frame_paths: list[str]) -> dict:
    """Measure how cleanly an animation loops.

    Compares the wrap step (last frame -> first frame) against the average step
    between consecutive frames. A clean loop has wrap ~= avg (ratio ~1); a loop
    that doesn't return to its start has a large wrap step (ratio >> 1).
    """
    if len(frame_paths) < 2:
        return {"wrap": 0.0, "avgStep": 0.0, "ratio": 0.0}
    steps = [_frame_diff(frame_paths[i], frame_paths[i + 1]) for i in range(len(frame_paths) - 1)]
    wrap = _frame_diff(frame_paths[-1], frame_paths[0])
    avg = sum(steps) / len(steps)
    ratio = round(wrap / avg, 2) if avg > 0 else 0.0
    return {"wrap": round(wrap, 2), "avgStep": round(avg, 2), "ratio": ratio}


def write_tiled_gif(frame_paths: list[str], n: int, duration: float,
                    output_path: str, has_alpha: bool = False):
    """Tile each frame into an NxN grid and assemble a looping GIF.

    The money-shot verification for an animated texture: it shows spatial seams
    (do the copies meet cleanly?) and the temporal loop (does it pop?) at once.
    """
    frames = []
    for p in frame_paths:
        tile = Image.open(p).convert("RGBA")
        w, h = tile.size
        bg = (0, 0, 0, 0) if has_alpha else (0, 0, 0, 255)
        grid = Image.new("RGBA", (w * n, h * n), bg)
        for row in range(n):
            for col in range(n):
                grid.paste(tile, (col * w, row * h), tile if has_alpha else None)
        frames.append(grid)
    frame_ms = int(round((duration / len(frames)) * 1000))
    frames[0].save(output_path, format="GIF", save_all=True, append_images=frames[1:],
                   duration=frame_ms, loop=0, disposal=2, transparency=0)


def generate_texture_preview(svg_name: str, variants: dict, tile_check_name: str | None,
                             grid_n: int, output_path: str):
    """Generate a self-contained preview HTML: each size variant plus the seam-check grid."""
    variant_imgs = "\n".join(
        f'      <figure><img src="{name}" class="tile"/><figcaption>{size}px</figcaption></figure>'
        for size, name in variants.items()
    )
    grid_section = ""
    if tile_check_name:
        grid_section = f"""
  <div class="section">
    <h3>{grid_n}&times;{grid_n} Seam Check</h3>
    <p class="info">Look for hard lines where copies meet &mdash; there should be none.</p>
    <img src="{tile_check_name}" class="grid"/>
  </div>"""
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Texture Preview: {svg_name}</title>
  <style>
    body {{ background: #1a1a2e; color: #eee; font-family: 'Segoe UI', sans-serif; padding: 30px; }}
    h1 {{ color: #e94560; }}
    h3 {{ color: #0f3460; margin-top: 25px; }}
    .section {{ margin: 20px 0; }}
    .info {{ color: #888; font-size: 13px; }}
    .variants {{ display: flex; gap: 20px; align-items: flex-end; flex-wrap: wrap; }}
    figure {{ margin: 0; text-align: center; }}
    figcaption {{ color: #888; font-size: 12px; margin-top: 6px; }}
    .tile {{ border: 1px solid #333; image-rendering: pixelated; }}
    .grid {{ border: 2px solid #0f3460; max-width: 100%; image-rendering: pixelated; }}
  </style>
</head>
<body>
  <h1>Texture Preview: {svg_name}</h1>
  <div class="section">
    <h3>Size Variants</h3>
    <div class="variants">
{variant_imgs}
    </div>
  </div>
  {grid_section}
</body>
</html>"""
    with open(output_path, "w") as f:
        f.write(html)


def _run_texture_animated(input_path: Path, args):
    """Bake a LOOPING animated tileable texture (lava, water, scrolling glow).

    Reuses the sprite frame loop (bake_frame per t) + stitch_frames + write_gif.
    Seamless on two axes: SPACE (edge-wrapped geometry, same as static — checked
    per frame) and TIME (cyclic SMIL returning to its start — the time % dur lerp
    loops cleanly; checked via temporal_loop_error). Emits a flipbook sheet per
    size, a looping GIF, a static + an animated NxN seam-check, and metadata.
    """
    stem = Path(args.output).stem if args.output else input_path.stem
    out_dir = input_path.parent
    sizes = parse_sizes(args.sizes)

    for flag, cli in (("mirror", "--mirror"), ("flip_to", "--flip-to"),
                      ("facing", "--facing"), ("silhouette", "--silhouette")):
        if getattr(args, flag, None):
            print(f"[texture] ignoring sprite-only flag {cli} in texture mode")

    if not check_svg_filters():
        print("[texture] warning: rsvg-convert could not render an feTurbulence probe; "
              "noise-filter textures may not render. Flat-geometry textures are unaffected.",
              file=sys.stderr)

    svg_text = input_path.read_text(encoding="utf-8")
    duration = args.duration or detect_duration(svg_text)
    frames = args.frames
    if "<animate" not in svg_text:
        print("[texture] warning: --animated set but the SVG has no <animate>/<animateTransform>; "
              "every frame will be identical. Add cyclic SMIL or drop --animated.", file=sys.stderr)

    tmp_dir = tempfile.mkdtemp(prefix="spriteforge_tex_")
    largest = max(sizes)
    largest_frames = []

    variants = {}
    for size in sizes:
        frame_paths = []
        for i in range(frames):
            t = (i / frames) * duration
            baked = bake_frame(svg_text, t)
            fp = os.path.join(tmp_dir, f"{size}_{i:03d}.png")
            render_svg_to_png(baked, fp, size)
            frame_paths.append(fp)
        sheet_path = out_dir / f"{stem}_{size}_sheet.png"
        stitch_frames(frame_paths, size, str(sheet_path))
        variants[str(size)] = sheet_path.name
        if size == largest:
            largest_frames = frame_paths
    print(f"[texture] {stem} | animated | {frames} frames, {duration}s loop | "
          f"sheets at {', '.join(map(str, sizes))}px")

    has_alpha = has_transparency(largest_frames[0])

    # SPATIAL seam: average the edge-wrap error across all frames.
    per_frame = [seam_error(p) for p in largest_frames]
    spatial_mean = round(sum(m for m, _ in per_frame) / len(per_frame), 2)
    spatial_max = max(mx for _, mx in per_frame)
    sv = "seamless" if spatial_mean <= SEAM_THRESHOLD else "SEAM VISIBLE"
    print(f"[seam] spatial edge-wrap (avg over frames) mean={spatial_mean} max={spatial_max} "
          f"({sv}) | surface: {'decal/alpha' if has_alpha else 'opaque'}")
    if spatial_mean > SEAM_THRESHOLD:
        print(f"[seam] warning: frames do not wrap cleanly (mean {spatial_mean} > {SEAM_THRESHOLD}). "
              "Seamlessness must come from edge-wrapped geometry, not noise.", file=sys.stderr)

    # TEMPORAL loop: does the last frame flow back into the first?
    loop = temporal_loop_error(largest_frames)
    lv = "loops cleanly" if loop["ratio"] <= LOOP_RATIO_MAX else "LOOP POPS"
    print(f"[loop] wrap={loop['wrap']} avgStep={loop['avgStep']} ratio={loop['ratio']} ({lv})")
    if loop["ratio"] > LOOP_RATIO_MAX:
        print(f"[loop] warning: the loop jumps at the wrap (ratio {loop['ratio']} > {LOOP_RATIO_MAX}). "
              "Make the SMIL values return to their start (cyclic), e.g. translate 0 -> -tileWidth.",
              file=sys.stderr)

    gif_path = None
    if args.gif:
        gif_path = out_dir / f"{stem}.gif"
        write_gif(largest_frames, duration, str(gif_path))
        print(f"[gif] {gif_path.name} ({frames} frames, {duration}s loop)")

    tile_check_path = tile_check_gif = None
    if args.tile_grid and args.tile_grid > 0:
        n = args.tile_grid
        tile_check_path = out_dir / f"{stem}_tilecheck.png"
        tile_grid(largest_frames[0], n, str(tile_check_path), has_alpha)
        print(f"[tilecheck] {tile_check_path.name} ({n}x{n} grid of frame 0)")
        if args.gif:
            tile_check_gif = out_dir / f"{stem}_tilecheck.gif"
            write_tiled_gif(largest_frames, n, duration, str(tile_check_gif), has_alpha)
            print(f"[tilecheck] {tile_check_gif.name} ({n}x{n} animated — spatial + temporal)")

    if args.meta:
        meta_path = out_dir / f"{stem}_texture.json"
        write_texture_metadata(str(meta_path), input_path.name, args.material, sizes, variants,
                               str(tile_check_path) if tile_check_path else None,
                               (spatial_mean, spatial_max), has_alpha, animated=True,
                               frame_count=frames, duration=duration, loop=loop,
                               gif=str(gif_path) if gif_path else None,
                               tile_check_gif=str(tile_check_gif) if tile_check_gif else None)
        print(f"[metadata] {meta_path.name}")

    if args.keep_frames:
        frames_dir = out_dir / f"{stem}_frames"
        if frames_dir.exists():
            shutil.rmtree(frames_dir)
        shutil.move(tmp_dir, str(frames_dir))
        print(f"[frames] {frames_dir.name}/")
    else:
        shutil.rmtree(tmp_dir)

    print("[done]")


def run_texture_pipeline(svg_path: Path, args):
    """Render a seamlessly tileable texture from an SVG.

    Bakes one static tile, renders it at each requested power-of-two size, runs a
    numeric seam self-check, and emits an NxN seam-check grid + metadata. Parallel
    to run_pipeline (which is sprite-sheet-shaped and unaffected).
    """
    check_rsvg()

    input_path = svg_path.resolve()
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    if getattr(args, "animated", False):
        _run_texture_animated(input_path, args)
        return

    # Warn-and-ignore sprite-only flags so misuse is visible, not silent.
    for flag, cli in (("mirror", "--mirror"), ("flip_to", "--flip-to"),
                      ("facing", "--facing"), ("silhouette", "--silhouette")):
        if getattr(args, flag, None):
            print(f"[texture] ignoring sprite-only flag {cli} in texture mode")

    stem = Path(args.output).stem if args.output else input_path.stem
    out_dir = input_path.parent
    sizes = parse_sizes(args.sizes)

    if not check_svg_filters():
        print("[texture] warning: rsvg-convert could not render an feTurbulence probe; "
              "noise-filter textures may not render. Flat-geometry textures are unaffected.",
              file=sys.stderr)

    svg_text = input_path.read_text(encoding="utf-8")
    baked = bake_frame(svg_text, 0.0)

    variants = {}
    for size in sizes:
        variant_path = out_dir / f"{stem}_{size}.png"
        render_svg_to_png(baked, str(variant_path), size)
        variants[str(size)] = variant_path.name
    print(f"[texture] {stem} | rendered {len(sizes)} size(s): {', '.join(map(str, sizes))}px")

    largest = max(sizes)
    largest_path = out_dir / f"{stem}_{largest}.png"

    has_alpha = has_transparency(str(largest_path))
    seam = seam_error(str(largest_path))
    verdict = "seamless" if seam[0] <= SEAM_THRESHOLD else "SEAM VISIBLE"
    print(f"[seam] edge-wrap error mean={seam[0]} max={seam[1]} ({verdict}) | "
          f"surface: {'decal/alpha' if has_alpha else 'opaque'}")
    if seam[0] > SEAM_THRESHOLD:
        print(f"[seam] warning: tile does not wrap cleanly (mean {seam[0]} > {SEAM_THRESHOLD}). "
              "Seamlessness must come from edge-wrapped geometry, not noise.", file=sys.stderr)

    tile_check_path = None
    if args.tile_grid and args.tile_grid > 0:
        tile_check_path = out_dir / f"{stem}_tilecheck.png"
        tile_grid(str(largest_path), args.tile_grid, str(tile_check_path), has_alpha)
        print(f"[tilecheck] {tile_check_path.name} "
              f"({args.tile_grid}x{args.tile_grid} grid of the {largest}px tile)")

    if args.meta:
        meta_path = out_dir / f"{stem}_texture.json"
        write_texture_metadata(str(meta_path), input_path.name, args.material, sizes, variants,
                               str(tile_check_path) if tile_check_path else None, seam, has_alpha)
        print(f"[metadata] {meta_path.name}")

    if args.preview:
        preview_path = out_dir / f"{stem}_texture_preview.html"
        generate_texture_preview(input_path.name, variants,
                                 tile_check_path.name if tile_check_path else None,
                                 args.tile_grid, str(preview_path))
        print(f"[preview] {preview_path.name}")

    print("[done]")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert animated SVGs to PNG sprite sheets.",
        epilog=textwrap.dedent("""\
            examples:
              %(prog)s hero_walk_left.svg
              %(prog)s hero_walk_left.svg --frames 6 --size 128
              %(prog)s hero_walk_left.svg --preview --keep-frames
              %(prog)s brick_wall_texture.svg --tileable
              %(prog)s brick_wall_texture.svg --tileable --sizes 128,256 --material brick
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("svg", help="path to an animated SVG file")
    parser.add_argument("--frames", type=int, default=8, help="number of frames (default: 8)")
    parser.add_argument("--size", type=int, default=64, help="frame size in px (default: 64)")
    parser.add_argument("--output", help="output PNG path (default: auto-derived)")
    parser.add_argument("--mirror", action=argparse.BooleanOptionalAction, default=False, help="also emit a horizontally-flipped <stem>_spritesheet_mirror.png (default: off)")
    parser.add_argument("--flip-to", dest="flip_to", metavar="NAME", help="emit a complete horizontally-flipped sibling deliverable (sheet + gif + meta) named NAME_*. Use for the right-facing direction of a set, e.g. --flip-to hero_walk_right")
    parser.add_argument("--facing", help="record this facing label in the metadata (e.g. left, down, up, downleft)")
    parser.add_argument("--meta", action=argparse.BooleanOptionalAction, default=True, help="generate JSON metadata file (default: on)")
    parser.add_argument("--keep-frames", action="store_true", help="keep individual frame PNGs")
    parser.add_argument("--duration", type=float, help="override animation duration (seconds)")
    parser.add_argument("--preview", action=argparse.BooleanOptionalAction, default=False, help="generate preview HTML (default: off)")
    parser.add_argument("--gif", action=argparse.BooleanOptionalAction, default=True, help="generate animated GIF (default: on)")
    parser.add_argument("--silhouette", action=argparse.BooleanOptionalAction, default=False, help="generate a black-on-white silhouette of frame 0 for readability checks (default: off)")
    # Texture mode — render a seamlessly tiling surface texture instead of a sprite sheet
    parser.add_argument("--tileable", action="store_true", help="texture mode: render a seamlessly tiling surface texture (no sprite sheet, no facing)")
    parser.add_argument("--sizes", default="64,128,256", help="texture mode: comma-separated power-of-two sizes to emit (default: 64,128,256). Supersedes --size")
    parser.add_argument("--tile-grid", dest="tile_grid", type=int, default=3, metavar="N", help="texture mode: emit an NxN tiled seam-check PNG (default: 3, 0 disables)")
    parser.add_argument("--material", help="texture mode: material label recorded in metadata (e.g. brick, stone, metal)")
    parser.add_argument("--animated", action="store_true", help="texture mode: bake a looping animated texture (flipbook sheet per size + GIF + animated seam-check) from the SVG's cyclic SMIL")
    args = parser.parse_args()

    svg_path = Path(args.svg)
    if not svg_path.exists():
        print(f"Error: {args.svg} not found", file=sys.stderr)
        sys.exit(1)

    if args.tileable:
        run_texture_pipeline(svg_path, args)
    else:
        run_pipeline(svg_path, args)


if __name__ == "__main__":
    main()
