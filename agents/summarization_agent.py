"""
Summarization Agent
-------------------
Generates a structured, consulting-grade executive summary from a clean transcript.
Supports two summary styles:
  - "executive": concise, McKinsey/Bain-style briefing
  - "detailed": comprehensive with full action item tables

Pipeline context keys consumed: "clean_transcript", "summary_style" (optional)
Pipeline context keys produced: "summary" (dict), "summary_markdown" (str)
"""
import json
import re
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from utils.config import (
    LLM_PROVIDER, ANTHROPIC_API_KEY, OPENAI_API_KEY,
    CLAUDE_MODEL, OPENAI_MODEL, DEFAULT_SUMMARY_STYLE,
)

logger = get_logger("SummarizationAgent")

_EXECUTIVE_PROMPT = """You are an expert business analyst with experience at top-tier consulting firms (McKinsey, Bain, BCG).

Your task is to convert the meeting transcript below into a structured executive summary.

STRICT OUTPUT FORMAT (respond with valid JSON only, no markdown fences):
{{
  "meeting_overview": "2-3 sentence overview of the meeting purpose and outcome",
  "key_discussion_points": [
    "Point 1",
    "Point 2"
  ],
  "decisions_taken": [
    "Decision 1",
    "Decision 2"
  ],
  "action_items": [
    {{"task": "...", "owner": "...", "deadline": "..."}},
    {{"task": "...", "owner": "...", "deadline": "..."}}
  ],
  "risks_and_blockers": [
    "Risk/Blocker 1"
  ],
  "next_steps": [
    "Next Step 1"
  ],
  "sentiment": "positive | neutral | negative",
  "key_metrics_mentioned": []
}}

RULES:
- Be concise and professional. No filler or padding.
- Do NOT hallucinate or invent facts. Extract only from the transcript.
- If a field has no data, use an empty list [].
- For action_items, use "Unassigned" for owner and "TBD" for deadline if not stated.
- Highlight any risks or blockers explicitly mentioned.

TRANSCRIPT:
{transcript}"""

_DETAILED_PROMPT = """You are a senior business analyst. Create a detailed, comprehensive meeting summary from the transcript below.

STRICT OUTPUT FORMAT (respond with valid JSON only, no markdown fences):
{{
  "meeting_overview": "Detailed 4-5 sentence overview covering context, attendees, purpose, and outcome",
  "key_discussion_points": [
    {{"topic": "...", "details": "...", "stakeholder": "..."}}
  ],
  "decisions_taken": [
    {{"decision": "...", "rationale": "...", "made_by": "..."}}
  ],
  "action_items": [
    {{"task": "...", "owner": "...", "deadline": "...", "priority": "High|Medium|Low", "notes": "..."}}
  ],
  "risks_and_blockers": [
    {{"item": "...", "impact": "...", "mitigation": "..."}}
  ],
  "next_steps": [
    {{"step": "...", "timeline": "...", "responsible": "..."}}
  ],
  "open_questions": [],
  "sentiment": "positive | neutral | negative",
  "key_metrics_mentioned": [],
  "follow_up_meetings_suggested": []
}}

RULES:
- Capture every nuance from the transcript.
- Do NOT hallucinate. Only extract from the transcript.
- Be thorough but professional.

TRANSCRIPT:
{transcript}"""


def _call_llm(prompt: str) -> str:
    if LLM_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    elif LLM_PROVIDER == "openai" and OPENAI_API_KEY:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content.strip()

    else:
        raise RuntimeError(
            "No LLM API key configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file."
        )


def _parse_json_response(text: str) -> dict:
    """Robustly parse JSON from LLM response (strips markdown fences if present)."""
    # Strip markdown code fences
    text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text.strip())
    return json.loads(text)


def _summary_to_markdown(summary: dict, style: str) -> str:
    """Convert summary dict to clean Markdown for display."""
    lines = []
    lines.append(f"## Meeting Overview\n{summary.get('meeting_overview', 'N/A')}\n")

    lines.append("## Key Discussion Points")
    for item in summary.get("key_discussion_points", []):
        if isinstance(item, dict):
            lines.append(f"- **{item.get('topic', '')}**: {item.get('details', '')} *(Stakeholder: {item.get('stakeholder', 'N/A')})*")
        else:
            lines.append(f"- {item}")
    lines.append("")

    lines.append("## Decisions Taken")
    for item in summary.get("decisions_taken", []):
        if isinstance(item, dict):
            lines.append(f"- **{item.get('decision', '')}** — Rationale: {item.get('rationale', 'N/A')}")
        else:
            lines.append(f"- {item}")
    lines.append("")

    lines.append("## Action Items")
    lines.append("| Task | Owner | Deadline | Priority |")
    lines.append("|------|-------|----------|----------|")
    for ai in summary.get("action_items", []):
        if isinstance(ai, dict):
            lines.append(
                f"| {ai.get('task', '')} | {ai.get('owner', 'Unassigned')} "
                f"| {ai.get('deadline', 'TBD')} | {ai.get('priority', '—')} |"
            )
    lines.append("")

    lines.append("## Risks & Blockers")
    for item in summary.get("risks_and_blockers", []):
        if isinstance(item, dict):
            lines.append(f"- ⚠️ **{item.get('item', '')}** — Impact: {item.get('impact', 'N/A')}")
        else:
            lines.append(f"- ⚠️ {item}")
    lines.append("")

    lines.append("## Next Steps")
    for item in summary.get("next_steps", []):
        if isinstance(item, dict):
            lines.append(f"- {item.get('step', '')} *(By: {item.get('responsible', 'TBD')}, {item.get('timeline', '')})*")
        else:
            lines.append(f"- {item}")
    lines.append("")

    if summary.get("open_questions"):
        lines.append("## Open Questions")
        for q in summary["open_questions"]:
            lines.append(f"- ❓ {q}")
        lines.append("")

    sentiment = summary.get("sentiment", "neutral")
    emoji = {"positive": "🟢", "neutral": "🟡", "negative": "🔴"}.get(sentiment, "⚪")
    lines.append(f"**Meeting Sentiment:** {emoji} {sentiment.title()}")

    return "\n".join(lines)


class SummarizationAgent:
    """Generates a structured meeting summary using an LLM."""

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        transcript = context.get("clean_transcript", "")
        if not transcript:
            raise ValueError("No clean_transcript found in pipeline context")

        style = context.get("summary_style", DEFAULT_SUMMARY_STYLE)
        logger.info(f"Generating '{style}' summary for {len(transcript)} char transcript…")

        template = _EXECUTIVE_PROMPT if style == "executive" else _DETAILED_PROMPT
        prompt = template.format(transcript=transcript)

        raw_response = _call_llm(prompt)
        logger.debug(f"LLM raw response length: {len(raw_response)}")

        try:
            summary = _parse_json_response(raw_response)
        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse LLM response as JSON: {exc}")
            logger.debug(f"Raw response: {raw_response[:500]}")
            raise RuntimeError(f"Summarization JSON parse error: {exc}") from exc

        context["summary"] = summary
        context["summary_style"] = style
        context["summary_markdown"] = _summary_to_markdown(summary, style)

        logger.info(f"Summary generated — {len(summary.get('action_items', []))} action items, "
                    f"{len(summary.get('key_discussion_points', []))} discussion points")
        return context
