export function LoadingState() {
  return (
    <div className="mx-auto flex w-full max-w-xl items-center justify-center gap-3 rounded-xl border border-slate-200 bg-white p-6 text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600" />
      Planning your trip…
    </div>
  )
}
