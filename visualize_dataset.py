"""Creates a browsable report showing how build_dataset.py tiles labeled images."""
import argparse
import html
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from build_dataset import tile_boxes, tiles
from common import pair_labels, read_yolo


def draw_box(draw, box, color, width=2):
    draw.rectangle(tuple(round(v) for v in box), outline=color, width=width)


def make_overview(image, boxes, split_x, tile, stride, val_frac, destination):
    width, height = image.size
    boundary = int(width * (1 - val_frac))
    coverage = np.zeros((height, width), dtype=np.uint8)
    tile_rects = []
    for split, x_offset, part_width, color in (
        ("train", 0, boundary, (40, 170, 255)),
        ("val", boundary, width - boundary, (255, 170, 40)),
    ):
        for tx, ty in tiles(part_width, height, tile, stride):
            tw, th = min(tile, part_width), min(tile, height)
            x0, y0 = x_offset + tx, ty
            x1, y1 = x0 + tw, y0 + th
            coverage[y0:y1, x0:x1] += 1
            tile_rects.append(((x0, y0, x1 - 1, y1 - 1), color))

    overlap = coverage > 1
    overlay_pixels = np.zeros((height, width, 4), dtype=np.uint8)
    overlay_pixels[overlap] = (220, 0, 170, 115)
    overlap_overlay = Image.fromarray(overlay_pixels, mode="RGBA")
    image = Image.alpha_composite(image.convert("RGBA"), overlap_overlay).convert("RGB")
    draw = ImageDraw.Draw(image)

    for box in boxes:
        draw_box(draw, box, (40, 255, 80), 2)
    for rect, color in tile_rects:
        draw.rectangle(rect, outline=color, width=2)

    draw.line((split_x, 0, split_x, height - 1), fill=(255, 255, 255), width=3)
    image.save(destination)


def tile_overlap_mask(tile_coords, tx, ty, tw, th):
    overlap = np.zeros((th, tw), dtype=bool)
    for other_x, other_y in tile_coords:
        if (other_x, other_y) == (tx, ty):
            continue
        x0, y0 = max(tx, other_x), max(ty, other_y)
        x1, y1 = min(tx + tw, other_x + tw), min(ty + th, other_y + th)
        if x0 < x1 and y0 < y1:
            overlap[y0 - ty:y1 - ty, x0 - tx:x1 - tx] = True
    return overlap


def make_tile_preview(tile_path, label_path, expected_kept, dropped, overlap, destination):
    with Image.open(tile_path) as source:
        image = source.convert("RGB")
    overlay_pixels = np.zeros((image.height, image.width, 4), dtype=np.uint8)
    overlay_pixels[overlap] = (220, 0, 170, 115)
    overlap_overlay = Image.fromarray(overlay_pixels, mode="RGBA")
    image = Image.alpha_composite(image.convert("RGBA"), overlap_overlay).convert("RGB")
    draw = ImageDraw.Draw(image)
    actual = read_yolo(label_path, *image.size)

    for box in dropped:
        draw_box(draw, box, (255, 140, 0), 2)
    for box in actual:
        draw_box(draw, box, (40, 255, 80), 2)
    draw.rectangle((0, 0, image.width - 1, image.height - 1), outline=(0, 255, 255), width=3)

    image.save(destination)
    matches = len(actual) == len(expected_kept)
    if matches:
        for actual_box, expected_box in zip(actual, expected_kept):
            if any(abs(a - e) > 0.002 for a, e in zip(actual_box, expected_box)):
                matches = False
                break
    return len(actual), matches


def density_rgb(density, scale):
    intensity = np.clip(density / scale, 0, 1)
    red = np.clip(2 * intensity, 0, 1)
    green = np.clip(2 * intensity - 0.5, 0, 1)
    blue = np.clip(1 - 2 * intensity, 0, 1)
    return (np.stack((red, green, blue), axis=-1) * 255).astype(np.uint8)


def make_processed_preview(image_path, density_path, scale, destination):
    with Image.open(image_path) as source:
        image = source.convert("RGB")
    density = np.load(density_path, allow_pickle=False)
    if density.ndim != 2 or density.shape != (image.height, image.width):
        raise ValueError(
            f"Density map {density_path} has shape {density.shape}; "
            f"expected {(image.height, image.width)} to match its image."
        )
    if not np.isfinite(density).all():
        raise ValueError(f"Density map contains non-finite values: {density_path}")

    heatmap = Image.fromarray(density_rgb(density, scale), mode="RGB")
    preview = Image.new("RGB", (image.width * 2, image.height), (255, 255, 255))
    preview.paste(image, (0, 0))
    preview.paste(heatmap, (image.width, 0))
    preview.save(destination)
    return float(density.sum()), float(density.max(initial=0)), int(np.count_nonzero(density))


def build_processed_section(processed_dir, out_dir):
    image_dir = processed_dir / "images"
    density_dir = processed_dir / "density_maps"
    if not image_dir.is_dir() or not density_dir.is_dir():
        raise FileNotFoundError(
            f"{processed_dir} must contain images/ and density_maps/ directories."
        )

    image_paths = sorted(image_dir.glob("*.png"))
    if not image_paths:
        raise ValueError(f"No processed image tiles found in {image_dir}")

    paired = []
    max_density = 0.0
    for image_path in image_paths:
        density_path = density_dir / f"{image_path.stem}.npy"
        if not density_path.is_file():
            raise FileNotFoundError(f"Missing density map for {image_path.name}: {density_path}")
        density = np.load(density_path, allow_pickle=False)
        if density.ndim != 2 or not np.isfinite(density).all():
            raise ValueError(f"Invalid density map in {density_path}")
        max_density = max(max_density, float(density.max(initial=0)))
        paired.append((image_path, density_path))

    preview_dir = out_dir / "processed_tiles"
    preview_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    total_density = 0.0
    total_nonzero = 0
    scale = max_density if max_density > 0 else 1.0

    for image_path, density_path in paired:
        preview_name = f"{image_path.stem}_pair.png"
        density_sum, density_max, nonzero = make_processed_preview(
            image_path, density_path, scale, preview_dir / preview_name
        )
        total_density += density_sum
        total_nonzero += nonzero
        rows.append(
            f'<article class="tile-card">'
            f'<h3>{html.escape(image_path.stem)}</h3>'
            f'<p>Density sum: {density_sum:.3f}; maximum: {density_max:.5f}; '
            f'nonzero pixels: {nonzero}.</p>'
            f'<img loading="lazy" src="processed_tiles/{html.escape(preview_name, quote=True)}" '
            f'alt="{html.escape(image_path.stem)} image and density-map pair">'
            f'</article>'
        )

    return (
        f'<section class="source">'
        f'<h2>Point-annotation density-map dataset</h2>'
        f'<p>{len(paired)} paired tiles from {html.escape(str(processed_dir))}. '
        f'Each preview places the processed image tile on the left and its matching '
        f'Gaussian density map on the right. Density colors use one shared scale '
        f'across all tiles, so brightness is comparable between tiles; black indicates zero.</p>'
        f'<p>Total density sum: {total_density:.3f}; nonzero density pixels: {total_nonzero}.</p>'
        f'<div class="tile-grid">{"".join(rows)}</div>'
        f'</section>'
    )


def build_report(images_dir, labels_dir, dataset_dir, out_dir, tile, stride, val_frac,
                 processed_dir=None):
    pairs = pair_labels(images_dir, labels_dir)
    if not pairs:
        raise ValueError(f"No matching image/label pairs found in {images_dir} and {labels_dir}")

    overview_dir = out_dir / "overview"
    tile_preview_dir = out_dir / "tiles"
    overview_dir.mkdir(parents=True, exist_ok=True)
    tile_preview_dir.mkdir(parents=True, exist_ok=True)

    source_sections = []
    total_tiles = total_labels = total_dropped = 0
    boundary_fraction = 1 - val_frac

    for image_path, label_path in pairs:
        with Image.open(image_path) as source:
            image = source.convert("RGB")
        width, height = image.size
        boxes = read_yolo(label_path, width, height)
        split_x = int(width * boundary_fraction)
        overview_name = f"{image_path.stem}_overview.png"
        make_overview(
            image.copy(), boxes, split_x, tile, stride, val_frac,
            overview_dir / overview_name,
        )

        rows = []
        split_counts = {}
        for split, x_offset, part_width in (
            ("train", 0, split_x),
            ("val", split_x, width - split_x),
        ):
            tile_coords = tiles(part_width, height, tile, stride)
            tile_label_count = tile_dropped_count = 0
            split_counts[split] = len(tile_coords)

            for tx, ty in tile_coords:
                tw, th = min(tile, part_width), min(tile, height)
                name = f"{image_path.stem}_{split}_x{tx}_y{ty}"
                tile_path = dataset_dir / "images" / split / f"{name}.png"
                tile_label_path = dataset_dir / "labels" / split / f"{name}.txt"
                if not tile_path.is_file() or not tile_label_path.is_file():
                    missing = tile_path if not tile_path.is_file() else tile_label_path
                    raise FileNotFoundError(
                        f"Expected build output not found: {missing}. "
                        "Rebuild the dataset or pass matching --tile, --stride, and --val-frac values."
                    )

                kept, dropped = tile_boxes(boxes, tx, ty, x_offset, tw, th)
                overlap = tile_overlap_mask(tile_coords, tx, ty, tw, th)
                preview_name = f"{name}.png"
                actual_count, matches = make_tile_preview(
                    tile_path, tile_label_path, kept, dropped,
                    overlap,
                    tile_preview_dir / preview_name,
                )
                tile_label_count += actual_count
                tile_dropped_count += len(dropped)
                status = "matches expected labels" if matches else "label mismatch"
                rows.append(
                    f'<article class="tile-card">'
                    f'<h3>{html.escape(split)} tile at x={tx}, y={ty}</h3>'
                    f'<p>{actual_count} saved labels; {len(dropped)} clipped boxes dropped '
                    f'by the 40% rule; {status}.</p>'
                    f'<p><span class="overlap-key">Purple: pixels shared with another tile</span>; '
                    f'<span class="border-key">cyan frame: this tile\'s bounds</span>.</p>'
                    f'<img loading="lazy" src="tiles/{html.escape(preview_name, quote=True)}" '
                    f'alt="{html.escape(name)} with label boxes">'
                    f'</article>'
                )

            split_counts[f"{split}_labels"] = tile_label_count
            split_counts[f"{split}_dropped"] = tile_dropped_count

        total_tiles += split_counts["train"] + split_counts["val"]
        total_labels += split_counts["train_labels"] + split_counts["val_labels"]
        total_dropped += split_counts["train_dropped"] + split_counts["val_dropped"]
        nominal_overlap = max(0, tile - stride)
        summary = (
            f'<section class="source">'
            f'<h2>{html.escape(image_path.name)}</h2>'
            f'<p>{width} × {height} px; split at x={split_x} '
            f'({boundary_fraction:.0%} train / {val_frac:.0%} validation); '
            f'{tile} px tiles, {stride} px nominal stride, '
            f'{nominal_overlap} px nominal overlap. Edge-aligned tiles may overlap more.</p>'
            f'<div class="overview"><img src="overview/{html.escape(overview_name, quote=True)}" '
            f'alt="Tile locations and labels on source echogram">'
            f'<p><span class="train-key">Blue: train tile grid</span> · '
            f'<span class="val-key">Orange: validation tile grid</span> · '
            f'<span class="label-key">Green: source labels</span> · '
            f'Purple shading: source pixels covered by multiple tiles · '
            f'White: split boundary</p></div>'
            f'<p>Tiles: train {split_counts["train"]} '
            f'({split_counts["train_labels"]} saved labels), validation {split_counts["val"]} '
            f'({split_counts["val_labels"]} saved labels). '
            f'Sliver-filtered tile-boxes: '
            f'{split_counts["train_dropped"]} train, {split_counts["val_dropped"]} validation. '
            f'Overlapping tiles can contain the same fish more than once.</p>'
            f'<div class="tile-grid">{"".join(rows)}</div>'
            f'</section>'
        )
        source_sections.append(summary)

    processed_section = ""
    if processed_dir is not None:
        processed_section = build_processed_section(processed_dir, out_dir)

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dataset build visualization</title>
<style>
body {{ font: 16px/1.5 system-ui, sans-serif; margin: 0 auto; max-width: 1500px; padding: 1.5rem; color: #202124; }}
h1, h2, h3 {{ line-height: 1.2; }}
.source {{ border-top: 2px solid #bbb; margin-top: 2rem; padding-top: 1rem; }}
.overview img {{ background: #222; max-width: 100%; height: auto; }}
.train-key {{ color: #0876bd; }} .val-key {{ color: #bd6b00; }} .label-key {{ color: #078b20; }}
.overlap-key {{ color: #ad0087; }} .border-key {{ color: #008b8b; }}
.tile-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 1rem; }}
.tile-card {{ border: 1px solid #ccc; border-radius: 6px; padding: .75rem; min-width: 0; }}
.tile-card h3 {{ font-size: 1rem; }}
.tile-card img {{ width: 100%; height: auto; image-rendering: pixelated; }}
</style>
</head>
<body>
<h1>Dataset build visualization</h1>
<p>Tiles: {total_tiles}; saved tile labels: {total_labels}; sliver-filtered box fragments: {total_dropped}.</p>
<p>Tile previews show saved labels in green and intersecting fragments removed by the 40% area rule in orange.
The source overview shows the tile grid over the original image, labels, and train/validation boundary.
“Label mismatch” flags a tile whose saved labels differ from the expected clipping result.</p>
{"".join(source_sections)}
{processed_section}
</body>
</html>
"""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(page, encoding="utf-8")
    return out_dir / "index.html"


def main():
    parser = argparse.ArgumentParser(
        description="Visualize the tiles and labels produced by build_dataset.py."
    )
    parser.add_argument("images", help="Original echogram image folder")
    parser.add_argument("labels", help="YOLO labels folder for the original images")
    parser.add_argument("dataset", help="Output folder previously created by build_dataset.py")
    parser.add_argument("--out", default="dataset_visualization", help="Report output folder")
    parser.add_argument("--tile", type=int, default=320)
    parser.add_argument("--stride", type=int, default=160)
    parser.add_argument("--val-frac", type=float, default=0.3)
    parser.add_argument(
        "--processed-dir",
        help="Also include process.py output (defaults to ./processed_dataset when present)",
    )
    args = parser.parse_args()

    if args.tile <= 0 or args.stride <= 0 or args.stride > args.tile:
        parser.error("--tile and --stride must be positive, and --stride cannot exceed --tile")
    if not 0 < args.val_frac < 1:
        parser.error("--val-frac must be between 0 and 1")

    processed_dir = Path(args.processed_dir) if args.processed_dir else None
    if processed_dir is None and Path("processed_dataset").is_dir():
        processed_dir = Path("processed_dataset")

    report_path = build_report(
        Path(args.images), Path(args.labels), Path(args.dataset), Path(args.out),
        args.tile, args.stride, args.val_frac, processed_dir,
    )
    print(f"Wrote {report_path.resolve()}")


if __name__ == "__main__":
    main()
