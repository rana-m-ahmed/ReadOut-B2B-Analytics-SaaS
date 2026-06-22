import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiFetch, ApiError } from '../lib/api/client'

// Mock the Supabase module
vi.mock('../lib/supabase/client', () => {
  return {
    createClient: () => ({
      auth: {
        getSession: vi.fn().mockResolvedValue({
          data: {
            session: { access_token: 'fake-jwt-token' }
          }
        })
      }
    })
  }
})

describe('apiFetch', () => {
  const originalFetch = global.fetch

  beforeEach(() => {
    vi.resetAllMocks()
    global.fetch = vi.fn()
  })

  afterAll(() => {
    global.fetch = originalFetch
  })

  it('attaches Supabase JWT and merges headers', async () => {
    const mockResponse = { ok: true, json: () => Promise.resolve({ data: 'ok' }), status: 200 }
    vi.mocked(global.fetch).mockResolvedValue(mockResponse as unknown as Response)

    const result = await apiFetch('/test', { headers: { 'X-Custom': 'value' } })

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/test'),
      expect.objectContaining({
        headers: {
          'Authorization': 'Bearer fake-jwt-token',
          'X-Custom': 'value',
        }
      })
    )
    expect(result).toEqual({ data: 'ok' })
  })

  it('retries exactly once on 503', async () => {
    const mockResponse503 = { ok: false, status: 503 }
    const mockResponseOk = { ok: true, json: () => Promise.resolve({ data: 'recovered' }), status: 200 }
    
    vi.mocked(global.fetch)
      .mockResolvedValueOnce(mockResponse503 as unknown as Response)
      .mockResolvedValueOnce(mockResponseOk as unknown as Response)

    const result = await apiFetch('/test-retry')

    expect(global.fetch).toHaveBeenCalledTimes(2)
    expect(result).toEqual({ data: 'recovered' })
  })

  it('parses structured API errors and throws ApiError', async () => {
    const errorBody = { error: { code: 'not_found', message: 'Resource missing' } }
    const mockResponse = { 
      ok: false, 
      status: 404, 
      json: () => Promise.resolve(errorBody) 
    }
    vi.mocked(global.fetch).mockResolvedValue(mockResponse as unknown as Response)

    await expect(apiFetch('/test-error')).rejects.toThrow(ApiError)
    await expect(apiFetch('/test-error')).rejects.toMatchObject({
      code: 'not_found',
      message: 'Resource missing'
    })
    
    // Ensure it does not retry a 4xx
    expect(global.fetch).toHaveBeenCalledTimes(2) // once for the first rejects, once for the second
  })

  it('handles network failure with retry', async () => {
    const mockResponseOk = { ok: true, json: () => Promise.resolve({ data: 'recovered' }), status: 200 }
    
    vi.mocked(global.fetch)
      .mockRejectedValueOnce(new TypeError('Failed to fetch'))
      .mockResolvedValueOnce(mockResponseOk as unknown as Response)

    const result = await apiFetch('/test-network-retry')

    expect(global.fetch).toHaveBeenCalledTimes(2)
    expect(result).toEqual({ data: 'recovered' })
  })
})
