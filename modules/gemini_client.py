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
    model: str = "gpt-4o-mini"  # update to your available model if necessary
    temperature: float = 0.3
    max_retries: int = 3

    def __post_init__(self):
        """
        Configure the google generative client only if api_key is present.
        This avoids crashes when api_key is None during local dev without secrets.
        """
        self._genai = None
        if not self.api_key:
            # defer configuration until a key is provided or used
            return
        try:
            from google import generativeai as genai  # type: ignore
            genai.configure(api_key=self.api_key)
            self._genai = genai
        except Exception:
            # leave _genai None and raise later when call attempted
            self._genai = None

    def _ensure_client(self):
        if not self._genai:
            raise RuntimeError("Google Generative AI client not configured. Provide GEMINI_API_KEY via st.secrets or environment.")

    # ... rest of methods unchanged (copy from the original implementation) ...
    def _prompt_payload(self, resume_text: str, domain_config: Dict[str, Any], weights: Dict[str, float]):
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
        first = text.find("{")
        last = text.rfind("}")
        if first != -1 and last != -1 and last > first:
            candidate = text[first:last+1]
            candidate = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", candidate)
            return candidate
        raise ValueError("No JSON object found in response")

    def _call_model(self, prompt_system: str, prompt_user: str) -> str:
        self._ensure_client()
        attempt = 0
        while attempt < self.max_retries:
            try:
                resp = self._genai.generate_text(
                    model=self.model,
                    prompt=f"{prompt_system}\n\n{prompt_user}",
                    temperature=self.temperature,
                    max_output_tokens=1500,
                )
                text = getattr(resp, "text", None) or resp.get("output", {}).get("text", "") or str(resp)
                return text
            except Exception:
                attempt += 1
                time.sleep(2 ** attempt)
                if attempt >= self.max_retries:
                    raise
        raise RuntimeError("Failed to call Gemini model after retries")

    def evaluate_resume(self, resume_text: str, domain_config: Dict[str, Any], weights: Dict[str, float]) -> Dict[str, Any]:
        system, user = self._prompt_payload(resume_text, domain_config, weights)
        raw = self._call_model(system, user)
        try:
            parsed = json.loads(raw)
        except Exception:
            repaired = self._repair_json(raw)
            parsed = json.loads(repaired)
        parsed.setdefault("scores", {})
        parsed.setdefault("justifications", {})
        parsed.setdefault("tips", {})
        parsed.setdefault("summary", "")
        parsed.setdefault("missing_keywords", [])
        parsed.setdefault("rewrites", {})
        parsed.setdefault("section_texts", {})
        return parsed

    def rewrite_section(self, section_name: str, section_text: str, domain_config: Dict[str, Any]) -> Dict[str, str]:
        system = f"You are a resume editor. Output JSON only: {{'rewritten':'...' }}.\nDomain config: {domain_config}"
        user = f"Rewrite the following section for clarity and impact: {section_name}\n\n{section_text}\n\nReturn 3 bullet-style rewritten lines in a single string separated by '\\n'."
        raw = self._call_model(system, user)
        try:
            parsed = json.loads(raw)
        except Exception:
            repaired = self._repair_json(raw)
            parsed = json.loads(repaired)
        return parsed
