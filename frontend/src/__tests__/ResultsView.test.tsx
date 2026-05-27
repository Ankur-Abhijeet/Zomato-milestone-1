import { describe, it, expect } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { ResultsView } from '../components/ResultsView/ResultsView'
import type { RecommendResponse } from '../types/api'

const mockData: RecommendResponse = {
  summary: 'This is an AI summary of 2 curated choices.',
  used_fallback: false,
  skip_llm: false,
  message: null,
  filter_stats: {
    initial: 50000,
    after_location: 2000,
    after_rating: 1000,
    after_budget: 500,
    after_cuisine: 10,
    capped_for_llm: 10,
  },
  recommendations: [
    {
      rank: 1,
      id: 'r1',
      name: 'The Fine Diner',
      cuisine: 'Continental, Italian',
      rating: 4.8,
      estimated_cost: '1200',
      location: 'Indiranagar',
      explanation: 'Great continental selections and high ambiance.',
      is_ai_generated: true,
    },
    {
      rank: 2,
      id: 'r2',
      name: 'Spice Route',
      cuisine: 'North Indian',
      rating: 4.5,
      estimated_cost: '800',
      location: 'Indiranagar',
      explanation: 'Delicious spices and affordable dining.',
      is_ai_generated: true,
    },
  ],
  dedup_removed: 3,
}

describe('ResultsView', () => {
  it('renders loading skeleton when isLoading is true', () => {
    render(<ResultsView isLoading={true} data={null} topK={3} />)

    expect(screen.getByLabelText(/loading recommendations/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/loading recommendations/i)).toHaveAttribute('aria-busy', 'true')
  })

  it('renders nothing when data is null', () => {
    const { container } = render(<ResultsView isLoading={false} data={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders empty state when skip_llm is true or recommendations is empty', () => {
    const emptyData: RecommendResponse = {
      summary: null,
      used_fallback: false,
      skip_llm: true,
      message: 'No active locations match.',
      filter_stats: {
        initial: 50000,
        after_location: 0,
        after_rating: 0,
        after_budget: 0,
        after_cuisine: 0,
        capped_for_llm: 0,
      },
      recommendations: [],
      dedup_removed: 0,
    }

    render(<ResultsView isLoading={false} data={emptyData} />)

    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.getByText(/no restaurants found/i)).toBeInTheDocument()
    expect(screen.getByText(/no active locations match/i)).toBeInTheDocument()

    // Check filter stats strip in empty state
    expect(screen.getByLabelText(/filter statistics/i)).toBeInTheDocument()
    expect(screen.getByText(/total/i)).toBeInTheDocument()
  })

  it('renders recommendations, summary, fallback banner, stats, and count when data is provided', () => {
    render(<ResultsView isLoading={false} data={mockData} />)

    // Filter Stats
    const statsContainer = screen.getByLabelText(/filter statistics/i)
    expect(statsContainer).toBeInTheDocument()

    // Check specific label and values inside the stats container
    expect(within(statsContainer).getByText(/total/i)).toBeInTheDocument()
    expect(within(statsContainer).getByText('50,000')).toBeInTheDocument()
    expect(within(statsContainer).getByText(/location/i)).toBeInTheDocument()
    expect(within(statsContainer).getByText('2,000')).toBeInTheDocument()
    expect(within(statsContainer).getByText(/sent to ai/i)).toBeInTheDocument()
    expect(within(statsContainer).getAllByText('10')).toHaveLength(2)

    // Dedup stats chip
    expect(within(statsContainer).getByText(/hidden/i)).toHaveTextContent(/3 duplicate/i)

    // Showing Count
    expect(screen.getByText(/showing/i)).toHaveTextContent(/showing 2 recommendations/i)

    // Recommendations Cards
    expect(screen.getByText('The Fine Diner')).toBeInTheDocument()
    expect(screen.getByText('Continental, Italian')).toBeInTheDocument()
    expect(screen.getByText(/1200 for two/i)).toBeInTheDocument()
    expect(screen.getByText('Spice Route')).toBeInTheDocument()
    expect(screen.getByText('North Indian')).toBeInTheDocument()
    expect(screen.getByText(/800 for two/i)).toBeInTheDocument()
  })

  it('renders fallback ranking warning banner when used_fallback is true', () => {
    const fallbackData = {
      ...mockData,
      used_fallback: true,
      recommendations: mockData.recommendations.map(r => ({
        ...r,
        is_ai_generated: false,
      })),
    }

    render(<ResultsView isLoading={false} data={fallbackData} />)

    expect(screen.getByText(/ai unavailable — results are ranked by rating/i)).toBeInTheDocument()
    // Should show Ranked by Rating warning banner
    const badges = screen.getAllByText(/ranked by rating/i)
    expect(badges.length).toBe(1)
  })
})
