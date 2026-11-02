import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, apiRequest } from '../api/cliente'
import AtencionesClinicas from './AtencionesClinicas'

vi.mock('../api/cliente', async (importOriginal) => {
  const original = await importOriginal<typeof import('../api/cliente')>()
  return { ...original, apiRequest: vi.fn() }
})

describe('vista clínica de Profesional', () => {
  const api = vi.mocked(apiRequest)
  const atencion = {
    turno_id: 41, paciente_id: 'paciente-sintetico-A',
    paciente_nombre: 'Paciente Sintético A',
    inicio: '2026-11-02T12:00:00Z', fin: '2026-11-02T12:30:00Z',
  }

  beforeEach(() => api.mockReset())

  it('carga las secciones sólo tras seleccionar una atención atendida propia', async () => {
    api.mockResolvedValueOnce({ items: [atencion], limit: 25, offset: 0 })
      .mockResolvedValueOnce({
        items: [{ id: 'version-1', paciente_id: atencion.paciente_id,
          profesional_id: 'profesional-sintetico-A', version: 1,
          created_at: '2026-11-02T12:31:00Z', hallazgos: [] }], version_vigente: 1,
      })
      .mockResolvedValueOnce({ items: [] })
    render(<AtencionesClinicas token="token-profesional" />)

    await screen.findByRole('option', { name: /Paciente Sintético A/ })
    expect(api).toHaveBeenCalledWith('/profesional/atenciones-atendidas?limit=25&offset=0',
      expect.objectContaining({ token: 'token-profesional' }))
    expect(api).toHaveBeenCalledTimes(1)
    fireEvent.change(screen.getByLabelText('Atención atendida'), { target: { value: '41' } })

    expect(await screen.findByRole('heading', { name: 'Odontograma' })).toBeInTheDocument()
    expect(await screen.findByText('sin registros de hallazgo')).toBeInTheDocument()
    expect(screen.getByText('Versión vigente: 1')).toBeInTheDocument()
    expect(api).toHaveBeenCalledWith(`/pacientes/${atencion.paciente_id}/odontograma`,
      expect.objectContaining({ token: 'token-profesional' }))
    expect(api).toHaveBeenCalledWith(`/pacientes/${atencion.paciente_id}/planes`,
      expect.objectContaining({ token: 'token-profesional' }))
  })

  it('muestra una lista vacía sin hacer llamadas clínicas', async () => {
    api.mockResolvedValueOnce({ items: [], limit: 25, offset: 0 })
    render(<AtencionesClinicas token="token-profesional" />)

    expect(await screen.findByText('No hay atenciones atendidas para mostrar.')).toBeInTheDocument()
    await waitFor(() => expect(api).toHaveBeenCalledTimes(1))
    expect(api.mock.calls.some(([ruta]) => String(ruta).includes('/odontograma'))).toBe(false)
    expect(api.mock.calls.some(([ruta]) => String(ruta).includes('/planes'))).toBe(false)
  })

  it('permite avanzar y volver entre páginas del listado de atenciones', async () => {
    const paginaSiguiente = Array.from({ length: 25 }, (_, indice) => ({
      ...atencion, turno_id: 100 + indice, paciente_id: `paciente-${indice}`,
    }))
    api.mockResolvedValueOnce({ items: paginaSiguiente, limit: 25, offset: 0 })
      .mockResolvedValueOnce({ items: paginaSiguiente, limit: 25, offset: 25 })
      .mockResolvedValueOnce({ items: paginaSiguiente, limit: 25, offset: 0 })
    render(<AtencionesClinicas token="token-profesional" />)
    await screen.findByText('Página 1')
    fireEvent.click(screen.getByRole('button', { name: 'Atenciones siguientes' }))
    expect(await screen.findByText('Página 2')).toBeInTheDocument()
    expect(api).toHaveBeenCalledWith('/profesional/atenciones-atendidas?limit=25&offset=25',
      expect.objectContaining({ token: 'token-profesional' }))
    fireEvent.click(screen.getByRole('button', { name: 'Atenciones anteriores' }))
    expect(await screen.findByText('Página 1')).toBeInTheDocument()
    expect(api).toHaveBeenCalledWith('/profesional/atenciones-atendidas?limit=25&offset=0',
      expect.objectContaining({ token: 'token-profesional' }))
  })

  it('envía las superficies elegidas y presenta con claridad el rechazo 422', async () => {
    api.mockImplementation(async (ruta, opciones = {}) => {
      if (typeof ruta !== 'string') return {} as never
      if (ruta === '/profesional/atenciones-atendidas?limit=25&offset=0') {
        return { items: [atencion], limit: 25, offset: 0 } as never
      }
      if (ruta === `/pacientes/${atencion.paciente_id}/odontograma` && opciones.method === 'POST') {
        throw new ApiError(422, 'entrada_invalida', 'hallazgos',
          'Los códigos del odontograma no son válidos.')
      }
      if (ruta.endsWith('/odontograma')) return { items: [], version_vigente: null } as never
      if (ruta.endsWith('/planes')) return { items: [] } as never
      throw new Error(`Ruta inesperada en prueba: ${ruta}`)
    })
    render(<AtencionesClinicas token="token-profesional" />)
    await screen.findByRole('option', { name: /Paciente Sintético A/ })
    fireEvent.change(screen.getByLabelText('Atención atendida'), { target: { value: '41' } })
    await screen.findByRole('heading', { name: 'Odontograma' })
    fireEvent.change(screen.getByLabelText('Pieza FDI'), { target: { value: '11' } })
    fireEvent.change(screen.getByLabelText('Superficies (separadas por coma)'),
      { target: { value: 'M, V' } })
    fireEvent.change(screen.getByLabelText('Observación sintética (opcional)'),
      { target: { value: 'Dato de demostración' } })
    fireEvent.click(screen.getByRole('button', { name: 'Registrar nueva versión' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Los códigos del odontograma no son válidos.')
    expect(api).toHaveBeenCalledWith(`/pacientes/${atencion.paciente_id}/odontograma`,
      expect.objectContaining({ method: 'POST', token: 'token-profesional',
        body: JSON.stringify({ hallazgos: [{ pieza_fdi: '11', superficies: ['M', 'V'],
          observacion: 'Dato de demostración' }] }),
      }))
  })

  it('crea un plan manual y envía el estado operativo elegido', async () => {
    let planes: Array<{ id: string; estado: 'propuesto' | 'en_curso'; created_at: string; etapas: Array<{ orden: number; prestacion_id: string }> }> = []
    api.mockImplementation(async (ruta, opciones = {}) => {
      if (typeof ruta !== 'string') return {} as never
      if (ruta === '/profesional/atenciones-atendidas?limit=25&offset=0') {
        return { items: [atencion], limit: 25, offset: 0 } as never
      }
      if (ruta.endsWith('/odontograma')) return { items: [], version_vigente: null } as never
      if (ruta.endsWith('/planes') && !opciones.method) return { items: planes } as never
      if (ruta.endsWith('/planes') && opciones.method === 'POST') {
        expect(opciones.body).toBe(JSON.stringify({ prestaciones_ids: ['prestacion-sintetica-A'] }))
        planes = [{ id: 'plan-sintetico-A', estado: 'propuesto', created_at: '2026-11-02T12:40:00Z',
          etapas: [{ orden: 1, prestacion_id: 'prestacion-sintetica-A' }] }]
        return planes[0] as never
      }
      if (ruta === '/planes/plan-sintetico-A/estado') {
        expect(opciones.body).toBe(JSON.stringify({ estado: 'en_curso' }))
        planes = planes.map((plan) => ({ ...plan, estado: 'en_curso' }))
        return planes[0] as never
      }
      throw new Error(`Ruta inesperada en prueba: ${ruta}`)
    })
    render(<AtencionesClinicas token="token-profesional" />)
    await screen.findByRole('option', { name: /Paciente Sintético A/ })
    fireEvent.change(screen.getByLabelText('Atención atendida'), { target: { value: '41' } })
    await screen.findByRole('heading', { name: 'Planes manuales' })
    fireEvent.change(screen.getByLabelText('IDs de prestaciones activas (separados por coma)'),
      { target: { value: 'prestacion-sintetica-A' } })
    fireEvent.click(screen.getByRole('button', { name: 'Crear plan' }))
    const iniciar = await screen.findByRole('button', { name: 'Iniciar plan' })
    fireEvent.click(iniciar)

    expect(await screen.findByText('Plan plan-sintetico-A — en_curso')).toBeInTheDocument()
    expect(api).toHaveBeenCalledWith('/planes/plan-sintetico-A/estado',
      expect.objectContaining({ method: 'PATCH', token: 'token-profesional' }))
  })
})
