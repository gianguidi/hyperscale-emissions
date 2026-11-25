#!/usr/bin/env python3
"""Build manuscript Figure 1 maps.

Figure 1b (power plants) uses only public inputs and always runs.
Figure 1a (hyperscale data centers) needs the DUA-protected facility point
file ``data/processed/df_emissions_per_dc_SF.geojson``; it is skipped with a
message when that file is not available locally (see REPRO.md).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hyperscale_emissions.plotting_maps import (  # noqa: E402
    gpd,
    plot_figure1a_hyperscalers,
    plot_figure1b_power_plants,
)

PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "results" / "figures"
RESTRICTED_POINTS = PROCESSED / "df_emissions_per_dc_SF.geojson"
BA_POLYGONS = PROCESSED / "gdf_EPA_totals.geojson"


def main() -> None:
    if gpd is None:
        raise SystemExit(
            "geopandas is required for the Figure 1 maps. "
            "Install it with: pip install -r requirements.txt"
        )

    plot_figure1b_power_plants(
        plants_with_regions_path=str(PROCESSED / "plants_with_regions.csv"),
        gdf_EPA_totals_path=str(BA_POLYGONS),
        output_path=str(FIGURES / "figure1b_power_plants.pdf"),
    )
    print(f"Wrote {FIGURES / 'figure1b_power_plants.pdf'}")

    if RESTRICTED_POINTS.exists():
        plot_figure1a_hyperscalers(
            df_emissions_per_dc_SF_path=str(RESTRICTED_POINTS),
            gdf_EPA_totals_path=str(BA_POLYGONS),
            output_path=str(FIGURES / "figure1a_hyperscalers.pdf"),
        )
        print(f"Wrote {FIGURES / 'figure1a_hyperscalers.pdf'}")
    else:
        print(
            "Skipped Figure 1a: it needs the DUA-protected facility point file "
            f"{RESTRICTED_POINTS.relative_to(ROOT)}, which is not distributed "
            "publicly (see REPRO.md). Source Data Fig. 1 gives state-level counts."
        )


if __name__ == "__main__":
    main()
