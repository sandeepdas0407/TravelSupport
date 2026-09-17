import type { LodgingSuggestion } from '../types/tripPlan'

export function LodgingSuggestions({ lodging }: { lodging: LodgingSuggestion[] }) {
  if (lodging.length === 0) {
    return null
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        Places to stay
      </h2>
      <ul className="mt-3 flex flex-col gap-3">
        {lodging.map((place) => (
          <li key={place.google_place_id} className="flex items-start justify-between gap-3">
            <div>
              <a
                href={place.maps_url}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-indigo-600 hover:underline dark:text-indigo-400"
              >
                {place.name}
              </a>
              <p className="text-sm text-slate-600 dark:text-slate-400">{place.address}</p>
            </div>
            {place.rating !== null && (
              <span className="shrink-0 text-sm font-medium text-slate-700 dark:text-slate-300">
                ★ {place.rating.toFixed(1)}
              </span>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
