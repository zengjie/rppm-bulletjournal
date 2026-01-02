# Bullet Journal PDF Generator for reMarkable Paper Pro Move

This project generates a Bullet Journal PDF optimized for reMarkable Paper Pro Move (rPPM).

## Project Structure

- `main.py` - Main entry point
- `bujo/` - Modular generator (config, calendar model, rendering, validation)
- `original/Bullet Journal.pdf` - Original reference PDF
- `output/BulletJournal_rPPM.pdf` - Generated output

## Usage

```bash
./download_fonts.sh
uv venv
uv sync
uv run python main.py
```

## Requirements

- Python 3.10+
- PyMuPDF (`fitz`) via `pyproject.toml`
- EB Garamond fonts downloaded to `fonts/` (use `./download_fonts.sh`)

## Output Specifications

- Page size: 954 x 1696 pixels
- Optimized for rPPM screen with top toolbar safe zone (130px)
- Dynamic page count based on calendar/year and settings

## Development Workflow

When modifying page layout or rendering code:

1. Run `uv run python main.py` to generate the PDF
2. Extract screenshots of affected pages to `screenshots/` directory (not tracked by git)
3. Verify layout, alignment, font sizes, and spacing visually before considering the task complete
4. Pay special attention to:
   - Symbol alignment (Signifiers, N.A.M.E. symbols, text should be vertically aligned)
   - Font readability and consistency
   - Proper use of page margins and content area
   - Link target accuracy (if applicable)
