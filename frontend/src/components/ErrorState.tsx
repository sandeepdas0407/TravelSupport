export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="mx-auto flex w-full max-w-xl flex-col items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-6 text-center dark:border-red-900 dark:bg-red-950">
      <p className="text-sm text-red-700 dark:text-red-300">{message}</p>
      <button
        onClick={onRetry}
        className="rounded-lg border border-red-300 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-100 dark:border-red-800 dark:text-red-300 dark:hover:bg-red-900"
      >
        Try again
      </button>
    </div>
  )
}
