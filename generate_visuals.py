import logging
import os
import sys

import matplotlib.pyplot as plt
import pandas as pd

from atlas_schemas.config import settings

logger = logging.getLogger(__name__)


def main():
    data_path = str(settings.PROJECT_ROOT / settings.OUTPUT_FILE)

    # Guard: exit gracefully if data file is missing
    if not os.path.exists(data_path):
        logger.error("Data file '%s' not found. Run the enrichment trace first.", data_path)
        sys.exit(1)

    # Load enriched metadata
    df = pd.read_json(data_path)

    # Ensure output directory exists
    os.makedirs("charts", exist_ok=True)

    # 1. Bar chart: Architecture counts
    # Ensure 'architecture' column exists and is not empty
    if "architecture" in df.columns and not df["architecture"].empty:
        arch_counts = df["architecture"].value_counts()
        if not arch_counts.empty:
            fig = plt.figure()
            arch_counts.plot.bar()
            plt.title("Model Architecture Distribution")
            plt.xlabel("Architecture")
            plt.ylabel("Count")
            plt.savefig("charts/architecture_bar.png")
            plt.close(fig)
        else:
            logger.info("Skipping architecture chart: No architecture data.")
    else:
        logger.info("Skipping architecture chart: 'architecture' column not found or empty.")

    # 2. Pie chart: License distribution
    # Ensure 'license' column exists and is not empty
    if "license" in df.columns and not df["license"].empty:
        fig = plt.figure()
        license_counts = df["license"].value_counts()
        if not license_counts.empty:
            license_counts.plot.pie(autopct="%1.1f%%")
            plt.title("License Distribution")
            plt.savefig("charts/license_pie.png")
            plt.close(fig)
        else:
            logger.info("Skipping license chart: No license data.")
            plt.close(fig)
    else:
        logger.info("Skipping license chart: 'license' column not found or empty.")

    # 3. Histogram: Model size (Requires 'size_bytes' which is currently missing from enriched data)
    # This section is commented out until 'size_bytes' is reliably available in models_enriched.json
    # fig = plt.figure()
    # plt.hist(df['size_bytes'] / 1e9, bins=20)
    # plt.title('Model Size (GB)')
    # plt.xlabel('Size (GB)')
    # plt.ylabel('Frequency')
    # plt.savefig('charts/size_histogram.png')
    # plt.close(fig)

    logger.info("Visuals generation complete. Check the 'charts/' directory.")


if __name__ == "__main__":
    main()
