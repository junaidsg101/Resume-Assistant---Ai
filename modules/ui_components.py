"""
ui_components.py - reusable Streamlit widgets and plotting helpers.
"""
from typing import Dict, Tuple, List
import streamlit as st
from modules import domain_config as dc, scorer
import plotly.graph_objects as go
import difflib
import re

CATEGORIES = list(scorer.DEFAULT_WEIGHTS.keys())

def domain_selector(domains: dict) -> str:
    """
    Show a selectbox of the 10 domains.
    """
    options = list(domains.keys())
    return st.selectbox("Select career domain", options)

def input_mode_widget() -> Tuple[str, str]:
    """
    Allow user to choose Paste or Upload modes. Returns (mode, text).
    """
    mode = st.radio("Input Mode", ["Paste/Write Mode", "Upload Mode"], index=0)
    if mode == "Paste/Write Mode":
        text = st.text_area("Paste or type resume text", height=300)
        return mode, text.strip()
    else:
        uploaded = st.file_uploader("Upload resume (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])
        if uploaded:
            from modules.file_parser import parse_uploaded_file
            text, err = parse_uploaded_file(uploaded)
            if err:
                st.error(f"File error: {err}")
                return mode, ""
            if not text.strip():
                st.error("Parsed file contained no text. It may be scanned or image-only.")
            return mode, text.strip()
        return mode, ""

def _get_session_weights():
    if "weights" not in st.session_state:
        st.session_state["weights"] = scorer.DEFAULT_WEIGHTS.copy()
        st.session_state["_prev_weights"] = st.session_state["weights"].copy()
    return st.session_state["weights"]

def weight_sliders() -> Dict[str, float]:
    """
    Display sliders for each category and auto-normalize when one changes.
    Returns normalized weights summing to 100.
    """
    weights = _get_session_weights()
    cols = st.columns(1)
    changed_key = None
    for k in CATEGORIES:
        key = f"w_{k}"
        if key not in st.session_state:
            st.session_state[key] = float(weights.get(k, 0.0))
        # slider with on_change handler that notes which key changed
        def _mark_change(k=k, key=key):
            st.session_state["_last_changed"] = k
        st.slider(k, min_value=0.0, max_value=100.0, value=st.session_state[key], key=key, on_change=_mark_change)
    # perform normalization if any change
    if "_last_changed" in st.session_state:
        changed = st.session_state.pop("_last_changed")
        # gather current
        current = {k: float(st.session_state[f"w_{k}"]) for k in CATEGORIES}
        total = sum(current.values())
        changed_val = current[changed]
        others_total = total - changed_val
        target_others = 100.0 - changed_val
        if target_others < 0:
            # changed value > 100, clamp
            changed_val = 100.0
            current[changed] = changed_val
            target_others = 0.0
            others_total = 0.0
        if others_total <= 0 and target_others > 0:
            # distribute equally
            per = target_others / (len(CATEGORIES) - 1)
            for k in CATEGORIES:
                if k != changed:
                    current[k] = per
        elif others_total > 0:
            factor = target_others / others_total if others_total > 0 else 0
            for k in CATEGORIES:
                if k != changed:
                    current[k] = max(0.0, current[k] * factor)
        # update session and round
        for k, v in current.items():
            st.session_state[f"w_{k}"] = round(v, 2)
        # final normalization fix (tiny rounding issues)
        final = {k: float(st.session_state[f"w_{k}"]) for k in CATEGORIES}
        final = scorer.normalize_weights(final)
        for k, v in final.items():
            st.session_state[f"w_{k}"] = v
        st.session_state["weights"] = final
    # return current weights
    if "weights" not in st.session_state:
        st.session_state["weights"] = scorer.normalize_weights({k: float(st.session_state[f"w_{k}"]) for k in CATEGORIES})
    return st.session_state["weights"]

def plot_score_charts(scores: Dict[str, float], weights: Dict[str, float]) -> None:
    """
    Plot radar + horizontal bar charts using Plotly.
    """
    # ensure order
    categories = list(weights.keys())
    values = [scores.get(k, 0) for k in categories]

    # Radar chart
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]],
                                  fill="toself", name="Scores"))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Horizontal bar
    st.plotly_chart(_bar_figure(categories, values), use_container_width=True)

def _bar_figure(categories: List[str], values: List[float]):
    fig = go.Figure(go.Bar(x=values, y=categories, orientation="h", marker_color="rgba(50,150,255,0.6)"))
    fig.update_layout(xaxis_title="Score (0-100)", height=350)
    return fig

def grade_from_score(score: float) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Strong"
    if score >= 60:
        return "Competitive"
    return "Entry / Needs Improvement"

def ats_keyword_match(resume_text: str, job_description: str) -> Tuple[set, set]:
    """
    Lightweight ATS keyword overlap extraction.
    Returns (overlap, missing) sets of keywords.
    """
    def tokenize(text: str):
        tokens = re.findall(r"[A-Za-z0-9\+\#\-\_]+", text.lower())
        stop = {"and", "or", "with", "the", "a", "an", "to", "for", "of", "in", "on", "using"}
        return {t for t in tokens if t not in stop and len(t) > 1}

    resume_tokens = tokenize(resume_text)
    job_tokens = tokenize(job_description)
    overlap = resume_tokens & job_tokens
    missing = job_tokens - resume_tokens
    # filter common short tokens
    return overlap, missing

def show_improvement_diff(before: str, after: str):
    """
    Show a simple unified diff of two strings.
    """
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    diff = difflib.unified_diff(before_lines, after_lines, lineterm="")
    st.code("\n".join(diff))