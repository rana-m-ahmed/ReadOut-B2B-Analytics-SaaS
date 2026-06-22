import { describe, it, expect } from 'vitest'
import { SPRING_DEFAULT, SPRING_SNAPPY, HOVER_LIFT, MODAL_OPEN } from '../lib/motion'

describe('Motion Presets', () => {
  it('exports SPRING_DEFAULT with exact stated values', () => {
    expect(SPRING_DEFAULT).toEqual({ stiffness: 220, damping: 26, mass: 1 })
  })
  
  it('exports SPRING_SNAPPY with exact stated values', () => {
    expect(SPRING_SNAPPY).toEqual({ stiffness: 320, damping: 30, mass: 0.9 })
  })
  
  it('exports HOVER_LIFT', () => {
    expect(HOVER_LIFT).toBeDefined()
  })

  it('exports MODAL_OPEN', () => {
    expect(MODAL_OPEN).toBeDefined()
  })
})
