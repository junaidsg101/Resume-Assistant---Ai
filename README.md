# AI Resume Assistant

A production-quality Streamlit app to evaluate, score, and improve resumes with domain-specific guidance powered by Google Gemini.

---

## Purpose
AI Resume Assistant helps job seekers, researchers, and recruiters evaluate resumes across 10 career domains with a weighted scoring breakdown, domain-specific suggestions, ATS keyword matching, and downloadable reports.

---

## Architecture (text diagram)

app.py (Streamlit)
├─ modules/
│  ├─ domain_config.py        (domain definitions & keywords)
│  ├─ file_parser.py          (PDF/DOCX/TXT parsing)
│  ├─ gemini_client.py        (Gemini prompts, JSON enforcement)
│  ├─ scorer.py               (weight normalization & aggregation)
│  ├─ ui_components.py        (widgets, charts, ATS)
│  └─ report_generator.py     (Markdown & PDF export)

---

## Domains (10)
| # | Domain | Category |
|---|--------|----------|
| 1 | Computer Science & Software Engineering | Core CS |
| 2 | Data Science & Data Analytics | Data/AI |
| 3 | Machine Learning Engineering | AI |
| 4 | Generative AI & LLM / Prompt Engineering | AI |
| 5 | Agentic AI & Autonomous Systems | AI |
| 6 | Computer Vision & Multimodal AI | AI |
| 7 | Robotics & Physical AI (Embedded Intelligence) | AI |
| 8 | Cybersecurity & AI-Driven Threat Intelligence | Core CS |
| 9 | Cloud Computing, DevOps & MLOps | Core CS |
| 10 | Blockchain, Web3 & Quantum Computing | Core CS |

(See modules/domain_config.py for skill/tool/cert lists used for scoring.)

---

## Features
- Domain-specific resume scoring across 7 categories that sum to 100%.
- Adjustable weights (sliders) that auto-normalize.
- Strict JSON Gemini prompts for reliable parsing.
- Radar & horizontal bar charts (Plotly).
- ATS keyword matching against a pasted job description.
- Downloadable Markdown and PDF reports.
- One-click section rewrite assistant.
- Session history to compare versions.
- Recruiter vs Candidate views.
- Light/dark friendly theme (Streamlit config).

---

## Local setup
1. Clone the repository.
2. Create and activate a Python virtual environment.
3. pip install -r requirements.txt
4. Create a `.env` file with: