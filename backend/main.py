from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from guardrails.classifier import Guardrail
from guardrails.sanitizer import sanitize_document
from guardrails.config import DEFAULTS

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "guardrail_tfidf.joblib"

app = FastAPI(
    title="Multilingual NLP Prompt Injection Security API",
    version="1.0.0",
    description="API for the project's local-first prompt-injection guardrails demo.",
)

origins = os.getenv("FRONTEND_ORIGIN", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

_guardrail: Guardrail | None = None

def get_guardrail() -> Guardrail:
    global _guardrail
    if _guardrail is None:
        if not MODEL_PATH.exists():
            raise RuntimeError(f"Trained model missing at {MODEL_PATH}")
        _guardrail = Guardrail(model_path=str(MODEL_PATH))
    return _guardrail


class InspectRequest(BaseModel):
    text: str = Field(min_length=1, max_length=12000)
    mode: Literal["protected", "baseline"] = "protected"


@app.get("/")
def root():
    return {"name": "Multilingual NLP Prompt Injection Security API", "status": "online", "docs": "/docs"}


@app.get("/health")
def health():
    try:
        model_ready = MODEL_PATH.exists()
        get_guardrail()
        return {"status": "ok", "model_loaded": model_ready}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Model unavailable: {exc}")


@app.post("/api/inspect")
def inspect(payload: InspectRequest):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Please enter text to inspect.")

    if payload.mode == "baseline":
        # Baseline is intentionally an unguarded pass-through demonstration.
        # No tools are executed and no external action is performed.
        return {
            "mode": "baseline",
            "decision": "UNPROTECTED",
            "risk": "NOT_CHECKED",
            "injection_probability": None,
            "reason_category": "GUARDRAILS_DISABLED_FOR_BASELINE",
            "explanation": "Baseline mode passes the supplied content through without applying the project's guardrails. No action is executed by this endpoint.",
            "safe_text": text,
            "quarantined_count": 0,
            "quarantined_categories": [],
        }

    guard = get_guardrail()
    try:
        sanitized = sanitize_document(text)
        safe_text = sanitized.get("safe_text", "")
        if sanitized.get("quarantined_count", 0) and not sanitized.get("has_safe_remainder"):
            inspection = {
                "decision": "BLOCK",
                "risk": "HIGH",
                "reason_category": "NO_SAFE_REMAINDER",
                "explanation": "Suspicious content was quarantined and no sufficiently safe remainder was retained.",
                "injection_probability": None,
            }
            safe_text = ""
        elif safe_text.strip():
            inspection = guard.inspect_untrusted_content(safe_text, DEFAULTS)
        else:
            inspection = {
                "decision": "BLOCK",
                "risk": "HIGH",
                "reason_category": "EMPTY_AFTER_SANITIZATION",
                "explanation": "No content remained after sanitization.",
                "injection_probability": None,
            }
        decision = "SANITIZE" if sanitized.get("quarantined_count", 0) and inspection.get("decision") == "ALLOW" else inspection.get("decision", "ESCALATE")
        return {
            "mode": "protected",
            "decision": decision,
            "risk": inspection.get("risk", "MEDIUM"),
            "injection_probability": inspection.get("injection_probability"),
            "reason_category": inspection.get("reason_category"),
            "explanation": inspection.get("explanation") or "The project's guardrail inspection completed.",
            "safe_text": safe_text,
            "quarantined_count": sanitized.get("quarantined_count", 0),
            "quarantined_categories": sanitized.get("categories", []),
            "retained_words": sanitized.get("retained_words", 0),
        }
    except Exception as exc:
        # Fail closed: never treat a failed inspection as approved.
        return {
            "mode": "protected",
            "decision": "ESCALATE",
            "risk": "MEDIUM",
            "injection_probability": None,
            "reason_category": "INSPECTION_ERROR",
            "explanation": f"Inspection could not complete; content was not cleared ({type(exc).__name__}).",
            "safe_text": "",
            "quarantined_count": 0,
            "quarantined_categories": [],
        }
