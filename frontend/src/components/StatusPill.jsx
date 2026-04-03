const styles = {
  completed: "bg-emerald-50 text-emerald-800 border-emerald-200",
  processing: "bg-amber-50 text-amber-800 border-amber-200",
  queued: "bg-sky-50 text-sky-800 border-sky-200",
  failed: "bg-rose-50 text-rose-800 border-rose-200",
  "in progress": "bg-amber-50 text-amber-800 border-amber-200",
  "on track": "bg-emerald-50 text-emerald-800 border-emerald-200",
  "due soon": "bg-orange-50 text-orange-800 border-orange-200",
  "at risk": "bg-rose-50 text-rose-800 border-rose-200",
  "needs owner": "bg-slate-100 text-slate-700 border-slate-200",
};

export default function StatusPill({ status }) {
  const key = (status || "").toLowerCase();
  const className = styles[key] || "bg-slate-100 text-slate-700 border-slate-200";

  return (
    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold ${className}`}>
      {status}
    </span>
  );
}
