import { ErrorState } from './components/ErrorState'
import { LoadingState } from './components/LoadingState'
import { TripPlanResult } from './components/TripPlanResult'
import { TripRequestForm } from './components/TripRequestForm'
import { useTripPlan } from './hooks/useTripPlan'

function App() {
  const { state, submit, reset } = useTripPlan()

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-10 dark:bg-slate-950">
      <header className="mx-auto mb-8 max-w-xl text-center">
        <h1 className="text-3xl font-semibold text-slate-900 dark:text-slate-100">TravelSupport</h1>
        <p className="mt-1 text-slate-600 dark:text-slate-400">
          Tell us where you're headed and we'll plan the route, weather, and stays.
        </p>
      </header>

      <main className="flex flex-col gap-6">
        {state.status !== 'success' && (
          <TripRequestForm onSubmit={submit} isSubmitting={state.status === 'loading'} />
        )}

        {state.status === 'loading' && <LoadingState />}
        {state.status === 'error' && <ErrorState message={state.message} onRetry={reset} />}
        {state.status === 'success' && (
          <>
            <TripPlanResult plan={state.data} />
            <button
              onClick={reset}
              className="mx-auto text-sm font-medium text-indigo-600 hover:underline dark:text-indigo-400"
            >
              Plan another trip
            </button>
          </>
        )}
      </main>
    </div>
  )
}

export default App
