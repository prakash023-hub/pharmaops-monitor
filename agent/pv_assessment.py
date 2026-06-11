"""
Pharmacovigilance (PV) Risk Assessment.

Links manufacturing deviations to patient safety risk per ICH E2E / WHO PV guidelines.
"""

PV_RISK_FACTORS = {
    "temperature_deviation": {
        "patient_risk": "Drug product stability compromise — potential sub-potent/supra-potent dosing",
        "ich_ref": "ICH E2E — Pharmacovigilance Planning",
        "who_ref": "WHO PV Guidelines — Product quality-related adverse events",
        "severity": "HIGH",
    },
    "moisture_deviation": {
        "patient_risk": "Microbial growth risk, degradation of moisture-sensitive APIs",
        "ich_ref": "ICH Q1A — Stability (moisture impact)",
        "who_ref": "WHO GMP — Environmental monitoring",
        "severity": "MEDIUM",
    },
    "coating_thermostat_drift": {
        "patient_risk": "Modified drug release profile — bioavailability change for extended-release products",
        "ich_ref": "ICH E2E + ICH Q8 CQA — dissolution/release profile",
        "who_ref": "WHO — Process validation requirements",
        "severity": "HIGH",
    },
}


PRODUCT_PV_PROFILE = {
    "Metformin_500mg": {"therapeutic_class": "Antidiabetic", "pv_priority": "MEDIUM", "reportable": False},
    "Amlodipine_5mg": {"therapeutic_class": "Antihypertensive", "pv_priority": "HIGH", "reportable": True},
    "Atorvastatin_10mg": {"therapeutic_class": "Lipid-lowering", "pv_priority": "HIGH", "reportable": True},
    "Paracetamol_500mg": {"therapeutic_class": "Analgesic", "pv_priority": "LOW", "reportable": False},
    "Azithromycin_250mg": {"therapeutic_class": "Antibiotic", "pv_priority": "CRITICAL", "reportable": True},
}


def assess_pv_risk(
    product: str,
    anomaly_type: str = "temperature_deviation",
    failure_mode: str = "unknown",
    batch_status: str = "FAIL",
    deviation_count: int = 0,
) -> dict:
    """Pharmacovigilance risk assessment for manufacturing deviation."""

    key = failure_mode if failure_mode in PV_RISK_FACTORS else anomaly_type
    pv_factor = PV_RISK_FACTORS.get(key, PV_RISK_FACTORS["temperature_deviation"])
    profile = PRODUCT_PV_PROFILE.get(product, {"therapeutic_class": "Unknown", "pv_priority": "MEDIUM", "reportable": False})

    base_score = {"CRITICAL": 85, "HIGH": 65, "MEDIUM": 40, "LOW": 20}.get(pv_factor["severity"], 50)
    product_mult = {"CRITICAL": 1.2, "HIGH": 1.1, "MEDIUM": 1.0, "LOW": 0.8}.get(profile["pv_priority"], 1.0)
    dev_mult = min(1.3, 1 + deviation_count / 30)
    fail_mult = 1.2 if batch_status == "FAIL" else 1.0

    pv_score = round(min(100, base_score * product_mult * dev_mult * fail_mult), 1)

    pv_level = (
        "CRITICAL — Report to PV team immediately" if pv_score >= 80 else
        "HIGH — PV review within 24h" if pv_score >= 60 else
        "MEDIUM — Document in batch record" if pv_score >= 40 else
        "LOW — No PV action required"
    )

    return {
        "pv_risk_score": pv_score,
        "pv_risk_level": pv_level.split(" — ")[0],
        "pv_action": pv_level.split(" — ")[1] if " — " in pv_level else pv_level,
        "patient_safety_risk": pv_factor["patient_risk"],
        "therapeutic_class": profile["therapeutic_class"],
        "pv_reportable": profile["reportable"] and pv_score >= 60,
        "ich_pv_reference": pv_factor["ich_ref"],
        "who_pv_reference": pv_factor["who_ref"],
        "pv_notification_required": pv_score >= 60,
        "regulatory_reporting": (
            "Submit Product Quality Complaint to PV system per ICH E2E"
            if profile["reportable"] and pv_score >= 60
            else "Internal QA documentation only"
        ),
    }
