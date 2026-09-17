// Mirrors backend/app/schemas.py. Regenerate with `npm run codegen:types` once the
// backend is running, to keep this in sync with the FastAPI-emitted OpenAPI schema.

export interface TripPlanRequest {
  from_location: string
  to_location: string
  start_date: string
  num_days: number
  additional_info?: string
}

export interface GeoPoint {
  query: string
  lat: number
  lon: number
  resolved_name: string
}

export interface RouteSummary {
  origin: GeoPoint
  destination: GeoPoint
  distance_km: number
  duration_minutes: number
}

export type WeatherSource = 'forecast' | 'climatology'

export interface DailyWeather {
  date: string
  source: WeatherSource
  temp_min_c: number
  temp_max_c: number
  precip_probability_pct: number
  conditions_summary: string
}

export interface LodgingSuggestion {
  name: string
  address: string
  rating: number | null
  price_level: string | null
  google_place_id: string
  maps_url: string
}

export interface DayPlan {
  day_number: number
  date: string
  title: string
  description: string
}

export interface NarrativePlan {
  summary: string
  day_by_day: DayPlan[]
  recommended_stays: string[]
  packing_suggestions: string[]
}

export interface TripPlanMeta {
  generated_at: string
  model_used: string
  data_sources_used: string[]
  warnings: string[]
}

export interface TripPlanResponse {
  route: RouteSummary
  weather: DailyWeather[]
  lodging: LodgingSuggestion[]
  narrative_plan: NarrativePlan
  meta: TripPlanMeta
}

export interface ApiErrorBody {
  detail: string
}
