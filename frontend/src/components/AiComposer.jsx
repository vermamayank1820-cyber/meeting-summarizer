import { ArrowRight, MessageSquareText, Sparkles, Upload } from "lucide-react";
import SuggestionChip from "./SuggestionChip";

export default function AiComposer({
  prompt,
  onPromptChange,
  onAsk,
  onUpload,
  onSuggestion,
  answer,
  answerContextLabel,
  isAnswering,
  error,
  canAsk,
}) {
  const suggestions = [
    "Summarize the latest leadership sync",
    "Find all overdue action items",
    "Show decisions made this week",
  ];

  return (
    <div className="relative overflow-hidden rounded-[32px] border hairline bg-[radial-gradient(circle_at_top_left,_rgba(251,191,36,0.18),_transparent_28%),linear-gradient(135deg,_#ffffff,_#f8fafc_45%,_#ecfeff)] p-6 shadow-panel md:p-8">
      <div className="absolute -right-10 top-5 h-24 w-24 rounded-full bg-amber-200/40 blur-3xl" />
      <div className="absolute -left-12 bottom-0 h-36 w-36 rounded-full bg-cyan-200/30 blur-3xl" />

      <div className="relative mx-auto max-w-4xl">
        <div className="inline-flex items-center gap-2 rounded-full border border-amber-200 bg-white/80 px-3 py-1 text-xs font-semibold text-amber-900">
          <Sparkles size={14} />
          AI-first workspace
        </div>

        <h2 className="mt-5 text-3xl font-extrabold tracking-[-0.05em] text-slate-950 md:text-5xl">
          Ask the system what matters. Then act on it.
        </h2>
        <p className="mt-4 max-w-3xl text-base leading-7 text-slate-600 md:text-lg">
          Large-input search, upload, and action orchestration in one place. The UI keeps focus on the next useful move instead of the raw transcript.
        </p>

        <div className="mt-8 rounded-[28px] border border-white/80 bg-white/80 p-4 shadow-soft md:p-5">
          <textarea
            value={prompt}
            onChange={(event) => onPromptChange(event.target.value)}
            placeholder="Ask about a meeting, decisions, or follow-ups. If the topic is outside the meeting, the assistant will say so clearly."
            className="min-h-[140px] w-full resize-none rounded-[22px] border border-dashed border-slate-200 bg-stone-50/80 p-5 text-left text-lg font-medium text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-amber-300 focus:bg-white"
          />

          <div className="mt-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex flex-wrap gap-2">
              {suggestions.map((label) => (
                <SuggestionChip
                  key={label}
                  label={label}
                  onClick={() => onSuggestion(label)}
                />
              ))}
            </div>

            <div className="flex flex-col gap-3 sm:flex-row">
              <button
                onClick={onUpload}
                className="inline-flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5 hover:border-slate-300 hover:bg-slate-50"
              >
                <Upload size={16} />
                Upload recording
              </button>

              <button
                onClick={() => onAsk(prompt)}
                disabled={!canAsk || !prompt.trim() || isAnswering}
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-stone-950 px-5 py-3 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <MessageSquareText size={16} />
                {isAnswering ? "Thinking..." : "Ask meeting"}
                {!isAnswering ? <ArrowRight size={16} /> : null}
              </button>
            </div>
          </div>

          {!canAsk ? (
            <div className="mt-4 rounded-[22px] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              Process at least one meeting first, then the assistant can answer questions grounded in that transcript.
            </div>
          ) : null}

          {error ? (
            <div className="mt-4 rounded-[22px] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
              {error}
            </div>
          ) : null}

          {answer ? (
            <div className="mt-4 rounded-[24px] border border-slate-200 bg-white px-5 py-4">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Answer {answerContextLabel ? `from ${answerContextLabel}` : ""}
              </div>
              <div className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">
                {answer}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
