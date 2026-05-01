# PDF to Markdown Converter

A simple Python script that converts PDF files into Markdown — one file at a time, or an entire folder in one go.

## Installation

You'll need Python 3 and at least one of the two supported conversion backends:

```bash
pip install docling      # recommended — better accuracy on complex documents
pip install marker-pdf   # alternative — faster for simple documents
```

## Usage

Place your PDFs in a `pdfs/` folder next to the script, then run:

```bash
# Convert a single file
python convert.py pdfs/my-document.pdf

# Convert all PDFs in the pdfs/ folder
python convert.py --all

# Convert a whole folder
python convert.py path/to/folder/
```

Output is saved as `.md` files in a `markdown/` folder. Already-converted files are skipped automatically.

## Options

| Flag | Description |
|------|-------------|
| `--backend marker` | Use marker-pdf instead of docling |
| `--force` | Reconvert files that have already been converted |
| `--batch` | Convert the whole folder in one pass (fastest option, docling only) |
| `--list` | Show which PDFs haven't been converted yet |

## Which backend should I use?

**docling** (default) is the better choice when your documents have complex layouts — things like tables, figures, or multi-column text. It's slower but produces more accurate output.

**marker-pdf** is faster and works well for straightforward documents where speed matters more than perfect formatting.
