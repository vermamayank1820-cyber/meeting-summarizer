import { ArrowRight, AudioLines } from "lucide-react";

export default function EmptyState({ title, description, ctaLabel, onCta }) {
  return (
    <div className="rounded-[28px] border border-dashed border-slate-300 bg-white/70 px-6 py-12 text-center shadow-soft">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-amber-50 text-amber-700">
        <AudioLines size={28} />
      </div>
      <h3 className="mt-5 text-2xl font-bold tracking-[-0.03em] text-slate-950">
        {title}
      </h3>
      <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-slate-600">
        {description}
      </p>
      <button
        onClick={onCta}
        className="mt-6 inline-flex items-center gap-2 rounded-2xl bg-stone-950 px-5 py-3 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-stone-800"
      >
        {ctaLabel}
        <ArrowRight size={16} />
      </button>
    </div>
  );
}
