import {
  ArrowUpRight,
  CalendarClock,
  CheckCheck,
  FileText,
  Flag,
  MessageSquareText,
} from "lucide-react";
import { formatDate, formatDuration, safeJsonParse, sentenceCase } from "../lib/formatters";
import ActionItemsBoard from "./ActionItemsBoard";
import SectionCard from "./SectionCard";
import StatusPill from "./StatusPill";

function ListBlock({ items, icon: Icon, emptyLabel }) {
  if (!items?.length) {
    return <div className="text-sm text-slate-500">{emptyLabel}</div>;
  }

  return (
    <div className="space-y-3">
      {items.map((item, index) => (
        <div key={`${index}-${typeof item === "string" ? item : JSON.stringify(item)}`} className="flex gap-3 rounded-[20px] bg-stone-50 px-4 py-4">
          <div className="mt-0.5 rounded-full bg-white p-2 text-slate-600 shadow-sm">
            <Icon size={14} />
          </div>
          <div className="min-w-0 text-sm leading-6 text-slate-700">
            {typeof item === "string" ? (
              item
            ) : (
              <>
                <div className="font-semibold text-slate-950">
                  {item.topic || item.decision || item.item || item.step || "Detail"}
                </div>
                <div className="mt-1">
                  {item.details || item.rationale || item.impact || item.timeline || item.mitigation || ""}
                </div>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ResultsView({ meeting }) {
  if (!meeting) return null;

  const summary = meeting.summary || {};
  const metrics = safeJsonParse(summary.key_metrics_mentioned, []);

  return (
    <div className="space-y-6">
      <SectionCard
        eyebrow="Result"
        title={meeting.filename}
        action={
          <div className="flex flex-wrap items-center gap-2">
            <StatusPill status={meeting.status} />
            <div className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold text-slate-700">
              {sentenceCase(meeting.summary_style || "executive")}
            </div>
          </div>
        }
      >
        <div className="grid gap-4 md:grid-cols-4">
          {[
            { label: "Created", value: formatDate(meeting.created_at), icon: CalendarClock },
            { label: "Audio", value: formatDuration(meeting.duration_secs), icon: MessageSquareText },
            { label: "Actions", value: `${safeJsonParse(meeting.action_items, []).length}`, icon: CheckCheck },
            { label: "Sentiment", value: sentenceCase(meeting.sentiment || "neutral"), icon: Flag },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.label} className="rounded-[22px] border hairline bg-stone-50/80 p-4">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  <Icon size={14} />
                  {item.label}
                </div>
                <div className="mt-3 text-base font-bold text-slate-950">{item.value}</div>
              </div>
            );
          })}
        </div>
      </SectionCard>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-6">
          <SectionCard eyebrow="Summary" title="Executive overview">
            <p className="text-[15px] leading-8 text-slate-700">
              {summary.meeting_overview || meeting.overview || "Summary will appear here once the pipeline finishes."}
            </p>
          </SectionCard>

          <SectionCard eyebrow="Main focus" title="Action items">
            <ActionItemsBoard
              meetings={[
                {
                  filename: "This meeting",
                  action_items: meeting.action_items,
                },
              ]}
            />
          </SectionCard>

          <div className="grid gap-6 md:grid-cols-2">
            <SectionCard eyebrow="Discussion" title="Key points">
              <ListBlock
                items={summary.key_discussion_points}
                icon={ArrowUpRight}
                emptyLabel="No key points captured."
              />
            </SectionCard>

            <SectionCard eyebrow="Decision log" title="Decisions taken">
              <ListBlock
                items={summary.decisions_taken}
                icon={CheckCheck}
                emptyLabel="No explicit decisions were extracted."
              />
            </SectionCard>
          </div>
        </div>

        <div className="space-y-6">
          <SectionCard eyebrow="Signals" title="Risks and blockers">
            <ListBlock
              items={summary.risks_and_blockers}
              icon={Flag}
              emptyLabel="No risks or blockers were identified."
            />
          </SectionCard>

          <SectionCard eyebrow="Follow-through" title="Next steps">
            <ListBlock
              items={summary.next_steps}
              icon={ArrowUpRight}
              emptyLabel="No next steps recorded."
            />
          </SectionCard>

          <SectionCard eyebrow="Source" title="Transcript preview">
            <div className="rounded-[24px] bg-stone-950 p-5 text-sm leading-7 text-stone-200">
              <div className="mb-4 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">
                <FileText size={14} />
                Clean transcript
              </div>
              <div className="max-h-[360px] overflow-y-auto whitespace-pre-wrap">
                {(meeting.clean_transcript || meeting.raw_transcript || "Transcript unavailable.").slice(0, 3600)}
              </div>
            </div>
          </SectionCard>

          <SectionCard eyebrow="Metrics" title="Referenced numbers">
            {metrics.length ? (
              <div className="flex flex-wrap gap-2">
                {metrics.map((metric, index) => (
                  <div key={`${metric}-${index}`} className="rounded-full border border-slate-200 bg-stone-50 px-3 py-2 text-sm font-medium text-slate-700">
                    {typeof metric === "string" ? metric : JSON.stringify(metric)}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-slate-500">No key metrics were called out in this meeting.</div>
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
