import { Bell, Sparkles } from "lucide-react";
import Sidebar from "./Sidebar";

export default function AppShell({
  currentView,
  onNavigate,
  health,
  children,
}) {
  return (
    <div className="min-h-screen p-3 text-ink md:p-5">
      <div className="mx-auto flex min-h-[calc(100vh-1.5rem)] max-w-[1600px] gap-3 rounded-[32px] border hairline bg-white/60 p-3 shadow-panel backdrop-blur-xl md:p-4">
        <Sidebar currentView={currentView} onNavigate={onNavigate} />

        <div className="flex min-w-0 flex-1 flex-col rounded-[28px] border hairline bg-stone-50/70">
          <header className="flex flex-col gap-4 border-b hairline px-5 py-5 md:flex-row md:items-center md:justify-between md:px-8">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">
                <Sparkles size={14} />
                AI meeting operating system
              </div>
              <h1 className="mt-3 text-2xl font-extrabold tracking-[-0.04em] md:text-[2rem]">
                From recording to aligned action in one flow.
              </h1>
              <p className="mt-2 max-w-2xl text-sm text-slate-600 md:text-[15px]">
                Upload, summarize, extract decisions, and keep every follow-up visible without digging through notes.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm shadow-soft">
                <div className="font-semibold text-emerald-900">
                  {health?.status === "ok" ? "API healthy" : "API unavailable"}
                </div>
                <div className="text-xs text-emerald-700/80">
                  {health?.llm_provider ? `LLM: ${health.llm_provider}` : "Check backend connection"}
                </div>
              </div>
              <button className="flex h-12 w-12 items-center justify-center rounded-2xl border hairline bg-white text-slate-600 transition hover:-translate-y-0.5 hover:shadow-soft">
                <Bell size={18} />
              </button>
            </div>
          </header>

          <main className="flex-1 overflow-y-auto px-4 py-5 md:px-8 md:py-8">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
