import type { DailyWeather } from '../types/tripPlan'

export function WeatherForecastList({ weather }: { weather: DailyWeather[] }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Weather</h2>
      <ul className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
        {weather.map((day) => (
          <li
            key={day.date}
            className="rounded-lg border border-slate-100 p-3 text-sm dark:border-slate-800"
          >
            <p className="font-medium text-slate-900 dark:text-slate-100">{day.date}</p>
            <p className="text-slate-600 dark:text-slate-400">
              {Math.round(day.temp_min_c)}° / {Math.round(day.temp_max_c)}°C
            </p>
            <p className="text-slate-500 dark:text-slate-400">{day.conditions_summary}</p>
            {day.source === 'climatology' && (
              <p className="mt-1 text-xs italic text-amber-600 dark:text-amber-400">
                Estimated from historical averages
              </p>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
