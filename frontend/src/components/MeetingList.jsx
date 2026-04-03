import { ArrowUpRight, Clock3 } from "lucide-react";
import { formatDate, formatDuration, safeJsonParse } from "../lib/formatters";
import StatusPill from "./StatusPill";

export default function MeetingList({ meetings, selectedMeetingId, onSelect }) {
  return (
    <div className="space-y-3">
      {meetings.map((meeting) => {
        const actionItems = safeJsonParse(meeting.action_items, []);

        return (
          <button
            key={meeting.id}
            onClick={() => onSelect(meeting.id)}
            className={`w-full rounded-[24px] border p-5 text-left shadow-soft transition hover:-translate-y-0.5 ${
              selectedMeetingId === meeting.id
                ? "border-stone-950 bg-stone-950 text-white"
                : "hairline bg-white hover:border-stone-300"
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="truncate text-lg font-bold tracking-[-0.03em]">
                  {meeting.filename}
                </div>
                <div className={`mt-2 flex flex-wrap items-center gap-3 text-sm ${
                  selectedMeetingId === meeting.id ? "text-stone-300" : "text-slate-500"
                }`}>
                  <span>{formatDate(meeting.created_at)}</span>
                  <span className="inline-flex items-center gap-1">
                    <Clock3 size={14} />
                    {formatDuration(meeting.duration_secs)}
                  </span>
                  <span>{actionItems.length} actions</span>
                </div>
              </div>
              <ArrowUpRight size={16} className={selectedMeetingId === meeting.id ? "text-amber-300" : "text-slate-400"} />
            </div>

            <p className={`mt-4 line-clamp-2 text-sm leading-6 ${
              selectedMeetingId === meeting.id ? "text-stone-200" : "text-slate-600"
            }`}>
              {meeting.overview || "No overview available yet."}
            </p>

            <div className="mt-4">
              <StatusPill status={meeting.status} />
            </div>
          </button>
        );
      })}
    </div>
  );
}
