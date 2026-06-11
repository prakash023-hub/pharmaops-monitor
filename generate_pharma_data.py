#!/usr/bin/env python3
"""
Generate FDA-aligned synthetic pharma manufacturing data.

Modeled on real GMP parameters:
- Tablet coating: 40-45°C (USP/FDA process validation ranges)
- Granulation moisture: 2-4% (standard oral solid dosage)
- Products: real API names used in Indian pharma exports

Each batch_id has ONE consistent product across all 4 data sources.
"""

import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

ROOT = Path(__file__).resolve().parent
OUTPUT = Path(os.getenv("PHARMA_DATA_DIR", ROOT))

# Real-world pharma products (top Indian export APIs)
PRODUCTS = {
    "Metformin_500mg": {"coating_temp": (40, 45), "moisture_max": 4.0, "line": "oral_solid"},
    "Amlodipine_5mg": {"coating_temp": (40, 45), "moisture_max": 3.5, "line": "oral_solid"},
    "Atorvastatin_10mg": {"coating_temp": (38, 44), "moisture_max": 3.8, "line": "oral_solid"},
    "Paracetamol_500mg": {"coating_temp": (40, 46), "moisture_max": 4.2, "line": "oral_solid"},
    "Azithromycin_250mg": {"coating_temp": (35, 42), "moisture_max": 3.5, "line": "oral_solid"},
}

EQUIPMENT = {
    "COAT-01": "film_coating",
    "COAT-02": "film_coating",
    "GRAN-01": "wet_granulation",
    "GRAN-02": "wet_granulation",
    "COMPRESS-01": "tablet_compression",
}

# Batches with injected failures for demo (realistic failure scenarios)
FAILURE_BATCHES = {
    "BATCH-1027": "coating_thermostat_drift",
    "BATCH-1011": "coating_thermostat_drift",
    "BATCH-1049": "coating_thermostat_drift",
    "BATCH-1012": "moisture_excursion",
    "BATCH-1038": "equipment_downtime_cascade",
}

N_BATCHES = 50
# Spread data over last 30 days so Splunk "All time" and recent ranges both work
END_DATE = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
START_DATE = END_DATE - timedelta(days=30)


def _batch_registry():
    """One consistent metadata record per batch."""
    registry = []
    product_names = list(PRODUCTS.keys())
    for i in range(N_BATCHES):
        batch_id = f"BATCH-{1001 + i}"
        product = product_names[i % len(product_names)]
        coat_eq = "COAT-01" if i % 2 == 0 else "COAT-02"
        gran_eq = "GRAN-01" if i % 3 == 0 else "GRAN-02"
        day_offset = int(30 * i / N_BATCHES)
        batch_start = START_DATE + timedelta(days=day_offset, hours=8 + (i % 6))
        failure = FAILURE_BATCHES.get(batch_id)
        registry.append({
            "batch_id": batch_id,
            "product": product,
            "coat_equipment": coat_eq,
            "gran_equipment": gran_eq,
            "batch_start": batch_start,
            "failure_mode": failure,
        })
    return registry


def _temp_status(temp: float, low: float, high: float) -> str:
    return "NORMAL" if low <= temp <= high else "DEVIATION"


def generate_temperature_logs(registry: list) -> pd.DataFrame:
    rows = []
    for b in registry:
        spec = PRODUCTS[b["product"]]
        low, high = spec["coating_temp"]
        failure = b["failure_mode"] == "coating_thermostat_drift"
        for minute in range(0, 180, 5):
            ts = b["batch_start"] + timedelta(minutes=minute)
            if failure:
                # Realistic drift: gradual rise then spike (equipment thermostat failure)
                if minute < 60:
                    temp = round(random.uniform(low, high), 2)
                elif minute < 120:
                    temp = round(random.uniform(high, high + 3), 2)
                else:
                    temp = round(random.uniform(low - 3, low), 2)
            elif random.random() < 0.04:
                temp = round(random.uniform(high + 1, high + 5), 2)
            else:
                temp = round(random.uniform(low, high), 2)
            rows.append({
                "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
                "batch_id": b["batch_id"],
                "equipment_id": b["coat_equipment"],
                "product": b["product"],
                "temperature_C": temp,
                "status": _temp_status(temp, low, high),
                "gmp_lower_C": low,
                "gmp_upper_C": high,
            })
    return pd.DataFrame(rows)


def generate_moisture_logs(registry: list) -> pd.DataFrame:
    rows = []
    for b in registry:
        spec = PRODUCTS[b["product"]]
        max_m = spec["moisture_max"]
        failure = b["failure_mode"] == "moisture_excursion"
        for minute in range(0, 120, 10):
            ts = b["batch_start"] + timedelta(minutes=minute + 30)
            if failure:
                moisture = round(random.uniform(max_m + 0.5, max_m + 3), 2)
            elif random.random() < 0.04:
                moisture = round(random.uniform(max_m + 0.2, max_m + 2), 2)
            else:
                moisture = round(random.uniform(2.0, max_m - 0.2), 2)
            rows.append({
                "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
                "batch_id": b["batch_id"],
                "equipment_id": b["gran_equipment"],
                "product": b["product"],
                "moisture_pct": moisture,
                "status": "NORMAL" if moisture <= max_m else "DEVIATION",
                "gmp_max_moisture_pct": max_m,
            })
    return pd.DataFrame(rows)


def generate_batch_summary(registry: list, temp_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for b in registry:
        dev_count = int(
            temp_df[(temp_df["batch_id"] == b["batch_id"]) & (temp_df["status"] == "DEVIATION")].shape[0]
        )
        moisture_dev = 1 if b["failure_mode"] == "moisture_excursion" else 0
        total_dev = dev_count + moisture_dev
        yield_pct = round(random.uniform(91, 99) if total_dev < 3 else random.uniform(85, 92), 2)
        status = "PASS" if total_dev < 4 and yield_pct >= 90 else "FAIL"
        rows.append({
            "timestamp": b["batch_start"].strftime("%Y-%m-%dT%H:%M:%S"),
            "batch_id": b["batch_id"],
            "product": b["product"],
            "yield_pct": yield_pct,
            "deviation_count": total_dev,
            "batch_status": status,
            "oee_score": round(random.uniform(72, 95) - total_dev * 2, 2),
            "failure_mode": b["failure_mode"] or "none",
        })
    return pd.DataFrame(rows)


def generate_downtime_logs(registry: list) -> pd.DataFrame:
    rows = []
    reasons = [
        "Thermostat calibration drift",
        "Scheduled preventive maintenance",
        "Mechanical seal replacement",
        "CIP cleaning cycle",
        "Power fluctuation recovery",
        "HVAC interlock trip",
    ]
    for eq_id, eq_type in EQUIPMENT.items():
        base_events = 5 if eq_id == "GRAN-01" else random.randint(2, 4)
        for _ in range(base_events):
            ts = START_DATE + timedelta(
                days=random.randint(0, 29),
                hours=random.randint(0, 20),
            )
            duration = random.randint(45, 180) if eq_id == "GRAN-01" else random.randint(15, 120)
            rows.append({
                "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
                "equipment_id": eq_id,
                "equipment_type": eq_type,
                "downtime_minutes": duration,
                "reason": random.choice(reasons),
                "severity": "HIGH" if duration > 120 else "MEDIUM" if duration > 60 else "LOW",
            })
    # Link downtime to failure batch equipment
    for b in registry:
        if b["failure_mode"] == "equipment_downtime_cascade":
            rows.append({
                "timestamp": (b["batch_start"] - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S"),
                "equipment_id": b["coat_equipment"],
                "equipment_type": "film_coating",
                "downtime_minutes": 145,
                "reason": "Thermostat calibration drift",
                "severity": "HIGH",
            })
    return pd.DataFrame(rows)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    registry = _batch_registry()

    temp_df = generate_temperature_logs(registry)
    moisture_df = generate_moisture_logs(registry)
    batch_df = generate_batch_summary(registry, temp_df)
    downtime_df = generate_downtime_logs(registry)

    files = {
        "temperature_logs.csv": temp_df,
        "moisture_logs.csv": moisture_df,
        "batch_summary.csv": batch_df,
        "equipment_downtime.csv": downtime_df,
    }
    for name, df in files.items():
        path = OUTPUT / name
        df.to_csv(path, index=False)
        print(f"  {name}: {len(df)} rows → {path}")

    print(f"\nData window: {START_DATE.date()} to {END_DATE.date()}")
    print(f"Failure batches: {', '.join(FAILURE_BATCHES.keys())}")
    top = (
        temp_df[temp_df["status"] == "DEVIATION"]
        .groupby("batch_id")
        .size()
        .sort_values(ascending=False)
        .head(3)
    )
    print(f"Top deviation batches:\n{top.to_string()}")
    print("\nDone. Re-upload CSVs to Splunk index pharma_manufacturing.")


if __name__ == "__main__":
    print("Generating FDA-aligned pharma manufacturing data...")
    main()
