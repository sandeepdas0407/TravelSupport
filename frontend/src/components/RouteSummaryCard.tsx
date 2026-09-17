import type { RouteSummary } from '../types/tripPlan'

export function RouteSummaryCard({ route }: { route: RouteSummary }) {
  const hours = Math.floor(route.duration_minutes / 60)
  const minutes = route.duration_minutes % 60

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Route</h2>
      <p className="mt-2 text-lg font-medium text-slate-900 dark:text-slate-100">
        {route.origin.resolved_name} → {route.destination.resolved_name}
      </p>
      <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
        {route.distance_km.toFixed(0)} km · {hours}h {minutes}m drive
      </p>
    </div>
  )
}
