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
    from PIL import Image, ImageOps
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
                parent.set("transform", f"{transform_type}({val})")
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
                   duration: float, mirror_path: str | None):
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

    if meta_path:
        write_metadata(str(meta_path), input_path.name, args.frames, args.size,
                       duration, str(mirror_path) if mirror_path else None)
        print(f"[metadata] {meta_path.name}")

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


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert animated SVGs to PNG sprite sheets.",
        epilog=textwrap.dedent("""\
            examples:
              %(prog)s hero_walk_left.svg
              %(prog)s hero_walk_left.svg --frames 6 --size 128
              %(prog)s hero_walk_left.svg --preview --keep-frames
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("svg", help="path to an animated SVG file")
    parser.add_argument("--frames", type=int, default=8, help="number of frames (default: 8)")
    parser.add_argument("--size", type=int, default=64, help="frame size in px (default: 64)")
    parser.add_argument("--output", help="output PNG path (default: auto-derived)")
    parser.add_argument("--mirror", action=argparse.BooleanOptionalAction, default=True, help="generate a flipped sprite sheet (default: on)")
    parser.add_argument("--meta", action=argparse.BooleanOptionalAction, default=True, help="generate JSON metadata file (default: on)")
    parser.add_argument("--keep-frames", action="store_true", help="keep individual frame PNGs")
    parser.add_argument("--duration", type=float, help="override animation duration (seconds)")
    parser.add_argument("--preview", action=argparse.BooleanOptionalAction, default=False, help="generate preview HTML (default: off)")
    parser.add_argument("--gif", action=argparse.BooleanOptionalAction, default=False, help="generate animated GIF (default: off)")
    args = parser.parse_args()

    svg_path = Path(args.svg)
    if not svg_path.exists():
        print(f"Error: {args.svg} not found", file=sys.stderr)
        sys.exit(1)

    run_pipeline(svg_path, args)


if __name__ == "__main__":
    main()
