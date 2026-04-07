#!/usr/bin/env python3
"""
CB2 Orientation Fix — Post-processing for AI-generated product photos.

When FLUX generates images of the CB2 wearable remote on someone's arm,
~50-60% of the time the symbols are flipped (facing camera instead of wearer).
This script detects the CB2 with SAM 3, rotates just the device 180°,
and composites it back with feathered edges.

Usage:
    # Single image (URL or local file)
    python fix-orientation.py https://example.com/image.jpg

    # Multiple images (batch mode)
    python fix-orientation.py image1.jpg https://example.com/image2.jpg image3.png

    # Local files
    python fix-orientation.py /path/to/photo.jpg

Dependencies: Pillow, requests
"""

import sys
import os
import time
import argparse
from typing import Optional
from pathlib import Path
from io import BytesIO

import requests
from PIL import Image, ImageFilter

# ── Config ──────────────────────────────────────────────────────────────────

FAL_API_KEY = "abd109db-5b32-4be9-8e80-55d543ef21b5:25db06d5650ad2d12f2f1d32dcca5099"
SAM3_ENDPOINT = "https://queue.fal.run/fal-ai/sam-3/image"
SAM3_PROMPTS = [
    "black remote control on wrist",
    "rectangular wearable on arm strap",
    "wearable remote control on forearm",
]

FEATHER_RADIUS = 3       # px of Gaussian blur on alpha for compositing
MIN_DEVICE_PX = 20       # skip if detected region smaller than this
MAX_DEVICE_RATIO = 0.50  # skip if detected region > 50% of image area
API_TIMEOUT = 60         # seconds for fal.ai requests
POLL_INTERVAL = 1        # seconds between status polls


# ── Helpers ─────────────────────────────────────────────────────────────────

def load_image(source: str) -> Image.Image:
    """Load image from URL or local file path."""
    if source.startswith("http://") or source.startswith("https://"):
        print(f"  Downloading image from URL...")
        resp = requests.get(
            source,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
            timeout=API_TIMEOUT,
        )
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content))
    else:
        path = Path(source).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return Image.open(str(path))


def upload_image_for_api(source: str) -> str:
    """Return a URL suitable for the SAM 3 API.

    If source is already a URL, return it directly.
    If it's a local file, upload to fal.ai storage first.
    """
    if source.startswith("http://") or source.startswith("https://"):
        return source

    # For local files, upload to fal.ai storage
    path = Path(source).expanduser().resolve()
    print(f"  Uploading local file to fal.ai storage...")

    # Read file and determine content type
    ext = path.suffix.lower()
    content_types = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
    }
    content_type = content_types.get(ext, "image/jpeg")

    # Step 1: Initiate upload to get signed URL
    init_resp = requests.post(
        "https://rest.alpha.fal.ai/storage/upload/initiate",
        headers={"Authorization": f"Key {FAL_API_KEY}"},
        json={"content_type": content_type, "file_name": path.name},
        timeout=API_TIMEOUT,
    )
    init_resp.raise_for_status()
    init_data = init_resp.json()
    file_url = init_data["file_url"]
    upload_url = init_data["upload_url"]

    # Step 2: PUT file content to the signed upload URL
    with open(str(path), "rb") as f:
        file_data = f.read()
    put_resp = requests.put(
        upload_url,
        headers={"Content-Type": content_type},
        data=file_data,
        timeout=API_TIMEOUT,
    )
    put_resp.raise_for_status()

    print(f"  Uploaded: {file_url[:80]}...")
    return file_url


def _call_sam3_single(image_url: str, prompt: str, headers: dict) -> dict:
    """Submit a single SAM 3 request and poll for the result."""
    payload = {
        "image_url": image_url,
        "prompt": prompt,
        "apply_mask": True,
    }

    # Submit to queue
    submit_resp = requests.post(
        SAM3_ENDPOINT,
        headers=headers,
        json=payload,
        timeout=API_TIMEOUT,
    )
    submit_resp.raise_for_status()
    queue_data = submit_resp.json()

    # Check if we got a direct result (non-queued response)
    if "image" in queue_data and queue_data["image"] is not None:
        return queue_data

    # Otherwise poll for result
    request_id = queue_data.get("request_id")
    status_url = queue_data.get("status_url")
    response_url = queue_data.get("response_url")

    if not request_id:
        raise RuntimeError(f"No request_id in queue response: {queue_data}")

    print(f"    Queued (request_id: {request_id}). Polling...")

    # Poll status
    start_time = time.time()
    while time.time() - start_time < API_TIMEOUT:
        time.sleep(POLL_INTERVAL)

        poll_url = status_url or f"https://queue.fal.run/fal-ai/sam-3/image/requests/{request_id}/status"
        status_resp = requests.get(poll_url, headers=headers, timeout=API_TIMEOUT)
        status_resp.raise_for_status()
        status_data = status_resp.json()

        status = status_data.get("status", "")
        if status == "COMPLETED":
            result_url = response_url or f"https://queue.fal.run/fal-ai/sam-3/image/requests/{request_id}"
            result_resp = requests.get(result_url, headers=headers, timeout=API_TIMEOUT)
            result_resp.raise_for_status()
            return result_resp.json()
        elif status in ("FAILED", "CANCELLED"):
            error = status_data.get("error", "Unknown error")
            raise RuntimeError(f"SAM 3 request failed: {error}")
        else:
            elapsed = int(time.time() - start_time)
            print(f"    Status: {status} ({elapsed}s elapsed)...")

    raise TimeoutError(f"SAM 3 request timed out after {API_TIMEOUT}s")


def call_sam3(image_url: str) -> dict:
    """Call SAM 3 on fal.ai to segment the CB2 device.

    Tries multiple prompts in order until one returns a valid detection.
    Returns the full API response dict.
    """
    headers = {
        "Authorization": f"Key {FAL_API_KEY}",
        "Content-Type": "application/json",
    }

    for i, prompt in enumerate(SAM3_PROMPTS):
        print(f"  Trying prompt {i+1}/{len(SAM3_PROMPTS)}: \"{prompt}\"")
        try:
            result = _call_sam3_single(image_url, prompt, headers)

            # Check if we got a valid detection
            masks = result.get("masks", [])
            image_data = result.get("image")
            if image_data is not None and len(masks) > 0:
                print(f"  Detection successful with prompt: \"{prompt}\"")
                return result
            else:
                print(f"    No detection with this prompt (masks={len(masks)}, image={'present' if image_data else 'null'})")
        except Exception as e:
            print(f"    Error with this prompt: {e}")

    raise RuntimeError(f"SAM 3 could not detect the CB2 device with any of {len(SAM3_PROMPTS)} prompts")


def find_mask_bbox(mask_img: Image.Image) -> tuple:
    """Find the bounding box of non-transparent pixels in an RGBA image.

    Returns (left, top, right, bottom) or None if no opaque pixels found.
    """
    # Convert to RGBA if needed
    if mask_img.mode != "RGBA":
        mask_img = mask_img.convert("RGBA")

    # Get alpha channel and find bounding box
    alpha = mask_img.split()[3]
    bbox = alpha.getbbox()
    return bbox


def validate_detection(bbox: tuple, image_size: tuple) -> Optional[str]:
    """Validate that the detected region is reasonable.

    Returns None if valid, or an error message string if invalid.
    """
    if bbox is None:
        return "SAM 3 did not detect any object (no non-transparent pixels)"

    left, top, right, bottom = bbox
    width = right - left
    height = bottom - top
    img_w, img_h = image_size

    if width < MIN_DEVICE_PX or height < MIN_DEVICE_PX:
        return f"Detected region too small: {width}x{height}px (min: {MIN_DEVICE_PX}px)"

    area_ratio = (width * height) / (img_w * img_h)
    if area_ratio > MAX_DEVICE_RATIO:
        pct = area_ratio * 100
        return f"Detected region too large: {width}x{height}px = {pct:.1f}% of image (max: {MAX_DEVICE_RATIO*100:.0f}%)"

    return None


def fix_orientation(source: str, output_path: str = None, feather: int = None) -> str:
    """Main pipeline: detect CB2, rotate 180°, composite back.

    Args:
        source: URL or local file path to the image
        output_path: Optional output path. If None, auto-generates as <name>_fixed.<ext>
        feather: Feather radius in pixels (default: FEATHER_RADIUS)

    Returns:
        Path to the saved output file.
    """
    if feather is None:
        feather = FEATHER_RADIUS
    print(f"\n{'='*60}")
    print(f"Processing: {source}")
    print(f"{'='*60}")

    # ── Step 1: Load the original image ──
    print("\n[Step 1] Loading original image...")
    original = load_image(source)
    original = original.convert("RGB")
    print(f"  Image size: {original.size[0]}x{original.size[1]}")

    # ── Step 2: Call SAM 3 to detect the CB2 ──
    print("\n[Step 2] Detecting CB2 with SAM 3...")
    image_url = upload_image_for_api(source)
    sam_result = call_sam3(image_url)

    # Download the masked RGBA image
    masked_url = sam_result.get("image", {}).get("url")
    if not masked_url:
        raise RuntimeError(f"No masked image URL in SAM 3 response: {list(sam_result.keys())}")

    print(f"  Downloading masked image...")
    mask_resp = requests.get(masked_url, timeout=API_TIMEOUT)
    mask_resp.raise_for_status()
    masked_img = Image.open(BytesIO(mask_resp.content)).convert("RGBA")
    print(f"  Masked image size: {masked_img.size[0]}x{masked_img.size[1]}")

    # ── Step 3: Find the bounding box of the detected device ──
    print("\n[Step 3] Finding device bounding box...")
    bbox = find_mask_bbox(masked_img)

    error = validate_detection(bbox, original.size)
    if error:
        raise ValueError(error)

    left, top, right, bottom = bbox
    width = right - left
    height = bottom - top
    print(f"  Device bbox: ({left}, {top}) to ({right}, {bottom}) = {width}x{height}px")

    # ── Step 4: Extract device region from ORIGINAL, rotate 180° ──
    print("\n[Step 4] Extracting and rotating device region...")

    # Crop the device region from the original image
    device_crop = original.crop(bbox)

    # Also crop the mask's alpha channel for the same region
    mask_alpha = masked_img.split()[3].crop(bbox)

    # Rotate the device crop 180°
    device_rotated = device_crop.rotate(180)

    print(f"  Rotated {width}x{height}px region by 180 degrees")

    # ── Step 5: Composite with feathered mask ──
    print("\n[Step 5] Compositing with feathered mask...")

    # Create feathered mask: blur the alpha channel
    feathered_mask = mask_alpha.filter(ImageFilter.GaussianBlur(radius=feather))

    # Create the output image (copy of original)
    result = original.copy()

    # Paste the rotated device using the feathered mask
    result.paste(device_rotated, (left, top), feathered_mask)

    print(f"  Composited with {feather}px feathered edges")

    # ── Step 6: Save result ──
    print("\n[Step 6] Saving result...")

    if output_path is None:
        # Auto-generate output path
        if source.startswith("http://") or source.startswith("https://"):
            # Extract filename from URL
            url_path = source.split("?")[0].split("#")[0]
            fname = url_path.split("/")[-1]
            if not fname or "." not in fname:
                fname = "image.jpg"
            stem = Path(fname).stem
            ext = Path(fname).suffix or ".jpg"
            output_path = f"{stem}_fixed{ext}"
        else:
            p = Path(source).expanduser().resolve()
            output_path = str(p.parent / f"{p.stem}_fixed{p.suffix}")

    # Save as JPEG
    if output_path.lower().endswith(".png"):
        result.save(output_path, "PNG")
    else:
        result.save(output_path, "JPEG", quality=95)

    print(f"  Saved: {output_path}")
    return output_path


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Fix 180° orientation flip on CB2 wearable remote in AI-generated photos.",
        epilog="Examples:\n"
               "  python fix-orientation.py image.jpg\n"
               "  python fix-orientation.py https://example.com/photo.jpg\n"
               "  python fix-orientation.py img1.jpg img2.jpg img3.jpg\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "images",
        nargs="+",
        help="Image URLs or local file paths to process",
    )
    parser.add_argument(
        "--feather",
        type=int,
        default=FEATHER_RADIUS,
        help=f"Feather radius in pixels (default: {FEATHER_RADIUS})",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save output files (default: same as input or current dir)",
    )

    args = parser.parse_args()

    feather = args.feather

    # Process all images
    results = {"success": [], "failed": []}

    for source in args.images:
        try:
            # Determine output path
            output_path = None
            if args.output_dir:
                os.makedirs(args.output_dir, exist_ok=True)
                if source.startswith("http://") or source.startswith("https://"):
                    url_path = source.split("?")[0].split("#")[0]
                    fname = url_path.split("/")[-1]
                    if not fname or "." not in fname:
                        fname = "image.jpg"
                    stem = Path(fname).stem
                    ext = Path(fname).suffix or ".jpg"
                    output_path = os.path.join(args.output_dir, f"{stem}_fixed{ext}")
                else:
                    p = Path(source)
                    output_path = os.path.join(args.output_dir, f"{p.stem}_fixed{p.suffix}")

            saved = fix_orientation(source, output_path, feather=feather)
            results["success"].append((source, saved))

        except Exception as e:
            print(f"\n  ERROR: {e}")
            results["failed"].append((source, str(e)))

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"BATCH SUMMARY")
    print(f"{'='*60}")
    print(f"  Total:     {len(args.images)}")
    print(f"  Succeeded: {len(results['success'])}")
    print(f"  Failed:    {len(results['failed'])}")

    if results["success"]:
        print(f"\n  Successful:")
        for src, out in results["success"]:
            src_short = src if len(src) < 50 else f"...{src[-47:]}"
            print(f"    {src_short}")
            print(f"      -> {out}")

    if results["failed"]:
        print(f"\n  Failed:")
        for src, err in results["failed"]:
            src_short = src if len(src) < 50 else f"...{src[-47:]}"
            print(f"    {src_short}")
            print(f"      Error: {err}")

    # Exit with error code if any failed
    if results["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
