export default function SuggestionChip({ label, onClick }) {
  return (
    <button
      onClick={onClick}
      className="rounded-full border border-white/70 bg-white/80 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:-translate-y-0.5 hover:border-amber-200 hover:bg-amber-50 hover:text-amber-900"
    >
      {label}
    </button>
  );
}
