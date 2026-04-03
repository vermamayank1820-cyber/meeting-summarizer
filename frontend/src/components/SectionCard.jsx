export default function SectionCard({
  title,
  eyebrow,
  action,
  children,
  className = "",
}) {
  return (
    <section className={`rounded-[28px] border hairline bg-white p-5 shadow-soft md:p-6 ${className}`}>
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          {eyebrow ? (
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
              {eyebrow}
            </div>
          ) : null}
          <h2 className="mt-2 text-xl font-bold tracking-[-0.03em] text-slate-950">
            {title}
          </h2>
        </div>
        {action}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}
