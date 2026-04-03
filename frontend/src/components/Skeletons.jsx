export function SkeletonBlock({ className = "" }) {
  return <div className={`shimmer animate-shimmer rounded-2xl ${className}`} />;
}

export function ProcessingLayoutSkeleton() {
  return (
    <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <div className="space-y-6">
        <div className="rounded-[28px] border hairline bg-white p-6 shadow-soft">
          <SkeletonBlock className="h-4 w-28" />
          <SkeletonBlock className="mt-4 h-10 w-3/4" />
          <SkeletonBlock className="mt-3 h-5 w-2/3" />
          <div className="mt-8 space-y-3">
            <SkeletonBlock className="h-20 w-full" />
            <SkeletonBlock className="h-20 w-full" />
            <SkeletonBlock className="h-20 w-[92%]" />
          </div>
        </div>

        <div className="rounded-[28px] border hairline bg-white p-6 shadow-soft">
          <SkeletonBlock className="h-4 w-32" />
          <div className="mt-6 space-y-4">
            <SkeletonBlock className="h-16 w-full" />
            <SkeletonBlock className="h-16 w-full" />
            <SkeletonBlock className="h-16 w-11/12" />
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <div className="rounded-[28px] border hairline bg-white p-6 shadow-soft">
          <SkeletonBlock className="h-4 w-24" />
          <SkeletonBlock className="mt-5 h-12 w-full" />
          <SkeletonBlock className="mt-4 h-12 w-full" />
          <SkeletonBlock className="mt-4 h-12 w-4/5" />
        </div>
        <div className="rounded-[28px] border hairline bg-white p-6 shadow-soft">
          <SkeletonBlock className="h-4 w-40" />
          <SkeletonBlock className="mt-6 h-40 w-full" />
        </div>
      </div>
    </div>
  );
}
