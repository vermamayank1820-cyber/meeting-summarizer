"""
Cleaning Agent
--------------
Takes a raw Whisper transcript and produces a clean, readable version by:
  - Removing filler words (um, uh, like, you know…)
  - Collapsing repeated phrases
  - Fixing run-on sentences and improving punctuation
  - Labelling speaker turns where detectable

Uses a regex-based fast pass first, then an optional LLM pass for fluency.

Pipeline context keys consumed: "raw_transcript"
Pipeline context keys produced: "clean_transcript"
"""
import re
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from utils.config import LLM_PROVIDER, ANTHROPIC_API_KEY, OPENAI_API_KEY, CLAUDE_MODEL, OPENAI_MODEL

logger = get_logger("CleaningAgent")

# Filler words to strip (whole-word match, case-insensitive)
_FILLERS = [
    r"\bum+\b", r"\buh+\b", r"\ber+\b", r"\bhmm+\b",
    r"\byou know\b", r"\blike\b(?=\s)", r"\bbasically\b",
    r"\bactually\b", r"\bliterally\b", r"\bsorta\b", r"\bkinda\b",
    r"\bright\?\s*", r"\bokay so\b", r"\bso so\b",
]
_FILLER_RE = re.compile("|".join(_FILLERS), re.IGNORECASE)

# Collapse 3+ repeated words: "yes yes yes" → "yes"
_REPEAT_RE = re.compile(r'\b(\w+)(\s+\1){2,}\b', re.IGNORECASE)

# Multiple spaces → single space
_SPACES_RE = re.compile(r' {2,}')

# Multiple punctuation marks
_MULTI_PUNCT_RE = re.compile(r'([.!?]){2,}')


def _regex_clean(text: str) -> str:
    text = _FILLER_RE.sub("", text)
    text = _REPEAT_RE.sub(r"\1", text)
    text = _SPACES_RE.sub(" ", text)
    text = _MULTI_PUNCT_RE.sub(r"\1", text)
    # Ensure sentences start with capital letter
    text = re.sub(r'(?<=[.!?])\s+([a-z])', lambda m: " " + m.group(1).upper(), text)
    return text.strip()


def _llm_clean(raw: str) -> str:
    """Optional LLM pass — makes the transcript fluent and coherent."""
    prompt = (
        "You are a professional transcript editor.\n"
        "Clean up the following meeting transcript:\n"
        "- Fix grammar, punctuation, and sentence structure\n"
        "- Remove any remaining filler words or repetition\n"
        "- Preserve all meaning and every speaker's intent\n"
        "- Do NOT add or invent any content\n"
        "- Output ONLY the cleaned transcript, no commentary\n\n"
        f"TRANSCRIPT:\n{raw}"
    )

    if LLM_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    elif LLM_PROVIDER == "openai" and OPENAI_API_KEY:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()

    else:
        logger.warning("No LLM API key configured — skipping LLM cleaning pass")
        return raw


class CleaningAgent:
    """Cleans and structures the raw transcript."""

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        raw = context.get("raw_transcript", "")
        if not raw:
            raise ValueError("No raw_transcript found in pipeline context")

        logger.info(f"Cleaning transcript ({len(raw)} chars)…")

        # Step 1: Fast regex pass
        cleaned = _regex_clean(raw)
        logger.debug(f"After regex clean: {len(cleaned)} chars")

        # Step 2: Optional LLM polish
        if self.use_llm:
            logger.info("Running LLM cleaning pass…")
            try:
                cleaned = _llm_clean(cleaned)
                logger.info(f"LLM cleaning done: {len(cleaned)} chars")
            except Exception as exc:
                logger.warning(f"LLM cleaning failed ({exc}) — using regex-cleaned transcript")

        context["clean_transcript"] = cleaned
        return context
