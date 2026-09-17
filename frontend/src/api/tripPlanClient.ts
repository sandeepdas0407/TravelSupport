import type { ApiErrorBody, TripPlanRequest, TripPlanResponse } from '../types/tripPlan'

export class TripPlanApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'TripPlanApiError'
    this.status = status
  }
}

export async function requestTripPlan(request: TripPlanRequest): Promise<TripPlanResponse> {
  const response = await fetch('/api/trip-plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiErrorBody | null
    throw new TripPlanApiError(response.status, body?.detail ?? `Request failed with status ${response.status}`)
  }

  return (await response.json()) as TripPlanResponse
}
