import {
  AudioLines,
  CalendarRange,
  CheckCircle2,
  FolderCog,
  LayoutDashboard,
  Upload,
} from "lucide-react";

const items = [
  { id: "dashboard", label: "Meetings", icon: LayoutDashboard },
  { id: "upload", label: "Ingestion", icon: Upload },
  { id: "agenda", label: "Agenda", icon: CalendarRange },
  { id: "action-items", label: "Action Items", icon: CheckCircle2 },
  { id: "settings", label: "Settings", icon: FolderCog },
];

export default function Sidebar({ currentView, onNavigate }) {
  return (
    <aside className="hidden w-[285px] flex-col rounded-[28px] border hairline bg-[#121a18] p-5 text-stone-100 lg:flex">
      <div className="rounded-[24px] border border-white/10 bg-white/5 p-4">
        <div className="flex items-start gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-400 text-stone-950 shadow-soft">
            <AudioLines size={20} />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">Northstar Ops</div>
            <div className="mt-1 text-xs text-stone-400">Design + product workspace</div>
          </div>
        </div>
        <div className="mt-4 rounded-2xl bg-white/5 p-3">
          <div className="text-xs uppercase tracking-[0.24em] text-stone-500">Signed in</div>
          <div className="mt-2 text-sm font-semibold text-white">Mayank Verma</div>
          <div className="text-xs text-stone-400">AI systems lead</div>
        </div>
      </div>

      <nav className="mt-6 space-y-1">
        {items.map((item) => {
          const Icon = item.icon;
          const active = currentView === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm font-medium transition ${
                active
                  ? "bg-white text-stone-950 shadow-soft"
                  : "text-stone-300 hover:bg-white/5 hover:text-white"
              }`}
            >
              <Icon size={18} />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="mt-auto rounded-[24px] border border-emerald-300/20 bg-emerald-400/10 p-4">
        <div className="text-xs uppercase tracking-[0.24em] text-emerald-200/70">
          Workflow tip
        </div>
        <p className="mt-3 text-sm leading-6 text-emerald-50">
          Keep uploads in executive mode by default. Use detailed mode only when you need owner-level traceability.
        </p>
      </div>
    </aside>
  );
}
