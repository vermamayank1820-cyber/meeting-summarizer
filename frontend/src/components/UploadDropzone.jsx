import { FileAudio2, UploadCloud, X } from "lucide-react";

export default function UploadDropzone({
  file,
  onFileChange,
  onClear,
  summaryStyle,
  onSummaryStyleChange,
  onSubmit,
  isSubmitting,
  error,
}) {
  return (
    <div className="grid gap-6 xl:grid-cols-[1.3fr_0.8fr]">
      <div className="rounded-[28px] border hairline bg-white p-6 shadow-soft">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
          New recording
        </div>
        <h2 className="mt-3 text-2xl font-bold tracking-[-0.03em] text-slate-950">
          Drag in a recording or browse from disk.
        </h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Video and audio are supported. Large files are chunked automatically before transcription.
        </p>

        <label className="mt-6 flex cursor-pointer flex-col items-center justify-center rounded-[28px] border-2 border-dashed border-slate-300 bg-stone-50/70 px-6 py-14 text-center transition hover:border-amber-300 hover:bg-amber-50/40">
          <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-white text-slate-700 shadow-soft">
            <UploadCloud size={28} />
          </div>
          <div className="mt-5 text-lg font-bold tracking-[-0.03em] text-slate-950">
            Drop your recording here
          </div>
          <div className="mt-2 max-w-md text-sm leading-6 text-slate-500">
            MP4, MP3, WAV, M4A, WebM, OGG, MKV, MOV. Use executive mode for fast summaries or detailed mode for full traceability.
          </div>
          <input
            className="hidden"
            type="file"
            accept=".mp4,.mp3,.wav,.m4a,.webm,.ogg,.mkv,.mov"
            onChange={(event) => onFileChange(event.target.files?.[0] || null)}
          />
        </label>

        {file ? (
          <div className="mt-5 flex items-center gap-4 rounded-[24px] border border-slate-200 bg-slate-50 px-4 py-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white shadow-soft">
              <FileAudio2 size={22} className="text-slate-700" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-semibold text-slate-950">{file.name}</div>
              <div className="mt-1 text-sm text-slate-500">
                {(file.size / 1024 / 1024).toFixed(1)} MB ready for ingestion
              </div>
            </div>
            <button
              onClick={onClear}
              className="rounded-full border border-slate-200 p-2 text-slate-500 transition hover:border-rose-200 hover:bg-rose-50 hover:text-rose-700"
            >
              <X size={16} />
            </button>
          </div>
        ) : null}

        {error ? (
          <div className="mt-5 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            {error}
          </div>
        ) : null}
      </div>

      <div className="rounded-[28px] border hairline bg-[#171c1a] p-6 text-white shadow-soft">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">
          Summary mode
        </div>
        <div className="mt-5 space-y-3">
          {[
            {
              value: "executive",
              title: "Executive brief",
              description: "Concise overview, decisions, and next moves for leaders.",
            },
            {
              value: "detailed",
              title: "Detailed breakdown",
              description: "Full context, structured discussion points, and owner-level action tracking.",
            },
          ].map((option) => {
            const active = summaryStyle === option.value;

            return (
              <button
                key={option.value}
                onClick={() => onSummaryStyleChange(option.value)}
                className={`w-full rounded-[24px] border px-4 py-4 text-left transition ${
                  active
                    ? "border-emerald-300 bg-emerald-400/10"
                    : "border-white/10 bg-white/5 hover:bg-white/10"
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="text-base font-semibold text-white">{option.title}</div>
                  <div className={`h-3 w-3 rounded-full ${active ? "bg-emerald-300" : "bg-white/30"}`} />
                </div>
                <div className="mt-2 text-sm leading-6 text-stone-300">
                  {option.description}
                </div>
              </button>
            );
          })}
        </div>

        <div className="mt-6 rounded-[24px] bg-white/5 p-4">
          <div className="text-sm font-semibold text-white">What happens next</div>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-stone-300">
            <li>1. Recording uploads to the backend pipeline.</li>
            <li>2. Audio is extracted and transcribed in parallel chunks.</li>
            <li>3. AI returns summary, key points, and action items in one workspace.</li>
          </ul>
        </div>

        <button
          onClick={onSubmit}
          disabled={!file || isSubmitting}
          className="mt-6 w-full rounded-[24px] bg-amber-400 px-5 py-4 text-sm font-extrabold text-stone-950 transition hover:-translate-y-0.5 hover:bg-amber-300 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {isSubmitting ? "Starting pipeline..." : "Process recording"}
        </button>
      </div>
    </div>
  );
}
