"""
gemini_client.py - Thin client wrapper for Google Gemini (google-generativeai).
Ensures strict JSON output from the model and includes retry & JSON repair logic.
"""
from typing import Dict, Any, Optional
import json
import re
import time
from dataclasses import dataclass

@dataclass
class GeminiClient:
    api_key: Optional[str] = None
    model: str = "gpt-4o-mini"  # update to your available model
    temperature: float = 0.3
    max_retries: int = 3

    def __post_init__(self):
        # Lazy import to avoid breaking offline linting
        try:
            from google import generativeai as genai  # type: ignore
            genai.configure(api_key=self.api_key)
            self._genai = genai
        except Exception:
            self._genai = None

    def _prompt_payload(self, resume_text: str, domain_config: Dict[str, Any], weights: Dict[str, float]):
        """
        Build a system + user prompt that enforces pure JSON output.
        """
        system = (
            "You are a professional resume evaluator. Output MUST be valid JSON with the exact schema:\n"
            "{\n"
            '  "scores": {"Category Name": number, ...},\n'
            '  "justifications": {"Category Name": "short justification", ...},\n'
            '  "tips": {"Category Name": "1-2 line suggestion", ...},\n'
            '  "summary": "overall summary",\n'
            '  "missing_keywords": ["kw1", "kw2", ...],\n'
            '  "rewrites": {"Category Name": ["before bullet", "after bullet", ...]},\n'
            '  "section_texts": {"Category Name": "extracted text from resume (optional)"}\n'
            "}\n"
            "Respond with JSON only and nothing else."
        )
        user = {
            "resume_text": resume_text,
            "domain_config": domain_config,
            "weights": weights,
            "notes": "Scores should be integers 0-100. Keep justifications concise. Provide top 5 missing domain keywords and 3 rewritten bullets for the weakest category."
        }
        return system, json.dumps(user)

    def _repair_json(self, text: str) -> str:
        """
        Try to extract JSON object from text using braces heuristic.
        """
        # find the first { and last }
        first = text.find("{")
        last = text.rfind("}")
        if first != -1 and last != -1 and last > first:
            candidate = text[first:last+1]
            # remove control characters
            candidate = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", candidate)
            return candidate
        raise ValueError("No JSON object found in response")

    def _call_model(self, prompt_system: str, prompt_user: str) -> str:
        """
        Call the generative model and return raw text.
        Includes retry logic.
        """
        if not self._genai:
            raise RuntimeError("Google Generative AI client not configured or missing.")
        attempt = 0
        while attempt < self.max_retries:
            try:
                # Using the modern client method: generate_text (may vary on version)
                resp = self._genai.generate_text(
                    model=self.model,
                    prompt=f"{prompt_system}\n\n{prompt_user}",
                    temperature=self.temperature,
                    max_output_tokens=1500,
                )
                # response content access may vary
                text = getattr(resp, "text", None) or resp.get("output", {}).get("text", "") or str(resp)
                return text
            except Exception as e:
                attempt += 1
                wait = 2 ** attempt
                time.sleep(wait)
                if attempt >= self.max_retries:
                    raise
        raise RuntimeError("Failed to call Gemini model after retries")

    def evaluate_resume(self, resume_text: str, domain_config: Dict[str, Any], weights: Dict[str, float]) -> Dict[str, Any]:
        """
        High-level method to evaluate resume. Returns parsed JSON dict.
        """
        system, user = self._prompt_payload(resume_text, domain_config, weights)
        raw = self._call_model(system, user)
        try:
            parsed = json.loads(raw)
        except Exception:
            # attempt to repair common issues
            try:
                repaired = self._repair_json(raw)
                parsed = json.loads(repaired)
            except Exception as e:
                raise ValueError(f"Failed to parse model JSON response: {e}\nRaw output:\n{raw}")
        # validation & defaults
        parsed.setdefault("scores", {})
        parsed.setdefault("justifications", {})
        parsed.setdefault("tips", {})
        parsed.setdefault("summary", "")
        parsed.setdefault("missing_keywords", [])
        parsed.setdefault("rewrites", {})
        parsed.setdefault("section_texts", {})
        return parsed

    def rewrite_section(self, section_name: str, section_text: str, domain_config: Dict[str, Any]) -> Dict[str, str]:
        """
        Ask Gemini to rewrite or rephrase a section. Returns a dict with 'rewritten'.
        """
        system = f"You are a resume editor. Output JSON only: {{'rewritten':'...' }}.\nDomain config: {domain_config}"
        user = f"Rewrite the following section for clarity and impact: {section_name}\n\n{section_text}\n\nReturn 3 bullet-style rewritten lines in a single string separated by '\\n'."
        raw = self._call_model(system, user)
        try:
            parsed = json.loads(raw)
        except Exception:
            try:
                repaired = self._repair_json(raw)
                parsed = json.loads(repaired)
            except Exception:
                parsed = {"rewritten": raw}
        return parsed