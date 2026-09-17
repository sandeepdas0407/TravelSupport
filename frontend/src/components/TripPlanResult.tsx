import type { TripPlanResponse } from '../types/tripPlan'
import { LodgingSuggestions } from './LodgingSuggestions'
import { NarrativePlan } from './NarrativePlan'
import { RouteSummaryCard } from './RouteSummaryCard'
import { WeatherForecastList } from './WeatherForecastList'

export function TripPlanResult({ plan }: { plan: TripPlanResponse }) {
  return (
    <div className="mx-auto flex w-full max-w-xl flex-col gap-4">
      {plan.meta.warnings.length > 0 && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-300">
          {plan.meta.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      )}
      <RouteSummaryCard route={plan.route} />
      <WeatherForecastList weather={plan.weather} />
      <LodgingSuggestions lodging={plan.lodging} />
      <NarrativePlan plan={plan.narrative_plan} />
    </div>
  )
}
