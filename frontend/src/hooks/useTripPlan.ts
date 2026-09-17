import { useCallback, useState } from 'react'
import { TripPlanApiError, requestTripPlan } from '../api/tripPlanClient'
import type { TripPlanRequest, TripPlanResponse } from '../types/tripPlan'

type TripPlanState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: TripPlanResponse }
  | { status: 'error'; message: string }

export function useTripPlan() {
  const [state, setState] = useState<TripPlanState>({ status: 'idle' })

  const submit = useCallback(async (request: TripPlanRequest) => {
    setState({ status: 'loading' })
    try {
      const data = await requestTripPlan(request)
      setState({ status: 'success', data })
    } catch (error) {
      const message = error instanceof TripPlanApiError ? error.message : 'Something went wrong. Please try again.'
      setState({ status: 'error', message })
    }
  }, [])

  const reset = useCallback(() => setState({ status: 'idle' }), [])

  return { state, submit, reset }
}
