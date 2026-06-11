"""
ICH Regulatory Framework for PharmaOps Monitor.

Maps manufacturing deviations to ICH Q-series guidelines and FDA 21 CFR Part 211.
Used by Investigation Agent and QA Review Agent for compliance-grounded CAPA.
"""

ICH_FRAMEWORK = {
    "Q1A(R2)": {
        "title": "Stability Testing of New Drug Substances and Products",
        "relevance": "Temperature excursions affect shelf-life and stability data integrity.",
        "sections": ["2.1.1 General", "2.2.2 Storage Conditions"],
    },
    "Q2(R2)": {
        "title": "Validation of Analytical Procedures",
        "relevance": "QC testing validity after process deviations.",
        "sections": ["2.2 Validation of Analytical Procedures"],
    },
    "Q7": {
        "title": "GMP for Active Pharmaceutical Ingredients",
        "relevance": "Manufacturing process controls, deviation handling, batch records.",
        "sections": [
            "Section 8: Production and In-Process Controls",
            "Section 10: Storage and Distribution",
            "Section 13: Change Control",
            "Section 14: Rejection and Reuse of Materials",
        ],
    },
    "Q8(R2)": {
        "title": "Pharmaceutical Development",
        "relevance": "Critical Quality Attributes (CQAs) — temperature/moisture are CQAs for coating/granulation.",
        "sections": [
            "Section 2.1 Quality Target Product Profile",
            "Section 2.3 Critical Quality Attributes",
            "Section 3.2.1 Design Space",
        ],
    },
    "Q9(R1)": {
        "title": "Quality Risk Management",
        "relevance": "Risk assessment for deviation impact on patient safety and product quality.",
        "sections": [
            "Section 4.3 Risk Assessment",
            "Section 4.4 Risk Control",
            "Section 4.5 Risk Communication",
            "Section 4.6 Risk Review",
        ],
    },
    "Q10": {
        "title": "Pharmaceutical Quality System",
        "relevance": "CAPA system, change management, management review of deviations.",
        "sections": [
            "Section 3.2.1 Process Performance and Product Quality Monitoring",
            "Section 3.2.2 CAPA System",
            "Section 3.2.3 Change Management System",
            "Section 3.3 Management Review",
        ],
    },
    "Q11": {
        "title": "Development and Manufacture of Drug Substances",
        "relevance": "Process parameter control during API/drug product manufacturing.",
        "sections": [
            "Section 9: Manufacturing Process Development",
            "Section 10: Starting Material and Process Controls",
        ],
    },
}

FDA_CFR = {
    "211.100": "Written procedures; deviations must be recorded and justified",
    "211.110": "Sampling and testing of in-process materials and drug products",
    "211.192": "Production record review — investigation of unexplained discrepancies",
    "211.198": "Complaint files — product quality complaints",
    "211.67": "Equipment cleaning and maintenance",
    "211.68": "Automatic, mechanical, and electronic equipment — calibration",
}

# Deviation type → applicable ICH + FDA
DEVIATION_MAP = {
    "temperature_deviation": {
        "ich": ["Q7", "Q8(R2)", "Q9(R1)", "Q10", "Q1A(R2)"],
        "fda": ["211.100", "211.110", "211.192", "211.68"],
        "cqa": "Coating temperature (Critical Process Parameter)",
        "risk_statement": "Temperature excursion may alter drug release profile, stability, and content uniformity per ICH Q8 CQA.",
    },
    "moisture_deviation": {
        "ich": ["Q7", "Q8(R2)", "Q9(R1)", "Q10", "Q11"],
        "fda": ["211.100", "211.110", "211.192"],
        "cqa": "Granulation moisture (Critical Process Parameter)",
        "risk_statement": "Moisture excursion affects granule properties, compression, and final tablet hardness per ICH Q8.",
    },
    "coating_thermostat_drift": {
        "ich": ["Q7", "Q9(R1)", "Q10", "Q1A(R2)"],
        "fda": ["211.68", "211.100", "211.192", "211.67"],
        "cqa": "Equipment temperature control system",
        "risk_statement": "Thermostat drift indicates loss of process control — ICH Q10 CAPA and ICH Q9 risk reassessment required.",
    },
    "equipment_downtime_cascade": {
        "ich": ["Q7", "Q10", "Q9(R1)"],
        "fda": ["211.67", "211.68", "211.100"],
        "cqa": "Equipment availability and maintenance",
        "risk_statement": "Unplanned downtime may compromise batch integrity — ICH Q10 change control and maintenance program review.",
    },
    "moisture_excursion": {
        "ich": ["Q7", "Q8(R2)", "Q9(R1)", "Q10"],
        "fda": ["211.100", "211.110", "211.192"],
        "cqa": "Granulation endpoint moisture",
        "risk_statement": "Moisture above specification risks microbial growth and degradation per ICH Q1A stability principles.",
    },
}


def map_deviation(
    anomaly_type: str = "temperature_deviation",
    failure_mode: str = "unknown",
) -> dict:
    """Return ICH + FDA regulatory mapping for a deviation."""
    key = failure_mode if failure_mode in DEVIATION_MAP else anomaly_type
    mapping = DEVIATION_MAP.get(key, DEVIATION_MAP["temperature_deviation"])

    ich_details = []
    for code in mapping["ich"]:
        info = ICH_FRAMEWORK.get(code, {})
        ich_details.append({
            "guideline": code,
            "title": info.get("title", ""),
            "relevance": info.get("relevance", ""),
            "sections": info.get("sections", []),
        })

    fda_details = [
        {"section": sec, "requirement": FDA_CFR[sec]}
        for sec in mapping["fda"]
        if sec in FDA_CFR
    ]

    return {
        "anomaly_type": anomaly_type,
        "failure_mode": failure_mode,
        "cqa": mapping["cqa"],
        "risk_statement": mapping["risk_statement"],
        "ich_guidelines": ich_details,
        "fda_citations": fda_details,
        "regulatory_summary": (
            f"This deviation affects {mapping['cqa']}. "
            f"Applicable: {', '.join(mapping['ich'])} + FDA 21 CFR {', '.join('§' + s for s in mapping['fda'])}."
        ),
    }


def ich_prompt_context(anomaly_type: str, failure_mode: str = "unknown") -> str:
    """Formatted ICH context for Gemini agent prompts."""
    m = map_deviation(anomaly_type, failure_mode)
    lines = [
        "ICH REGULATORY FRAMEWORK:",
        f"CQA affected: {m['cqa']}",
        f"Risk: {m['risk_statement']}",
        "",
        "Applicable ICH Guidelines:",
    ]
    for g in m["ich_guidelines"]:
        lines.append(f"  - {g['guideline']}: {g['title']}")
        lines.append(f"    Sections: {', '.join(g['sections'][:2])}")
    lines.append("")
    lines.append("Applicable FDA 21 CFR Part 211:")
    for f in m["fda_citations"]:
        lines.append(f"  - §{f['section']}: {f['requirement']}")
    return "\n".join(lines)


def risk_level_from_ich(deviation_count: int, gmp_impact: str) -> dict:
    """ICH Q9(R1) risk classification."""
    severity = {"Critical": 4, "Major": 3, "Minor": 2}.get(gmp_impact, 3)
    occurrence = 4 if deviation_count >= 20 else 3 if deviation_count >= 10 else 2
    detectability = 1  # AI detected it — high detectability lowers risk
    rpn = severity * occurrence * detectability

    level = "HIGH" if rpn >= 24 else "MEDIUM" if rpn >= 8 else "LOW"
    return {
        "severity": severity,
        "occurrence": occurrence,
        "detectability": detectability,
        "rpn": rpn,
        "risk_level": level,
        "method": "ICH Q9(R1) Risk Priority Number (RPN)",
        "recommendation": (
            "Immediate CAPA per ICH Q10 §3.2.2" if level == "HIGH"
            else "Standard deviation investigation per ICH Q7 Section 14"
        ),
    }
