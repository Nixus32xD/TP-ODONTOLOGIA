import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../api/cliente'
import Reportes from './Reportes'

vi.mock('../api/cliente', async (importOriginal) => {
  const original = await importOriginal<typeof import('../api/cliente')>()
  return { ...original, apiRequest: vi.fn() }
})

describe('reportes operativos', () => {
  const api = vi.mocked(apiRequest)

  beforeEach(() => api.mockReset())

  it('consulta agenda para Recepción y no expone el panel financiero', async () => {
    api.mockResolvedValueOnce({
      desde: '2026-11-02', hasta: '2026-11-03', zona: 'America/Argentina/Mendoza',
      dias: [{
        fecha: '2026-11-02', estados: {
          reservado: { cantidad: 2, minutos: 60 }, confirmado: { cantidad: 0, minutos: 0 },
          atendido: { cantidad: 0, minutos: 0 }, ausente: { cantidad: 0, minutos: 0 },
          cancelado: { cantidad: 0, minutos: 0 },
        }, recursos: { profesionales: [], boxes: [] },
      }],
    } as never)
    render(<Reportes rol="recepcion" token="token-recepcion" />)
    fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '2026-11-02' } })
    fireEvent.change(screen.getByLabelText('Hasta (exclusivo)'), { target: { value: '2026-11-03' } })
    fireEvent.click(screen.getByRole('button', { name: 'Consultar reportes' }))

    expect(await screen.findByText('Reservados')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Resumen financiero' })).not.toBeInTheDocument()
    expect(api).toHaveBeenCalledWith(
      '/reportes/agenda?desde=2026-11-02&hasta=2026-11-03', { token: 'token-recepcion' },
    )
  })

  it('muestra finanzas únicamente a Administración y ofrece CSV autenticado', async () => {
    api.mockImplementation(async (ruta) => {
      if (String(ruta).startsWith('/reportes/agenda?')) {
        return { desde: '2026-11-02', hasta: '2026-11-03', zona: 'America/Argentina/Mendoza', dias: [] } as never
      }
      if (String(ruta).startsWith('/reportes/finanzas?')) {
        return {
          saldo_apertura_ars: '20.00', dias: [{ fecha: '2026-11-02',
            cargos: { cantidad: 1, importe_ars: '10.00' },
            cobros: { cantidad: 1, importe_ars: '5.00' },
            reversiones: { cantidad: 0, importe_ars: '0.00' },
            neto_ars: '5.00', saldo_cierre_ars: '25.00' }],
        } as never
      }
      if (ruta === undefined) return {} as never
      throw new Error(`Ruta inesperada: ${String(ruta)}`)
    })
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true, status: 200, blob: async () => new Blob(['csv'], { type: 'text/csv' }),
    })
    vi.stubGlobal('fetch', fetchMock)
    vi.stubGlobal('URL', { ...URL, createObjectURL: vi.fn(() => 'blob:report'), revokeObjectURL: vi.fn() })
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined)

    render(<Reportes rol="administrador" token="token-admin" />)
    fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '2026-11-02' } })
    fireEvent.change(screen.getByLabelText('Hasta (exclusivo)'), { target: { value: '2026-11-03' } })
    fireEvent.click(screen.getByRole('button', { name: 'Consultar reportes' }))
    expect(await screen.findByRole('heading', { name: 'Resumen financiero' })).toBeInTheDocument()
    expect(screen.getByText('25.00')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Descargar finanzas CSV' }))
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/api/reportes/finanzas.csv?'),
      expect.objectContaining({ headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }) }))
    expect(click).toHaveBeenCalled()
    click.mockRestore()
  })

  it('anuncia agenda vacía para Recepción', async () => {
    api.mockResolvedValueOnce({
      desde: '2026-11-02', hasta: '2026-11-03', zona: 'America/Argentina/Mendoza', dias: [],
    } as never)
    render(<Reportes rol="recepcion" token="token-recepcion" />)
    fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '2026-11-02' } })
    fireEvent.change(screen.getByLabelText('Hasta (exclusivo)'), { target: { value: '2026-11-03' } })
    fireEvent.click(screen.getByRole('button', { name: 'Consultar reportes' }))

    expect(await screen.findByRole('status')).toHaveTextContent('No hay datos de agenda para el período consultado.')
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('anuncia finanzas vacías sin ocultar la agenda con actividad', async () => {
    api.mockImplementation(async (ruta) => {
      if (String(ruta).startsWith('/reportes/agenda?')) {
        return {
          desde: '2026-11-02', hasta: '2026-11-03', zona: 'America/Argentina/Mendoza',
          dias: [{ fecha: '2026-11-02', estados: { reservado: { cantidad: 1, minutos: 30 } },
            recursos: { profesionales: [], boxes: [] } }],
        } as never
      }
      return { saldo_apertura_ars: '0.00', dias: [] } as never
    })
    render(<Reportes rol="administrador" token="token-admin" />)
    fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '2026-11-02' } })
    fireEvent.change(screen.getByLabelText('Hasta (exclusivo)'), { target: { value: '2026-11-03' } })
    fireEvent.click(screen.getByRole('button', { name: 'Consultar reportes' }))

    expect(await screen.findByRole('status')).toHaveTextContent('No hay movimientos financieros para el período consultado.')
    expect(screen.getByRole('heading', { name: 'Resumen de agenda' })).toBeInTheDocument()
    expect(screen.getByRole('table', { name: 'Turnos por estado' })).toBeInTheDocument()
  })

  it('mantiene los errores de consulta como alertas y no como estados vacíos', async () => {
    api.mockRejectedValueOnce(new Error('No se pudieron consultar los reportes.'))
    render(<Reportes rol="recepcion" token="token-recepcion" />)
    fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '2026-11-02' } })
    fireEvent.change(screen.getByLabelText('Hasta (exclusivo)'), { target: { value: '2026-11-03' } })
    fireEvent.click(screen.getByRole('button', { name: 'Consultar reportes' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudieron consultar los reportes.')
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})
