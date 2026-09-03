"""
app.py - Streamlit entry point for AI Resume Assistant
Run: streamlit run app.py
"""
from typing import Dict, Any
import streamlit as st
from modules import domain_config, file_parser, gemini_client, scorer, ui_components, report_generator

st.set_page_config(page_title="AI Resume Assistant", layout="wide", initial_sidebar_state="expanded")

# --- Header ---
st.title("AI Resume Assistant")
st.write("Evaluate and improve resumes with domain-specific guidance powered by Google Gemini.")

# --- Config & Secrets ---
GEMINI_ENV_NAME = "GEMINI_API_KEY"
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    # fallback to dotenv/sysenv if running locally
    from dotenv import load_dotenv
    import os
    load_dotenv()
    api_key = os.environ.get(GEMINI_ENV_NAME)

if not api_key:
    st.warning(
        "No Gemini API key found. Add it under Streamlit Cloud → App → Settings → Secrets as:\n\n"
        'GEMINI_API_KEY = "your-real-key-here"\n\n'
        "For local testing, set a .env or environment variable with the same name."
    )

# Instantiate Gemini client
client = gemini_client.GeminiClient(api_key=api_key)

# --- Sidebar Controls ---
with st.sidebar:
    st.header("Controls")
    domain = ui_components.domain_selector(domain_config.DOMAINS)
    view_mode = st.selectbox("View", ["Candidate Feedback (detailed)", "Recruiter Screening (condensed)"])
    # weight sliders
    weights = ui_components.weight_sliders()  # returns normalized dict (sums to 100)
    st.markdown("---")
    st.checkbox("Show session history", key="show_history")
    st.markdown("### ATS / Job Description")
    show_ats = st.checkbox("Enable ATS keyword matching", value=True)
    job_desc = st.text_area("Paste target job description (optional)", height=120) if show_ats else ""
    st.markdown("---")
    st.markdown("Developer note: keys are read from `st.secrets['GEMINI_API_KEY']` or .env")

# --- Input mode & resume text ---
st.subheader("Resume Input")
input_mode, resume_text = ui_components.input_mode_widget()

if not resume_text:
    st.info("Paste your resume text or upload a .pdf/.docx/.txt file to begin.")
    st.stop()

# --- Run evaluation ---
if st.button("Evaluate Resume"):
    with st.spinner("Sending to Gemini for evaluation..."):
        domain_cfg = domain_config.DOMAINS.get(domain)
        if domain_cfg is None:
            st.error("Selected domain not recognized.")
            st.stop()

        # Call Gemini evaluation
        try:
            result = client.evaluate_resume(resume_text=resume_text, domain_config=domain_cfg, weights=weights)
        except Exception as e:
            st.error(f"Evaluation failed: {e}")
            st.stop()

    # --- Visualization & UI ---
    left, right = st.columns([2, 1])
    with left:
        st.subheader("Score Breakdown")
        # radar and bar charts
        ui_components.plot_score_charts(result["scores"], weights)
        # overall score & tier
        overall_score = scorer.compute_weighted_score(result["scores"], weights)
        tier = ui_components.grade_from_score(overall_score)
        st.metric("Overall Score", f"{overall_score:.1f}/100", delta=None)
        st.write(f"Tier: **{tier}**")
        st.markdown("### Summary")
        st.write(result.get("summary", "No summary returned."))

        # Rewriting assistant for weakest section
        weakest = min(result["scores"].items(), key=lambda kv: kv[1])[0]
        st.markdown(f"### Improve: {weakest}")
        st.write(result["justifications"].get(weakest, ""))
        if st.button(f"One-click rewrite suggestions for {weakest}"):
            with st.spinner("Requesting rewrite from Gemini..."):
                rewrite = client.rewrite_section(section_name=weakest,
                                                 section_text=result.get("section_texts", {}).get(weakest, ""),
                                                 domain_config=domain_cfg)
                st.markdown("**Before**")
                st.code(result.get("section_texts", {}).get(weakest, ""))
                st.markdown("**After**")
                st.code(rewrite.get("rewritten", ""))
                # store version
                st.session_state.setdefault("history", []).append({"resume": resume_text, "score": overall_score})

    with right:
        st.subheader("Detailed Per-Category Feedback")
        for k, v in result["scores"].items():
            st.markdown(f"**{k}** — {v}/100")
            st.write(result["justifications"].get(k, ""))
            st.markdown(f"*Improvement tip:* {result['tips'].get(k, '')}")

        st.markdown("---")
        st.subheader("Top missing keywords")
        st.write(", ".join(result.get("missing_keywords", [])))

        # ATS match
        if job_desc:
            st.markdown("---")
            st.subheader("ATS Keyword Match")
            overlap, missing = ui_components.ats_keyword_match(resume_text, job_desc)
            st.write(f"Matched keywords: {', '.join(sorted(overlap)) if overlap else 'None'}")
            st.write(f"Missing keywords: {', '.join(sorted(missing)) if missing else 'None'}")

        # Downloadable report
        st.markdown("---")
        st.subheader("Export")
        md_report = report_generator.generate_markdown_report(
            resume_text=resume_text,
            domain=domain,
            weights=weights,
            result=result,
            overall_score=overall_score,
            tier=tier
        )
        st.download_button("Download Markdown report", data=md_report, file_name="resume_report.md")

        try:
            pdf_bytes = report_generator.generate_pdf_report(md_report)
            st.download_button("Download PDF report", data=pdf_bytes, file_name="resume_report.pdf")
        except Exception as e:
            st.info("PDF export unavailable (missing dependency or error). Markdown download provided.")

# --- Session history panel ---
if st.sidebar.checkbox("Show history", key="history_toggle"):
    st.sidebar.subheader("Session History")
    for i, entry in enumerate(st.session_state.get("history", [])[::-1], 1):
        st.sidebar.write(f"{i}. Score: {entry['score']:.1f}")
