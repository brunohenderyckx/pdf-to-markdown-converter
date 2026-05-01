#!/usr/bin/env python3
"""
Convert PDF files to Markdown using docling or marker-pdf.

Usage:
    python convert.py <file.pdf>                   # single file
    python convert.py pdfs/                        # all unconverted in a directory
    python convert.py --all                        # all unconverted in default pdfs/ folder
    python convert.py --backend marker <path>      # use marker-pdf instead of docling
    python convert.py --force                      # reconvert already-converted files
    python convert.py --list                       # list unconverted PDFs
    python convert.py --batch                      # docling only: one call for whole dir (fastest on Apple Silicon)
"""

import argparse
import platform
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent.resolve()
PDFS_DIR = SCRIPT_DIR / "pdfs"
MARKDOWN_DIR = SCRIPT_DIR / "markdown"


def detect_device() -> tuple[str, int, int]:
    """Return (device, threads, batch_size) tuned for the current platform."""
    if platform.system() == "Darwin":
        return "mps", 8, 8
    return "auto", 4, 4


def is_converted(pdf_path: Path) -> bool:
    """Return True if a markdown output already exists for this PDF."""
    stem = pdf_path.stem
    return (MARKDOWN_DIR / f"{stem}.md").exists() or (MARKDOWN_DIR / stem).exists()


def convert_with_marker(pdf_path: Path) -> bool:
    """Convert a single PDF using marker-pdf (marker_single CLI)."""
    try:
        result = subprocess.run(
            ["marker_single", str(pdf_path), "--output_dir", str(MARKDOWN_DIR)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        return True
    except FileNotFoundError:
        print("Error: marker_single not found. Install with: pip install marker-pdf")
        return False


def convert_with_docling(pdf_path: Path, device: str, threads: int, batch_size: int) -> bool:
    """Convert a single PDF using docling CLI."""
    try:
        result = subprocess.run(
            [
                "docling", str(pdf_path),
                "--output", str(MARKDOWN_DIR),
                "--to", "md",
                "--device", device,
                "--num-threads", str(threads),
                "--page-batch-size", str(batch_size),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        return True
    except FileNotFoundError:
        print("Error: docling not found. Install with: pip install docling")
        return False


def convert_with_docling_batch(pdf_dir: Path, device: str, threads: int, batch_size: int) -> bool:
    """Convert an entire directory in one docling call (fastest on Apple Silicon)."""
    try:
        result = subprocess.run(
            [
                "docling", str(pdf_dir),
                "--output", str(MARKDOWN_DIR),
                "--to", "md",
                "--device", device,
                "--num-threads", str(threads),
                "--page-batch-size", str(batch_size),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        return True
    except FileNotFoundError:
        print("Error: docling not found. Install with: pip install docling")
        return False


def convert_pdf(pdf_path: Path, backend: str, device: str, threads: int, batch_size: int) -> bool:
    """Convert a single PDF with the chosen backend."""
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        return False
    if pdf_path.suffix.lower() != ".pdf":
        print(f"Error: Not a PDF file: {pdf_path}")
        return False

    print(f"Converting: {pdf_path.name}  [{backend}]")
    if backend == "marker":
        success = convert_with_marker(pdf_path)
    else:
        success = convert_with_docling(pdf_path, device, threads, batch_size)

    if success:
        print(f"Done: {pdf_path.stem}")
    return success


def convert_directory(
    pdf_dir: Path,
    backend: str,
    force: bool,
    batch: bool,
    device: str,
    threads: int,
    batch_size: int,
) -> None:
    """Convert all (unconverted) PDFs in a directory."""
    if not pdf_dir.exists():
        print(f"Error: Directory not found: {pdf_dir}")
        return

    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No PDF files found in: {pdf_dir}")
        return

    to_convert = pdfs if force else [p for p in pdfs if not is_converted(p)]
    skipped = len(pdfs) - len(to_convert)

    if not to_convert:
        print("All PDFs are already converted. Use --force to reconvert.")
        return

    print(f"Found {len(to_convert)} PDF(s) to convert (skipping {skipped} already done).")

    if batch and backend == "docling":
        if force:
            for md in MARKDOWN_DIR.glob("*.md"):
                md.unlink()
        print(f"Batch mode: converting {pdf_dir} in one pass  [docling]")
        convert_with_docling_batch(pdf_dir, device, threads, batch_size)
        return

    success, failed = 0, 0
    for pdf in to_convert:
        if convert_pdf(pdf, backend, device, threads, batch_size):
            success += 1
        else:
            failed += 1
        print()

    print(f"Converted: {success}  Failed: {failed}  Skipped: {skipped}")


def list_unconverted(pdf_dir: Path) -> None:
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    unconverted = [p for p in pdfs if not is_converted(p)]
    if not unconverted:
        print("All PDFs have been converted.")
    else:
        print(f"Unconverted ({len(unconverted)}):")
        for p in unconverted:
            print(f"  {p.name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert PDF files to Markdown using docling or marker-pdf."
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="PDF file or directory to convert (omit to use --all or --list)",
    )
    parser.add_argument(
        "--backend",
        choices=["docling", "marker"],
        default="docling",
        help="Conversion backend (default: docling)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help=f"Convert all unconverted PDFs in the default pdfs/ folder",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reconvert files that have already been converted",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Docling only: convert the whole directory in one call (fastest on Apple Silicon)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List unconverted PDFs without converting",
    )

    args = parser.parse_args()
    MARKDOWN_DIR.mkdir(exist_ok=True)

    device, threads, batch_size = detect_device()

    if args.list:
        target_dir = Path(args.path) if args.path else PDFS_DIR
        list_unconverted(target_dir)
        return

    if args.path:
        target = Path(args.path)
        # Resolve bare filename to pdfs/ folder
        if not target.exists() and not target.is_absolute():
            candidate = PDFS_DIR / target.name
            if candidate.exists():
                target = candidate

        if target.is_dir():
            convert_directory(target, args.backend, args.force, args.batch, device, threads, batch_size)
        else:
            if not args.force and is_converted(target):
                print(f"Already converted: {target.name}  (use --force to reconvert)")
                return
            convert_pdf(target, args.backend, device, threads, batch_size)
        return

    if args.all:
        convert_directory(PDFS_DIR, args.backend, args.force, args.batch, device, threads, batch_size)
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
