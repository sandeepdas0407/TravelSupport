import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { TripRequestForm } from '../src/components/TripRequestForm'

describe('TripRequestForm', () => {
  it('shows a validation error when submitted empty', async () => {
    const onSubmit = vi.fn()
    render(<TripRequestForm onSubmit={onSubmit} isSubmitting={false} />)

    await userEvent.click(screen.getByRole('button', { name: /plan my trip/i }))

    expect(await screen.findByText(/enter a starting location/i)).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('submits valid input', async () => {
    const onSubmit = vi.fn()
    render(<TripRequestForm onSubmit={onSubmit} isSubmitting={false} />)

    await userEvent.type(screen.getByPlaceholderText(/seattle/i), 'Seattle, WA')
    await userEvent.type(screen.getByPlaceholderText(/banff/i), 'Banff, AB')
    await userEvent.click(screen.getByRole('button', { name: /plan my trip/i }))

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ from_location: 'Seattle, WA', to_location: 'Banff, AB' }),
    )
  })
})
