import { render } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Page from '../app/(marketing)/page'

describe('Placeholder Page', () => {
  it('renders successfully', () => {
    const { container } = render(<Page />)
    expect(container).toBeInTheDocument()
  })
})
