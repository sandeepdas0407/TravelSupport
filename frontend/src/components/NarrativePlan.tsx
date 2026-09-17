import type { NarrativePlan as NarrativePlanType } from '../types/tripPlan'

export function NarrativePlan({ plan }: { plan: NarrativePlanType }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        Your trip plan
      </h2>
      <p className="mt-2 text-slate-800 dark:text-slate-200">{plan.summary}</p>

      <ol className="mt-4 flex flex-col gap-3">
        {plan.day_by_day.map((day) => (
          <li key={day.day_number} className="border-l-2 border-indigo-500 pl-3">
            <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Day {day.day_number} · {day.date} — {day.title}
            </p>
            <p className="text-sm text-slate-600 dark:text-slate-400">{day.description}</p>
          </li>
        ))}
      </ol>

      {plan.packing_suggestions.length > 0 && (
        <div className="mt-4">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Packing suggestions
          </h3>
          <ul className="mt-1 list-inside list-disc text-sm text-slate-700 dark:text-slate-300">
            {plan.packing_suggestions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
