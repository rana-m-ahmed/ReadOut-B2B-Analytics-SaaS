import sys
import csv
import io
sys.path.append('d:/projects/ReadOut-B2B-Analytics-SaaS/apps/api')
from app.datasets.demo_generation import generate_demo_dataset, DEMO_DATASET_SEED

artifacts = generate_demo_dataset(seed=DEMO_DATASET_SEED)
content = artifacts.csv_bytes.decode('utf-8')
reader = csv.DictReader(io.StringIO(content))

total_revenue = 0
total_orders = 0

for row in reader:
    total_orders += 1
    total_revenue += float(row['revenue'])

print(f"Total Revenue: {total_revenue}")
print(f"Total Orders: {total_orders}")
print(f"Average Order Value: {total_revenue / total_orders if total_orders else 0}")
