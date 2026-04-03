import { ChevronDown, ChevronUp, Circle, Clock3, UserRound } from "lucide-react";
import { useMemo, useState } from "react";
import { formatDate, inferTaskStatus, safeJsonParse } from "../lib/formatters";
import StatusPill from "./StatusPill";

function normalizeTasks(actionItems, fallbackTitle) {
  return safeJsonParse(actionItems, []).map((item, index) => ({
    id: `${fallbackTitle}-${index}`,
    task: item.task || item.step || item.decision || "Untitled action",
    owner: item.owner || item.responsible || item.stakeholder || "Unassigned",
    deadline: item.deadline || item.timeline || "TBD",
    notes: item.notes || item.details || item.rationale || "",
  }));
}

function Group({ title, items, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="rounded-[24px] border hairline bg-white">
      <button
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left"
      >
        <div>
          <div className="text-base font-bold tracking-[-0.03em] text-slate-950">{title}</div>
          <div className="mt-1 text-sm text-slate-500">{items.length} tracked actions</div>
        </div>
        <div className="rounded-full bg-stone-100 p-2 text-slate-600">
          {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </button>

      {open ? (
        <div className="border-t hairline px-3 pb-3 pt-1">
          {items.map((item) => {
            const status = inferTaskStatus(item.deadline);

            return (
              <div
                key={item.id}
                className="mt-3 rounded-[20px] border border-slate-200 bg-stone-50/80 px-4 py-4 transition hover:border-stone-300 hover:bg-stone-50"
              >
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="min-w-0">
                    <div className="flex items-start gap-3">
                      <Circle size={16} className="mt-1 text-slate-300" />
                      <div>
                        <div className="text-sm font-semibold text-slate-950 md:text-[15px]">
                          {item.task}
                        </div>
                        {item.notes ? (
                          <div className="mt-2 text-sm leading-6 text-slate-600">
                            {item.notes}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 pl-7 md:pl-0">
                    <div className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-2 text-xs font-medium text-slate-600">
                      <UserRound size={14} />
                      {item.owner}
                    </div>
                    <div className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-2 text-xs font-medium text-slate-600">
                      <Clock3 size={14} />
                      {item.deadline === "TBD" ? "TBD" : formatDate(item.deadline)}
                    </div>
                    <StatusPill status={status} />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}

export default function ActionItemsBoard({ meetings, groupBy = "meeting" }) {
  const groups = useMemo(() => {
    if (groupBy === "owner") {
      const ownerMap = new Map();

      meetings.forEach((meeting) => {
        normalizeTasks(meeting.action_items, meeting.filename).forEach((task) => {
          const key = task.owner || "Unassigned";
          const bucket = ownerMap.get(key) || [];
          bucket.push(task);
          ownerMap.set(key, bucket);
        });
      });

      return Array.from(ownerMap.entries()).map(([title, items]) => ({ title, items }));
    }

    return meetings
      .map((meeting) => ({
        title: meeting.filename,
        items: normalizeTasks(meeting.action_items, meeting.filename),
      }))
      .filter((group) => group.items.length > 0);
  }, [groupBy, meetings]);

  if (!groups.length) {
    return (
      <div className="rounded-[24px] border border-dashed border-slate-300 bg-stone-50/80 px-5 py-10 text-center text-sm text-slate-500">
        No action items yet. Process a meeting to generate owner-level follow-ups.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {groups.map((group, index) => (
        <Group key={group.title} title={group.title} items={group.items} defaultOpen={index < 2} />
      ))}
    </div>
  );
}
