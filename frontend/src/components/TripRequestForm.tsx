import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import type { TripPlanRequest } from '../types/tripPlan'

const todayIso = () => new Date().toISOString().slice(0, 10)

const tripRequestSchema = z.object({
  from_location: z.string().trim().min(2, 'Enter a starting location'),
  to_location: z.string().trim().min(2, 'Enter a destination'),
  start_date: z.string().refine((value) => value >= todayIso(), 'Start date cannot be in the past'),
  num_days: z.coerce.number().int().min(1, 'At least 1 day').max(21, 'Max 21 days'),
  additional_info: z.string().max(2000, 'Keep it under 2000 characters').optional(),
})

type TripRequestFormInput = z.input<typeof tripRequestSchema>

interface TripRequestFormProps {
  onSubmit: (request: TripPlanRequest) => void
  isSubmitting: boolean
}

export function TripRequestForm({ onSubmit, isSubmitting }: TripRequestFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TripRequestFormInput, unknown, TripPlanRequest>({
    resolver: zodResolver(tripRequestSchema),
    defaultValues: {
      from_location: '',
      to_location: '',
      start_date: todayIso(),
      num_days: 3,
      additional_info: '',
    },
  })

  return (
    <form
      onSubmit={handleSubmit((values) => onSubmit(values))}
      className="mx-auto flex w-full max-w-xl flex-col gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="From" error={errors.from_location?.message}>
          <input
            {...register('from_location')}
            placeholder="Seattle, WA"
            className="input"
          />
        </Field>
        <Field label="To" error={errors.to_location?.message}>
          <input
            {...register('to_location')}
            placeholder="Banff, AB"
            className="input"
          />
        </Field>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Travel date" error={errors.start_date?.message}>
          <input type="date" {...register('start_date')} className="input" />
        </Field>
        <Field label="Number of days" error={errors.num_days?.message}>
          <input type="number" min={1} max={21} {...register('num_days')} className="input" />
        </Field>
      </div>

      <Field label="Additional information (optional)" error={errors.additional_info?.message}>
        <textarea
          {...register('additional_info')}
          rows={4}
          placeholder="Traveling with a toddler, prefer scenic stops, on a budget..."
          className="input resize-none"
        />
      </Field>

      <button
        type="submit"
        disabled={isSubmitting}
        className="mt-2 rounded-lg bg-indigo-600 px-4 py-2.5 font-medium text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? 'Planning your trip…' : 'Plan my trip'}
      </button>
    </form>
  )
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="font-medium text-slate-700 dark:text-slate-200">{label}</span>
      {children}
      {error && <span className="text-xs text-red-600 dark:text-red-400">{error}</span>}
    </label>
  )
}
