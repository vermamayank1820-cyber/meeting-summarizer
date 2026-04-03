export default function KpiCard({ label, value, hint, tone = "default" }) {
  const tones = {
    default: "from-white to-stone-50",
    warm: "from-amber-50 to-orange-50",
    cool: "from-cyan-50 to-sky-50",
    green: "from-emerald-50 to-lime-50",
  };

  return (
    <div className={`rounded-[24px] border hairline bg-gradient-to-br ${tones[tone]} p-5 shadow-soft transition hover:-translate-y-0.5`}>
      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
        {label}
      </div>
      <div className="mt-4 text-3xl font-extrabold tracking-[-0.05em]">{value}</div>
      <div className="mt-2 text-sm text-slate-600">{hint}</div>
    </div>
  );
}
