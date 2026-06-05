#!/usr/bin/env python3
"""Generate dashboard panel preview images from CSV data for README and Devpost."""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "dashboard"
OUT.mkdir(parents=True, exist_ok=True)

plt.style.use("seaborn-v0_8-whitegrid")
COLORS = {"PASS": "#22c55e", "FAIL": "#ef4444", "NORMAL": "#3b82f6", "DEVIATION": "#f97316"}


def panel1_deviations_by_batch():
    df = pd.read_csv(ROOT / "temperature_logs.csv")
    dev = df[df["status"] == "DEVIATION"].groupby("batch_id").size().sort_values(ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(dev.index[::-1], dev.values[::-1], color=COLORS["DEVIATION"], edgecolor="white")
    ax.set_xlabel("Deviation Count")
    ax.set_title("Panel 1: Temperature Deviations by Batch", fontsize=13, fontweight="bold", color="#1e3a5f")
    ax.set_facecolor("#f8fafc")
    fig.patch.set_facecolor("#f8fafc")
    for bar in bars:
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2, int(bar.get_width()), va="center", fontsize=9)
    plt.tight_layout()
    fig.savefig(OUT / "01_temperature_deviations_by_batch.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {OUT / '01_temperature_deviations_by_batch.png'}")


def panel2_ai_anomaly_detection():
    df = pd.read_csv(ROOT / "temperature_logs.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    hourly = df.groupby(df["timestamp"].dt.floor("h"))["temperature_C"].mean().reset_index()

    temps = hourly["temperature_C"].values
    median = pd.Series(temps).rolling(10, min_periods=1).median()
    mad = (pd.Series(temps) - median).abs().rolling(10, min_periods=1).median()
    upper = median + 3 * mad
    lower = median - 3 * mad

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(hourly["timestamp"], temps, color="#3b82f6", linewidth=1.5, label="Temperature (°C)")
    ax.fill_between(hourly["timestamp"], lower, upper, alpha=0.2, color="#22c55e", label="AI Bounds (MAD 3σ)")
    outliers = (temps > upper) | (temps < lower)
    ax.scatter(hourly["timestamp"][outliers], temps[outliers], color="#ef4444", s=40, zorder=5, label="Anomaly")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title("Panel 2: AI Temperature Anomaly Detection (MAD)", fontsize=13, fontweight="bold", color="#1e3a5f")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_facecolor("#f8fafc")
    fig.patch.set_facecolor("#f8fafc")
    plt.xticks(rotation=30, fontsize=8)
    plt.tight_layout()
    fig.savefig(OUT / "02_ai_anomaly_detection.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {OUT / '02_ai_anomaly_detection.png'}")


def panel3_gmp_monitoring_bounds():
    df = pd.read_csv(ROOT / "temperature_logs.csv")
    batch = df[df["batch_id"] == "BATCH-1011"].copy()
    batch["timestamp"] = pd.to_datetime(batch["timestamp"])

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(batch["timestamp"], batch["temperature_C"], color="#2563eb", linewidth=2, marker="o", markersize=3)
    ax.axhspan(40, 45, alpha=0.15, color="#22c55e", label="GMP Spec (40-45°C)")
    ax.axhline(45, color="#ef4444", linestyle="--", linewidth=1, label="Upper Limit")
    ax.axhline(40, color="#ef4444", linestyle="--", linewidth=1, label="Lower Limit")
    dev_pts = batch[batch["status"] == "DEVIATION"]
    ax.scatter(dev_pts["timestamp"], dev_pts["temperature_C"], color="#ef4444", s=60, zorder=5, label="Deviation")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title("Panel 3: GMP Temperature Monitoring — BATCH-1011", fontsize=13, fontweight="bold", color="#1e3a5f")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_facecolor("#f8fafc")
    fig.patch.set_facecolor("#f8fafc")
    plt.xticks(rotation=30, fontsize=8)
    plt.tight_layout()
    fig.savefig(OUT / "03_gmp_temperature_bounds.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {OUT / '03_gmp_temperature_bounds.png'}")


def panel4_batch_pass_fail():
    df = pd.read_csv(ROOT / "batch_summary.csv")
    counts = df["batch_status"].value_counts()

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = [COLORS.get(s, "#94a3b8") for s in counts.index]
    wedges, texts, autotexts = ax.pie(
        counts.values, labels=counts.index, autopct="%1.1f%%",
        colors=colors, startangle=90, explode=[0.03] * len(counts),
        textprops={"fontsize": 11},
    )
    for t in autotexts:
        t.set_fontweight("bold")
    ax.set_title("Panel 4: Batch Pass/Fail Status", fontsize=13, fontweight="bold", color="#1e3a5f")
    fig.patch.set_facecolor("#f8fafc")
    plt.tight_layout()
    fig.savefig(OUT / "04_batch_pass_fail.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {OUT / '04_batch_pass_fail.png'}")


def panel5_equipment_downtime():
    df = pd.read_csv(ROOT / "equipment_downtime.csv")
    totals = df.groupby("equipment_id")["downtime_minutes"].sum().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(totals)))
    bars = ax.barh(totals.index, totals.values, color=colors, edgecolor="white")
    ax.set_xlabel("Total Downtime (minutes)")
    ax.set_title("Panel 5: Equipment Downtime by Machine", fontsize=13, fontweight="bold", color="#1e3a5f")
    ax.set_facecolor("#f8fafc")
    fig.patch.set_facecolor("#f8fafc")
    for bar in bars:
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2, f"{int(bar.get_width())} min", va="center", fontsize=9)
    plt.tight_layout()
    fig.savefig(OUT / "05_equipment_downtime.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {OUT / '05_equipment_downtime.png'}")


def panel_overview():
    """Combined 2x3 overview image for README hero."""
    images = sorted(OUT.glob("0*.png"))
    if len(images) < 5:
        return

    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    fig.suptitle("PharmaOps Monitor Dashboard", fontsize=16, fontweight="bold", color="#1e3a5f", y=1.02)

    for ax, img_path in zip(axes.flat, images):
        img = plt.imread(img_path)
        ax.imshow(img)
        ax.axis("off")
        ax.set_title(img_path.stem.replace("_", " ").title(), fontsize=9, pad=4)

    if len(images) < 6:
        axes.flat[-1].axis("off")

    plt.tight_layout()
    fig.savefig(OUT / "00_dashboard_overview.png", dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {OUT / '00_dashboard_overview.png'}")


def main():
    print("Generating dashboard preview images...")
    panel1_deviations_by_batch()
    panel2_ai_anomaly_detection()
    panel3_gmp_monitoring_bounds()
    panel4_batch_pass_fail()
    panel5_equipment_downtime()
    panel_overview()
    print("Done.")


if __name__ == "__main__":
    main()
