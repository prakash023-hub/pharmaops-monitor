"""Financial impact calculator — Indian pharma batch failure economics."""

# Industry benchmarks (INR lakhs)
BATCH_VALUE_LAKHS = {
    "Metformin_500mg": 80,
    "Amlodipine_5mg": 120,
    "Atorvastatin_10mg": 150,
    "Paracetamol_500mg": 60,
    "Azithromycin_250mg": 200,
}

GMP_MULTIPLIER = {"Critical": 1.0, "Major": 0.6, "Minor": 0.25}
INVESTIGATION_COST_LAKHS = 8
REWORK_COST_PCT = 0.35


def calculate_impact(
    product: str,
    deviation_count: int,
    gmp_impact: str = "Major",
    batch_status: str = "FAIL",
) -> dict:
    base = BATCH_VALUE_LAKHS.get(product, 100)
    mult = GMP_MULTIPLIER.get(gmp_impact, 0.6)
    deviation_factor = min(1.0, deviation_count / 20)

    batch_risk = round(base * mult * deviation_factor, 1)
    investigation = INVESTIGATION_COST_LAKHS
    rework = round(base * REWORK_COST_PCT * mult, 1) if batch_status == "FAIL" else 0
    downtime = round(3 + deviation_count * 0.5, 1)

    total_min = round(investigation + batch_risk * 0.4, 1)
    total_max = round(investigation + batch_risk + rework + downtime, 1)

    return {
        "product": product,
        "batch_value_lakhs": base,
        "gmp_impact": gmp_impact,
        "batch_risk_lakhs": batch_risk,
        "investigation_lakhs": investigation,
        "rework_lakhs": rework,
        "downtime_lakhs": downtime,
        "total_min_lakhs": total_min,
        "total_max_lakhs": total_max,
        "display": f"{total_min}-{total_max} lakhs",
        "prevented_if_caught_early_lakhs": round(total_max * 0.7, 1),
    }
