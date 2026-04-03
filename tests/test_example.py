"""
Example Test Case
-----------------
Tests the full pipeline using a synthetic short transcript (no real audio file needed).
Useful for verifying your setup and API key before using real recordings.

Run: python tests/test_example.py
"""
import sys
import json
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.cleaning_agent import CleaningAgent, _regex_clean
from agents.storage_agent import StorageAgent
from utils.logger import get_logger

logger = get_logger("TestExample")

SAMPLE_TRANSCRIPT = """
Um, so let's uh get started. Today's meeting is about the Q3 product roadmap.
Okay so first, uh, Sarah mentioned that we need to finalize the API design by end of month.
Like, John agreed and said he would um own that deliverable.
So the decision was made to, you know, use GraphQL over REST for the new endpoints.
Mike raised a risk that uh the backend team is understaffed and this could delay delivery.
So basically the next steps are: John to complete API spec by July 15th,
Sarah to review and sign off by July 18th, and Mike to hire two contractors.
"""


def test_regex_cleaning():
    logger.info("Test 1: Regex cleaning")
    cleaned = _regex_clean(SAMPLE_TRANSCRIPT)
    assert "um" not in cleaned.lower() or "summary" in cleaned.lower(), "Filler words should be removed"
    assert len(cleaned) > 50, "Cleaned transcript should have meaningful content"
    logger.info(f"  ✓ Cleaned transcript ({len(cleaned)} chars)")
    logger.info(f"  Preview: {cleaned[:200]}…")
    return cleaned


def test_cleaning_agent_no_llm():
    logger.info("Test 2: CleaningAgent (regex only, no LLM)")
    agent = CleaningAgent(use_llm=False)
    context = {"raw_transcript": SAMPLE_TRANSCRIPT}
    result = agent.run(context)
    assert "clean_transcript" in result
    assert len(result["clean_transcript"]) > 0
    logger.info(f"  ✓ Cleaning done ({len(result['clean_transcript'])} chars)")
    return result


def test_storage_agent():
    logger.info("Test 3: StorageAgent")
    agent = StorageAgent()

    # Build a fake pipeline context
    context = {
        "file_path": "/recordings/test_meeting.mp4",
        "meeting_id": "test001",
        "raw_transcript": SAMPLE_TRANSCRIPT,
        "clean_transcript": _regex_clean(SAMPLE_TRANSCRIPT),
        "duration_seconds": 600.0,
        "summary_style": "executive",
        "summary": {
            "meeting_overview": "Q3 product roadmap planning meeting focusing on API design decisions.",
            "key_discussion_points": [
                "API design strategy (GraphQL vs REST)",
                "Backend team capacity concerns",
            ],
            "decisions_taken": [
                "Use GraphQL over REST for new endpoints",
            ],
            "action_items": [
                {"task": "Complete API spec", "owner": "John", "deadline": "July 15", "priority": "High"},
                {"task": "Review and sign off API spec", "owner": "Sarah", "deadline": "July 18", "priority": "High"},
                {"task": "Hire two contractors", "owner": "Mike", "deadline": "TBD", "priority": "Medium"},
            ],
            "risks_and_blockers": [
                "Backend team understaffed — may delay API delivery",
            ],
            "next_steps": [
                "John to deliver API spec by July 15",
                "Sarah review by July 18",
                "Mike to start contractor recruitment",
            ],
            "sentiment": "neutral",
            "key_metrics_mentioned": [],
        },
        "summary_markdown": "## Meeting Overview\nQ3 roadmap planning.\n",
    }

    result = agent.run(context)
    assert "output_json_path" in result
    assert Path(result["output_json_path"]).exists()
    logger.info(f"  ✓ JSON saved: {result['output_json_path']}")
    logger.info(f"  ✓ MD saved:   {result['output_md_path']}")

    # Verify we can list and retrieve
    meetings = StorageAgent.list_meetings()
    assert any(m["id"] == "test001" for m in meetings), "Meeting should appear in list"
    logger.info(f"  ✓ Found in meeting list ({len(meetings)} total meetings)")

    return result


def test_full_pipeline_no_audio():
    """
    Tests the full pipeline stack (cleaning → summarization → storage)
    without requiring an audio file. Skips transcription.
    Requires a valid LLM API key.
    """
    from utils.config import ANTHROPIC_API_KEY, OPENAI_API_KEY

    if not ANTHROPIC_API_KEY and not OPENAI_API_KEY:
        logger.warning("Skipping LLM test — no API key configured in .env")
        return

    logger.info("Test 4: Full pipeline (no audio, LLM enabled)")
    from agents.cleaning_agent import CleaningAgent
    from agents.summarization_agent import SummarizationAgent
    from agents.storage_agent import StorageAgent

    context = {
        "file_path": "/recordings/llm_test.mp4",
        "meeting_id": "llmtest01",
        "raw_transcript": SAMPLE_TRANSCRIPT,
        "summary_style": "executive",
    }

    context = CleaningAgent(use_llm=True).run(context)
    logger.info(f"  ✓ Cleaning done")

    context = SummarizationAgent().run(context)
    logger.info(f"  ✓ Summary generated — {len(context['summary'].get('action_items', []))} action items")

    context = StorageAgent().run(context)
    logger.info(f"  ✓ Stored at: {context['output_json_path']}")

    print("\n📄 SUMMARY MARKDOWN PREVIEW:")
    print("─" * 60)
    print(context.get("summary_markdown", "")[:1000])


if __name__ == "__main__":
    print("\n" + "═" * 60)
    print("   Meeting Summarizer — Test Suite")
    print("═" * 60 + "\n")

    test_regex_cleaning()
    test_cleaning_agent_no_llm()
    test_storage_agent()
    test_full_pipeline_no_audio()

    print("\n" + "═" * 60)
    print("   All tests passed ✅")
    print("═" * 60 + "\n")
