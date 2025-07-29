import os
import pandas as pd
import matplotlib.pyplot as plt

# Load enriched metadata
df = pd.read_json('models_enriched.json')

# Ensure output directory exists
os.makedirs("charts", exist_ok=True)

# 1. Bar chart: Architecture counts
# Ensure 'architecture' column exists and is not empty
if 'architecture' in df.columns and not df['architecture'].empty:
    arch_counts = df['architecture'].value_counts()
    if not arch_counts.empty:
        plt.figure()
        arch_counts.plot.bar()
        plt.title('Model Architecture Distribution')
        plt.xlabel('Architecture')
        plt.ylabel('Count')
        plt.savefig('charts/architecture_bar.png')
    else:
        print("Skipping architecture chart: No architecture data.")
else:
    print("Skipping architecture chart: 'architecture' column not found or empty.")

# 2. Pie chart: License distribution
# Ensure 'license' column exists and is not empty
if 'license' in df.columns and not df['license'].empty:
    plt.figure()
    license_counts = df['license'].value_counts()
    if not license_counts.empty:
        license_counts.plot.pie(autopct='%1.1f%%')
        plt.title('License Distribution')
        plt.savefig('charts/license_pie.png')
    else:
        print("Skipping license chart: No license data.")
else:
    print("Skipping license chart: 'license' column not found or empty.")

# 3. Histogram: Model size (Requires 'size_bytes' which is currently missing from enriched data)
# This section is commented out until 'size_bytes' is reliably available in models_enriched.json
# plt.figure()
# plt.hist(df['size_bytes'] / 1e9, bins=20)
# plt.title('Model Size (GB)')
# plt.xlabel('Size (GB)')
# plt.ylabel('Frequency')
# plt.savefig('charts/size_histogram.png')

print("Visuals generation complete. Check the 'charts/' directory.")
