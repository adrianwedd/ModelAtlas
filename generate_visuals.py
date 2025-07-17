import os
import pandas as pd
import matplotlib.pyplot as plt

# Load enriched metadata
df = pd.read_json('models_enriched.json')

# Ensure output directory exists
os.makedirs("charts", exist_ok=True)

# 1. Bar chart: Architecture counts
arch_counts = df['architecture'].value_counts()
plt.figure()
arch_counts.plot.bar()
plt.title('Model Architecture Distribution')
plt.xlabel('Architecture')
plt.ylabel('Count')
plt.savefig('charts/architecture_bar.png')

# 2. Pie chart: License distribution
plt.figure()
license_counts = df['license'].value_counts()
license_counts.plot.pie(autopct='%1.1f%%')
plt.title('License Distribution')
plt.savefig('charts/license_pie.png')

# 3. Histogram: Model size
plt.figure()
plt.hist(df['size_bytes'] / 1e9, bins=20)
plt.title('Model Size (GB)')
plt.xlabel('Size (GB)')
plt.ylabel('Frequency')
plt.savefig('charts/size_histogram.png')
