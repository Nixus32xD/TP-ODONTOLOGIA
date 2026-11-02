import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, apiRequest } from './cliente'

const respuesta = (status: number, cuerpo?: unknown): Response => ({
  ok: status >= 200 && status < 300,
  status,
  json: vi.fn().mockResolvedValue(cuerpo),
} as unknown as Response)

afterEach(() => vi.unstubAllGlobals())

describe('apiRequest', () => {
  it('envía bearer y JSON, y devuelve la respuesta tipada', async () => {
    const fetchMock = vi.fn().mockResolvedValue(respuesta(201, { id: 7 }))
    vi.stubGlobal('fetch', fetchMock)

    const resultado = await apiRequest<{ id: number }>('/turnos', {
      token: 'bearer-de-prueba',
      method: 'POST',
      body: JSON.stringify({ paciente_id: 'paciente-ficticio' }),
    })

    expect(resultado).toEqual({ id: 7 })
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    const headers = new Headers(init.headers)
    expect(url).toBe('/api/turnos')
    expect(init.method).toBe('POST')
    expect(headers.get('Authorization')).toBe('Bearer bearer-de-prueba')
    expect(headers.get('Accept')).toBe('application/json')
    expect(headers.get('Content-Type')).toBe('application/json')
  })

  it('acepta una respuesta 204 sin intentar leer JSON', async () => {
    const response = respuesta(204)
    const fetchMock = vi.fn().mockResolvedValue(response)
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiRequest<void>('/sesiones/actual', {
      token: 'bearer-de-prueba',
      method: 'DELETE',
    })).resolves.toBeUndefined()
    expect(response.json).not.toHaveBeenCalled()
  })

  it('no envía una cabecera bearer cuando la petición no está autenticada', async () => {
    const fetchMock = vi.fn().mockResolvedValue(respuesta(200, { status: 'ok' }))
    vi.stubGlobal('fetch', fetchMock)

    await apiRequest('/health')

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(new Headers(init.headers).has('Authorization')).toBe(false)
  })

  it('expone el error público de API sin incluir un cuerpo inesperado', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(respuesta(409, {
      codigo: 'conflicto_box', campo: 'box_id', mensaje: 'El box ya está ocupado.',
      detalle_interno: 'SQL secreto',
    })))

    await expect(apiRequest('/turnos', { method: 'POST', body: '{}' }))
      .rejects.toMatchObject({
        name: 'ApiError', status: 409, codigo: 'conflicto_box',
        campo: 'box_id', message: 'El box ya está ocupado.',
      })
    await expect(apiRequest('/turnos')).rejects.toBeInstanceOf(ApiError)
  })

  it('usa un mensaje neutro si la respuesta de error no es JSON válido', async () => {
    const response = respuesta(503)
    vi.mocked(response.json).mockRejectedValue(new Error('secret backend trace'))
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))

    await expect(apiRequest('/turnos')).rejects.toMatchObject({
      status: 503,
      message: 'La API respondió 503.',
    })
  })

  it('reduce una falla de transporte a un error público neutro', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('private hostname and stack')))

    await expect(apiRequest('/turnos')).rejects.toMatchObject({
      status: 0,
      codigo: 'api_no_disponible',
      message: 'No se pudo conectar con la API.',
    })
  })
})
