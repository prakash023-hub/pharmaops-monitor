import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

random.seed(42)
np.random.seed(42)

# Settings
n_batches = 50
start_date = datetime(2026, 1, 1)
output_dir = os.path.expanduser("~/pharma_ops/data")
os.makedirs(output_dir, exist_ok=True)

equipment_ids = ["COAT-01", "COAT-02", "GRAN-01", "GRAN-02", "COMPRESS-01"]
products = ["Metformin_500mg", "Amlodipine_5mg", "Atorvastatin_10mg", "Paracetamol_500mg"]

# 1. Temperature logs
temp_logs = []
for i in range(n_batches):
    batch_id = f"BATCH-{1001+i}"
    eq = random.choice(equipment_ids[:2])
    product = random.choice(products)
    batch_start = start_date + timedelta(days=i//2, hours=random.randint(0,12))
    for minute in range(0, 180, 5):
        ts = batch_start + timedelta(minutes=minute)
        # Normal range 40-45C, inject anomalies
        if random.random() < 0.05:
            temp = round(random.uniform(46, 50), 2)  # anomaly high
        elif random.random() < 0.03:
            temp = round(random.uniform(35, 39), 2)  # anomaly low
        else:
            temp = round(random.uniform(40, 45), 2)  # normal
        temp_logs.append({
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
            "batch_id": batch_id,
            "equipment_id": eq,
            "product": product,
            "temperature_C": temp,
            "status": "NORMAL" if 40 <= temp <= 45 else "DEVIATION"
        })

df_temp = pd.DataFrame(temp_logs)
df_temp.to_csv(f"{output_dir}/temperature_logs.csv", index=False)
print(f"Temperature logs: {len(df_temp)} rows")

# 2. Moisture logs
moisture_logs = []
for i in range(n_batches):
    batch_id = f"BATCH-{1001+i}"
    eq = random.choice(equipment_ids[2:4])
    product = random.choice(products)
    batch_start = start_date + timedelta(days=i//2, hours=random.randint(0,12))
    for minute in range(0, 120, 10):
        ts = batch_start + timedelta(minutes=minute)
        if random.random() < 0.05:
            moisture = round(random.uniform(5, 7), 2)
        else:
            moisture = round(random.uniform(2, 4), 2)
        moisture_logs.append({
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
            "batch_id": batch_id,
            "equipment_id": eq,
            "product": product,
            "moisture_pct": moisture,
            "status": "NORMAL" if moisture <= 4 else "DEVIATION"
        })

df_moisture = pd.DataFrame(moisture_logs)
df_moisture.to_csv(f"{output_dir}/moisture_logs.csv", index=False)
print(f"Moisture logs: {len(df_moisture)} rows")

# 3. Batch summary
batch_records = []
for i in range(n_batches):
    batch_id = f"BATCH-{1001+i}"
    product = random.choice(products)
    batch_start = start_date + timedelta(days=i//2)
    yield_pct = round(random.uniform(88, 99), 2)
    deviations = random.randint(0, 5)
    status = "PASS" if deviations < 3 and yield_pct > 90 else "FAIL"
    batch_records.append({
        "timestamp": batch_start.strftime("%Y-%m-%dT%H:%M:%S"),
        "batch_id": batch_id,
        "product": product,
        "yield_pct": yield_pct,
        "deviation_count": deviations,
        "batch_status": status,
        "oee_score": round(random.uniform(72, 95), 2)
    })

df_batch = pd.DataFrame(batch_records)
df_batch.to_csv(f"{output_dir}/batch_summary.csv", index=False)
print(f"Batch summary: {len(df_batch)} rows")

# 4. Equipment downtime
downtime_logs = []
for eq in equipment_ids:
    for i in range(random.randint(2, 6)):
        ts = start_date + timedelta(days=random.randint(0,80), hours=random.randint(0,20))
        duration = random.randint(15, 240)
        downtime_logs.append({
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
            "equipment_id": eq,
            "downtime_minutes": duration,
            "reason": random.choice(["Scheduled maintenance","Mechanical failure","Cleaning","Calibration","Power failure"]),
            "severity": "HIGH" if duration > 120 else "MEDIUM" if duration > 60 else "LOW"
        })

df_downtime = pd.DataFrame(downtime_logs)
df_downtime.to_csv(f"{output_dir}/equipment_downtime.csv", index=False)
print(f"Downtime logs: {len(df_downtime)} rows")

print(f"\nAll files saved to: {output_dir}")
print("Done!")
