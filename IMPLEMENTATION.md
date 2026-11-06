# Rexbiswas GitHub Profile Setup

## Phase 1 files
- `README.md` — profile content
- `dark.svg` — dark-theme banner
- `light.svg` — light-theme banner
- `assets/` — preview and generated portrait intermediates
- `scripts/generate_rexbiswas_banner.py` — generator source

## Upload to GitHub
Create a **public** repository named exactly `Rexbiswas` under the `Rexbiswas` account.
Upload `README.md`, `dark.svg`, and `light.svg` to the repository root.

The `assets/` and `scripts/` folders are supporting/source files and are not required for the banner to display.

## Important
The generator expects `assets/source-photo.png`. The original source photograph is intentionally not included in this scaffold. Add it locally only if you want to regenerate the portrait. Do not commit a private photograph unless you want it publicly accessible.

## Later phases
Add `.github/workflows/snake.yml` in Phase 3, after configuring GitHub Actions permissions. Do not add an empty workflow or a snake image reference before the workflow has generated the `output` branch.
