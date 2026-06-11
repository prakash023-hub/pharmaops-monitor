"""
GMP Compliance Scorer — WHO/EU/FDA GMP principles + 21 CFR Part 211.

Scores batch manufacturing compliance 0-100 across 6 GMP pillars.
"""

GMP_PILLARS = {
    "documentation": {
        "weight": 0.20,
        "standard": "21 CFR 211.188 — Batch production records complete and accurate",
        "ich_ref": "ICH Q7 Section 6 — Documentation",
    },
    "process_control": {
        "weight": 0.25,
        "standard": "21 CFR 211.110 — In-process testing and CPP monitoring",
        "ich_ref": "ICH Q8 — Critical Process Parameters within design space",
    },
    "deviation_management": {
        "weight": 0.20,
        "standard": "21 CFR 211.100 — Written procedures; deviations recorded",
        "ich_ref": "ICH Q10 Section 3.2.2 — CAPA system",
    },
    "equipment_qualification": {
        "weight": 0.15,
        "standard": "21 CFR 211.68 — Equipment calibration and maintenance",
        "ich_ref": "ICH Q7 Section 5 — Process equipment",
    },
    "quality_oversight": {
        "weight": 0.10,
        "standard": "21 CFR 211.22 — Quality control unit responsibilities",
        "ich_ref": "ICH Q10 Section 2.1 — Management responsibilities",
    },
    "batch_release": {
        "weight": 0.10,
        "standard": "21 CFR 211.165 — Testing and release for distribution",
        "ich_ref": "ICH Q7 Section 11 — Laboratory controls",
    },
}


def calculate_gmp_score(
    deviation_count: int,
    batch_status: str = "FAIL",
    failure_mode: str = "unknown",
    has_capa: bool = True,
    investigation_complete: bool = True,
) -> dict:
    """Calculate GMP compliance score (0-100) across 6 pillars."""

    dev_penalty = min(40, deviation_count * 1.5)
    fail_penalty = 25 if batch_status == "FAIL" else 0
    equip_penalty = 20 if "thermostat" in failure_mode or "equipment" in failure_mode else 5

    pillar_scores = {
        "documentation": max(0, 100 - (0 if investigation_complete else 30)),
        "process_control": max(0, 100 - dev_penalty),
        "deviation_management": max(0, 100 - (0 if has_capa else 40) - min(30, deviation_count)),
        "equipment_qualification": max(0, 100 - equip_penalty),
        "quality_oversight": max(0, 100 - fail_penalty),
        "batch_release": 0 if batch_status == "FAIL" else max(0, 100 - dev_penalty * 0.5),
    }

    weighted = sum(
        pillar_scores[k] * GMP_PILLARS[k]["weight"] for k in GMP_PILLARS
    )
    overall = round(weighted, 1)

    grade = (
        "A — Compliant" if overall >= 85 else
        "B — Minor Gaps" if overall >= 70 else
        "C — Major Gaps" if overall >= 50 else
        "D — Non-Compliant" if overall >= 30 else
        "F — Critical Failure"
    )

    gaps = [
        f"{k}: {pillar_scores[k]:.0f}/100 — {GMP_PILLARS[k]['standard']}"
        for k, s in pillar_scores.items() if s < 70
    ]

    return {
        "gmp_score": overall,
        "gmp_grade": grade,
        "pillar_scores": pillar_scores,
        "gmp_gaps": gaps,
        "gmp_status": "COMPLIANT" if overall >= 85 else "AT_RISK" if overall >= 50 else "NON_COMPLIANT",
        "framework": "WHO GMP + EU GMP Annex 1 + FDA 21 CFR Part 211",
    }
