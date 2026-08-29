import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusBadge } from '../components/ui/StatusBadge'
import { EmptyState } from '../components/ui/EmptyState'

describe('UI Primitives (SL-047)', () => {
  it('renders StatusBadge with completed state', () => {
    render(<StatusBadge status="completed" />)
    expect(screen.getByText('Completed')).toBeDefined()
  })

  it('renders StatusBadge with in_progress state', () => {
    render(<StatusBadge status="in_progress" />)
    expect(screen.getByText('In Progress')).toBeDefined()
  })

  it('renders EmptyState title and description', () => {
    render(
      <EmptyState
        title="No Documents Found"
        description="Upload a document to get started."
      />
    )
    expect(screen.getByText('No Documents Found')).toBeDefined()
    expect(screen.getByText('Upload a document to get started.')).toBeDefined()
  })
})
