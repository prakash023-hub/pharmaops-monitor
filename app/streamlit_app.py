#!/usr/bin/env python3
"""PharmaOps Monitor — Plant Manager Command Center."""

import json
import os
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))

from impact_calculator import calculate_impact
from multi_agent import run_multi_agent
from orchestrator import check_system
from splunk_mcp import detect_top_anomaly, search

st.set_page_config(page_title="PharmaOps Monitor", page_icon="💊", layout="wide")

# ── Header ──────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#1e3a5f,#2d6a9f);padding:20px;border-radius:10px;color:white;margin-bottom:20px">
<h1 style="margin:0;color:white">PharmaOps Monitor</h1>
<p style="margin:5px 0 0;opacity:0.9">AI Multi-Agent GMP Compliance — Splunk MCP + Gemini + FDA 21 CFR + ICH Q7/Q8/Q9/Q10</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚡ System Status")
    health = check_system()
    c1, c2 = st.columns(2)
    c1.metric("MCP", "✅" if health.get("mcp") else "❌")
    c2.metric("REST", "✅" if health.get("splunk_rest") else "❌")
    c1.metric("Data", "✅" if health.get("csv") else "❌")
    c2.metric("Gemini", "✅" if health.get("gemini") else "❌")
    st.caption(f"Active: **{health.get('recommended', 'csv')}**")

    st.divider()
    st.header("💰 Impact Calculator")
    product = st.selectbox("Product", ["Amlodipine_5mg", "Atorvastatin_10mg", "Metformin_500mg", "Paracetamol_500mg", "Azithromycin_250mg"])
    devs = st.slider("Deviations", 1, 30, 24)
    gmp = st.selectbox("GMP Impact", ["Critical", "Major", "Minor"])
    impact = calculate_impact(product, devs, gmp, "FAIL")
    st.metric("Financial Risk", f"₹{impact['display']}")
    st.metric("Prevented (early AI)", f"₹{impact['prevented_if_caught_early_lakhs']}L")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Dashboard", "🤖 Multi-Agent", "🏛️ Regulatory", "💬 Ask AI",
    "📋 Reports", "📜 ICH/GMP", "🏭 Splunk Live",
])

# ── TAB 1: Dashboard ────────────────────────────────────────────────
with tab1:
    overview = ROOT / "docs" / "dashboard" / "00_dashboard_overview.png"
    if overview.exists():
        st.image(str(overview), use_container_width=True)
    st.link_button("Open Live Splunk Dashboard",
                   "http://localhost:8000/en-US/app/search/pharmaops_monitor")

# ── TAB 2: Multi-Agent ──────────────────────────────────────────────
with tab2:
    st.subheader("3-Agent Autonomous Pipeline")
    st.markdown("""
    | Agent | Role |
    |---|---|
    | **Detection Agent** | Scans Splunk for GMP temperature/moisture anomalies |
    | **Investigation Agent** | Gathers evidence, root cause + CAPA via Gemini |
    | **QA Review Agent** | Validates FDA 21 CFR + ICH Q7/Q8/Q9/Q10, approves/rejects |
    """)

    if not os.getenv("GEMINI_API_KEY"):
        st.error("Set `GEMINI_API_KEY` to run agents.")
    else:
        if st.button("🚀 Run Multi-Agent Pipeline", type="primary", use_container_width=True):
            with st.spinner("Detection → Investigation → QA Review..."):
                import io, contextlib
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    report = run_multi_agent(open_browser=False)
                st.code(buf.getvalue(), language=None)
                if report:
                    st.session_state["report"] = report
                    st.success(f"✅ {report['report_id']}")

        if "report" in st.session_state:
            r = st.session_state["report"]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Batch", r["batch_id"])
            col2.metric("Deviations", r["deviation_count"])
            col3.metric("Impact", f"₹{r.get('impact', {}).get('display', 'N/A')}")
            qa = r.get("agents", {}).get("qa_review", {})
            col4.metric("QA Decision", qa.get("qa_decision", "N/A"))
            st.markdown(r.get("agent_analysis", ""))

# ── TAB 3: Regulatory Intelligence ─────────────────────────────────
with tab3:
    from regulatory_report import build_regulatory_scores, save_regulatory_report
    from gmp_scorer import calculate_gmp_score
    from qms_risk import calculate_qms_risk_score
    from pv_assessment import assess_pv_risk

    st.subheader("Regulatory Intelligence — GMP + QMS + PV + ICH")
    st.markdown("**Demo case:** BATCH-1027 — Amlodipine 5mg — Coating thermostat drift")

    if st.button("🚀 Generate Regulatory Report", type="primary", use_container_width=True):
        scores = build_regulatory_scores(
            batch_id="BATCH-1027", product="Amlodipine_5mg",
            anomaly_type="temperature_deviation", failure_mode="coating_thermostat_drift",
            deviation_count=24, gmp_impact="Major", batch_status="FAIL",
        )
        st.session_state["reg_scores"] = scores
        save_regulatory_report(scores)

    if "reg_scores" in st.session_state:
        s = st.session_state["reg_scores"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("GMP Score", f"{s['gmp']['gmp_score']}/100", s["gmp"]["gmp_grade"])
        c2.metric("QMS Risk", f"{s['qms']['qms_risk_score']}/100", s["qms"]["qms_risk_level"])
        c3.metric("PV Risk", f"{s['pv']['pv_risk_score']}/100", s["pv"]["pv_risk_level"])
        c4.metric("ICH Q9 RPN", s["ich_risk"]["rpn"], s["ich_risk"]["risk_level"])

        st.markdown("### Industry: Manual vs PharmaOps AI")
        imp = s["industry_improvement"]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Detection", "30 sec", f"{imp['detection_time_reduction_pct']}% faster")
        m2.metric("Investigation", "2.5 min", f"{imp['investigation_time_reduction_pct']}% faster")
        m3.metric("Cost saved", f"₹{imp['cost_saving_per_deviation_lakhs']}L", "per deviation")
        m4.metric("Batch loss prevented", f"₹{imp['batch_loss_prevented_lakhs']}L", "early AI catch")

        with st.expander("GMP Pillar Scores"):
            st.bar_chart(s["gmp"]["pillar_scores"])
        with st.expander("QMS Risk Dimensions"):
            st.bar_chart(s["qms"]["dimension_risks"])
        with st.expander("PV Assessment"):
            st.json(s["pv"])
        with st.expander("ICH Regulatory Mapping"):
            st.json(s["ich"])

        st.info(f"**Summary:** {s['regulatory_summary']}")
        reg_file = ROOT / "agent" / "reports" / "regulatory_BATCH-1027.html"
        if reg_file.exists():
            st.components.v1.html(reg_file.read_text(encoding="utf-8"), height=600, scrolling=True)

# ── TAB 4: Chat ─────────────────────────────────────────────────────
with tab4:
    q = st.text_input("Plant Manager Question", placeholder="What batches failed?")
    if st.button("Ask") and q and os.getenv("GEMINI_API_KEY"):
        from mcp_chat_demo import chat
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            chat(q)
        st.markdown(buf.getvalue())

# ── TAB 5: Reports ──────────────────────────────────────────────────
with tab5:
    reports = sorted((ROOT / "agent" / "reports").glob("report_*.html"), reverse=True)
    if not reports:
        st.info("Run Multi-Agent pipeline first.")
    for f in reports[:5]:
        with st.expander(f"📄 {f.name}"):
            st.components.v1.html(f.read_text(encoding="utf-8"), height=450, scrolling=True)

# ── TAB 6: ICH/GMP Compliance ───────────────────────────────────────
with tab6:
    from ich_guidelines import ICH_FRAMEWORK, map_deviation, risk_level_from_ich

    st.subheader("ICH Regulatory Framework")
    st.markdown("PharmaOps maps every deviation to **ICH Q-series** + **FDA 21 CFR Part 211**")

    col1, col2 = st.columns(2)
    with col1:
        anomaly = st.selectbox("Anomaly Type", ["temperature_deviation", "moisture_deviation", "coating_thermostat_drift"])
        failure = st.selectbox("Failure Mode", ["unknown", "coating_thermostat_drift", "moisture_excursion", "equipment_downtime_cascade"])
    with col2:
        dev_count = st.slider("Deviation Count", 1, 30, 24)
        gmp_imp = st.selectbox("GMP Impact", ["Critical", "Major", "Minor"])

    if st.button("Map to ICH Guidelines"):
        m = map_deviation(anomaly, failure)
        r = risk_level_from_ich(dev_count, gmp_imp)
        st.success(m["regulatory_summary"])
        st.metric("ICH Q9 Risk Level", r["risk_level"], f"RPN={r['rpn']}")
        st.markdown(f"**CQA (ICH Q8):** {m['cqa']}")
        st.markdown(f"**Risk:** {m['risk_statement']}")
        for g in m["ich_guidelines"]:
            with st.expander(f"ICH {g['guideline']}: {g['title']}"):
                st.write(g["relevance"])
                st.write("Sections:", ", ".join(g["sections"]))
        st.markdown("**FDA 21 CFR:**")
        for f in m["fda_citations"]:
            st.write(f"§{f['section']}: {f['requirement']}")

    st.divider()
    st.markdown("**All ICH Guidelines in PharmaOps:**")
    for code, info in ICH_FRAMEWORK.items():
        st.write(f"**{code}** — {info['title']}")

# ── TAB 7: Splunk Live ──────────────────────────────────────────────
with tab7:
    col1, col2 = st.columns(2)
    if col1.button("Top Deviation Batches"):
        r = search(
            'search index=pharma_manufacturing source=temperature_logs.csv status=DEVIATION '
            '| stats count as deviations by batch_id product | sort -deviations | head 5'
        )
        st.dataframe(r.get("rows", []), use_container_width=True)
    if col2.button("Equipment Downtime"):
        r = search(
            'search index=pharma_manufacturing source=equipment_downtime.csv '
            '| stats sum(downtime_minutes) as total by equipment_id | sort -total'
        )
        st.dataframe(r.get("rows", []), use_container_width=True)

    if st.button("Detect Top Anomaly Now"):
        a = detect_top_anomaly()
        if a:
            st.json(a)
        else:
            st.warning("No anomalies found.")
