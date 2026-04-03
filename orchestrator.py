"""
Orchestrator
------------
Central pipeline coordinator. Runs agents in sequence and manages shared context.
Can be invoked:
  - By WatcherAgent (automatic, from file system events)
  - By FastAPI (manual upload endpoint)
  - From the command line (python orchestrator.py <file_path>)
"""
import time
import uuid
from pathlib import Path
from typing import Any

from agents.transcription_agent import TranscriptionAgent
from agents.cleaning_agent import CleaningAgent
from agents.summarization_agent import SummarizationAgent
from agents.storage_agent import StorageAgent
from utils.logger import get_logger
from utils.config import DEFAULT_SUMMARY_STYLE

logger = get_logger("Orchestrator")


class PipelineError(Exception):
    """Raised when the pipeline fails at a specific stage."""
    def __init__(self, stage: str, original: Exception):
        self.stage = stage
        self.original = original
        super().__init__(f"Pipeline failed at [{stage}]: {original}")


class Orchestrator:
    """
    Runs the full meeting processing pipeline:
    TranscriptionAgent → CleaningAgent → SummarizationAgent → StorageAgent
    """

    def __init__(self, use_llm_cleaning: bool = True):
        self.transcription_agent = TranscriptionAgent()
        self.cleaning_agent = CleaningAgent(use_llm=use_llm_cleaning)
        self.summarization_agent = SummarizationAgent()
        self.storage_agent = StorageAgent()

    def process(self, file_path: Path, summary_style: str = DEFAULT_SUMMARY_STYLE) -> dict[str, Any]:
        """
        Full pipeline for a recording file.

        Args:
            file_path: Path to the audio/video recording
            summary_style: "executive" or "detailed"

        Returns:
            Final pipeline context dict with all outputs

        Raises:
            PipelineError: If any agent fails
        """
        meeting_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        context: dict[str, Any] = {
            "file_path": str(file_path),
            "meeting_id": meeting_id,
            "summary_style": summary_style,
            "status": "processing",
        }

        logger.info(f"━━━ Pipeline START [{meeting_id}] — {file_path.name} ━━━")

        stages = [
            ("Transcription", self.transcription_agent.run),
            ("Cleaning",      self.cleaning_agent.run),
            ("Summarization", self.summarization_agent.run),
            ("Storage",       self.storage_agent.run),
        ]

        for stage_name, agent_fn in stages:
            stage_start = time.time()
            logger.info(f"[{meeting_id}] ▶ Starting {stage_name}…")
            try:
                context = agent_fn(context)
                elapsed = time.time() - stage_start
                logger.info(f"[{meeting_id}] ✓ {stage_name} done ({elapsed:.1f}s)")
            except Exception as exc:
                logger.error(f"[{meeting_id}] ✗ {stage_name} FAILED: {exc}", exc_info=True)
                context["status"] = f"failed_{stage_name.lower()}"
                raise PipelineError(stage_name, exc)

        total = time.time() - start_time
        context["status"] = "completed"
        context["total_processing_seconds"] = round(total, 1)

        logger.info(f"━━━ Pipeline COMPLETE [{meeting_id}] in {total:.1f}s ━━━")
        logger.info(f"    JSON:     {context.get('output_json_path', 'N/A')}")
        logger.info(f"    Markdown: {context.get('output_md_path', 'N/A')}")

        return context


# ─── CLI entry point ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py <path_to_recording> [executive|detailed]")
        sys.exit(1)

    path = Path(sys.argv[1])
    style = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SUMMARY_STYLE

    orchestrator = Orchestrator()
    try:
        result = orchestrator.process(path, style)
        print(f"\n✅ Done! Summary saved to:\n  {result.get('output_md_path')}")
    except PipelineError as e:
        print(f"\n❌ Failed at stage [{e.stage}]: {e.original}")
        sys.exit(1)
