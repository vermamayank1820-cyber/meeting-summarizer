import { ArrowRight, Sparkles } from "lucide-react";
import SuggestionChip from "./SuggestionChip";

export default function AiComposer({ onPrimaryAction, onSuggestion }) {
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
          <div className="min-h-[120px] rounded-[22px] border border-dashed border-slate-200 bg-stone-50/80 p-5 text-left text-lg font-medium text-slate-400">
            Ask about a meeting, paste a follow-up request, or upload a new recording to generate a fresh brief.
          </div>

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

            <button
              onClick={onPrimaryAction}
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-stone-950 px-5 py-3 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-stone-800"
            >
              Summarize meeting
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
