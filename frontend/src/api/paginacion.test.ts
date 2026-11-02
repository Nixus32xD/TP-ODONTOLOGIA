import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from './cliente'
import { listarTodasLasPaginas } from './paginacion'

vi.mock('./cliente', () => ({ apiRequest: vi.fn() }))

describe('lectura paginada completa de catálogos', () => {
  const api = vi.mocked(apiRequest)
  beforeEach(() => api.mockReset())

  it('continúa hasta la última página y mantiene el token', async () => {
    api.mockResolvedValueOnce({ items: Array.from({ length: 100 }, (_, i) => i), limit: 100, offset: 0 })
      .mockResolvedValueOnce({ items: [100], limit: 100, offset: 100 })

    await expect(listarTodasLasPaginas<number>('/pacientes', 'token-demo'))
      .resolves.toEqual(Array.from({ length: 101 }, (_, i) => i))
    expect(api).toHaveBeenNthCalledWith(1, '/pacientes?limit=100&offset=0', { token: 'token-demo' })
    expect(api).toHaveBeenNthCalledWith(2, '/pacientes?limit=100&offset=100', { token: 'token-demo' })
  })

  it('devuelve una colección vacía al recibir una primera página vacía', async () => {
    api.mockResolvedValueOnce({ items: [], limit: 100, offset: 0 })
    await expect(listarTodasLasPaginas('/boxes', 'token-demo')).resolves.toEqual([])
    expect(api).toHaveBeenCalledTimes(1)
  })
})
