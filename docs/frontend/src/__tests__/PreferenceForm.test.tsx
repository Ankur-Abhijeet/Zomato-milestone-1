import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PreferenceForm } from '../components/PreferenceForm/PreferenceForm'

describe('PreferenceForm', () => {
  it('renders all form fields correctly', () => {
    render(<PreferenceForm onSubmit={() => {}} isLoading={false} />)

    expect(screen.getByLabelText(/location/i)).toBeInTheDocument()
    expect(screen.getByRole('group', { name: /budget selection/i })).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/type a cuisine/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/min rating/i)).toBeInTheDocument()
    expect(screen.getByRole('group', { name: /number of results/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/special preferences/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /find restaurants/i })).toBeInTheDocument()
  })

  it('shows error message if submitted with empty location', () => {
    render(<PreferenceForm onSubmit={() => {}} isLoading={false} />)

    const submitBtn = screen.getByRole('button', { name: /find restaurants/i })
    fireEvent.click(submitBtn)

    expect(screen.getByRole('alert')).toHaveTextContent(/please enter a city or area/i)
  })

  it('allows selecting different budget options', () => {
    const handleSubmit = vi.fn()
    render(<PreferenceForm onSubmit={handleSubmit} isLoading={false} />)

    const locationInput = screen.getByLabelText(/location/i)
    fireEvent.change(locationInput, { target: { value: 'Bellandur' } })

    const lowBudgetBtn = screen.getByRole('button', { name: /low/i })
    fireEvent.click(lowBudgetBtn)

    const submitBtn = screen.getByRole('button', { name: /find restaurants/i })
    fireEvent.click(submitBtn)

    expect(handleSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        location: 'Bellandur',
        budget: 'low',
      })
    )
  })

  it('allows adding and removing cuisines', () => {
    const handleSubmit = vi.fn()
    render(<PreferenceForm onSubmit={handleSubmit} isLoading={false} />)

    const locationInput = screen.getByLabelText(/location/i)
    fireEvent.change(locationInput, { target: { value: 'Koramangala' } })

    const cuisineInput = screen.getByPlaceholderText(/type a cuisine/i)
    fireEvent.change(cuisineInput, { target: { value: 'Chinese' } })
    fireEvent.keyDown(cuisineInput, { key: 'Enter', code: 'Enter' })

    // Input should be cleared and chip should be present
    expect(screen.getByText('Chinese')).toBeInTheDocument()

    // Add another
    fireEvent.change(cuisineInput, { target: { value: 'Italian' } })
    fireEvent.keyDown(cuisineInput, { key: ',', code: 'Comma' })
    expect(screen.getByText('Italian')).toBeInTheDocument()

    // Remove first
    const removeBtn = screen.getByRole('button', { name: /remove chinese/i })
    fireEvent.click(removeBtn)
    expect(screen.queryByText('Chinese')).not.toBeInTheDocument()

    const submitBtn = screen.getByRole('button', { name: /find restaurants/i })
    fireEvent.click(submitBtn)

    expect(handleSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        location: 'Koramangala',
        cuisines: ['Italian'],
      })
    )
  })

  it('disables input controls when isLoading is true', () => {
    render(<PreferenceForm onSubmit={() => {}} isLoading={true} />)

    expect(screen.getByLabelText(/location/i)).toBeDisabled()
    expect(screen.getByRole('button', { name: /low/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /medium/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /high/i })).toBeDisabled()
    expect(screen.getByPlaceholderText(/type a cuisine/i)).toBeDisabled()
    expect(screen.getByLabelText(/min rating/i)).toBeDisabled()
    expect(screen.getByRole('button', { name: /decrease results/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /increase results/i })).toBeDisabled()
    expect(screen.getByLabelText(/special preferences/i)).toBeDisabled()
    expect(screen.getByRole('button', { name: /finding your perfect spots/i })).toBeDisabled()
  })

  it('supports modifying rating and results count', () => {
    const handleSubmit = vi.fn()
    render(<PreferenceForm onSubmit={handleSubmit} isLoading={false} />)

    const locationInput = screen.getByLabelText(/location/i)
    fireEvent.change(locationInput, { target: { value: 'Indiranagar' } })

    const ratingInput = screen.getByLabelText(/min rating/i)
    fireEvent.change(ratingInput, { target: { value: '4.5' } })

    const incBtn = screen.getByRole('button', { name: /increase results/i })
    fireEvent.click(incBtn) // 5 -> 6
    fireEvent.click(incBtn) // 6 -> 7

    const submitBtn = screen.getByRole('button', { name: /find restaurants/i })
    fireEvent.click(submitBtn)

    expect(handleSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        location: 'Indiranagar',
        min_rating: 4.5,
        top_k: 7,
      })
    )
  })
})
