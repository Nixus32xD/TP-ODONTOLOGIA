import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../api/cliente'
import PortalPaciente from './PortalPaciente'

vi.mock('../api/cliente', async (importOriginal) => {
  const original = await importOriginal<typeof import('../api/cliente')>()
  return { ...original, apiRequest: vi.fn() }
})

describe('portal sintético del paciente', () => {
  const api = vi.mocked(apiRequest)
  const slot = { inicio: '2026-11-03T16:00:00Z', fin: '2026-11-03T16:30:00Z' }
  const turno = {
    turno_id: 17, inicio: slot.inicio, fin: slot.fin, estado: 'reservado', version: 2,
  }

  beforeEach(() => api.mockReset())

  it('reserva sólo el inicio elegido y envía una clave idempotente', async () => {
    api.mockImplementation(async (ruta) => {
      if (String(ruta) === '/mis-turnos') return { items: [] } as never
      if (String(ruta).startsWith('/portal/disponibilidad')) {
        return { fecha: '2026-11-03', items: [slot] } as never
      }
      return { ...turno, turno_id: 18 } as never
    })
    render(<PortalPaciente token="token-paciente" />)
    fireEvent.change(await screen.findByLabelText('Horario disponible'), {
      target: { value: slot.inicio },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Reservar turno' }))

    await screen.findByText('Reserva realizada.')
    const llamada = api.mock.calls.find(([ruta, opciones]) =>
      String(ruta) === '/mis-turnos' && opciones?.method === 'POST')
    expect(llamada).toBeDefined()
    expect(llamada?.[1]?.body).toBe(JSON.stringify({ inicio: slot.inicio }))
    expect(new Headers(llamada?.[1]?.headers).get('Idempotency-Key')).toBeTruthy()
  })

  it('permite cancelar y reprogramar sólo mediante rutas del portal', async () => {
    api.mockImplementation(async (ruta, opciones = {}) => {
      if (String(ruta) === '/mis-turnos') return { items: [turno] } as never
      if (String(ruta).startsWith('/portal/disponibilidad')) {
        return { fecha: '2026-11-03', items: [{
          inicio: '2026-11-03T17:00:00Z', fin: '2026-11-03T17:30:00Z',
        }] } as never
      }
      if (opciones.method === 'POST' && String(ruta).endsWith('/reprogramacion')) {
        return { ...turno, inicio: '2026-11-03T17:00:00Z', version: 3 } as never
      }
      if (opciones.method === 'POST' && String(ruta).endsWith('/cancelacion')) {
        return { ...turno, estado: 'cancelado', version: 4 } as never
      }
      return {} as never
    })
    render(<PortalPaciente token="token-paciente" />)
    fireEvent.change(await screen.findByLabelText('Horario disponible'), {
      target: { value: '2026-11-03T17:00:00Z' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Reprogramar al horario elegido' }))
    await screen.findByText('Turno reprogramado.')
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
    await screen.findByText('Turno cancelado.')

    expect(api.mock.calls.some(([ruta]) => String(ruta) === '/mis-turnos/17/reprogramacion')).toBe(true)
    expect(api.mock.calls.some(([ruta]) => String(ruta) === '/mis-turnos/17/cancelacion')).toBe(true)
    expect(api.mock.calls.some(([ruta]) => String(ruta).startsWith('/turnos'))).toBe(false)
  })

  it('al cambiar la fecha limpia franjas anteriores y consulta sólo la fecha nueva', async () => {
    let resolverNuevaFecha: ((resultado: unknown) => void) | undefined
    api.mockImplementation((ruta) => {
      if (String(ruta) === '/mis-turnos') return Promise.resolve({ items: [] }) as never
      if (String(ruta) === '/portal/disponibilidad?fecha=2026-11-04') {
        return new Promise((resolve) => { resolverNuevaFecha = resolve }) as never
      }
      return Promise.resolve({
        fecha: '2026-11-03', items: [slot],
      }) as never
    })
    render(<PortalPaciente token="token-paciente" />)
    await screen.findByRole('option', { name: /3 nov 2026/ })

    fireEvent.change(screen.getByLabelText('Fecha'), { target: { value: '2026-11-04' } })

    await waitFor(() => expect(api).toHaveBeenCalledWith(
      '/portal/disponibilidad?fecha=2026-11-04', { token: 'token-paciente' },
    ))
    expect(screen.queryByRole('option', { name: /3 nov 2026/ })).not.toBeInTheDocument()

    resolverNuevaFecha?.({
      fecha: '2026-11-04', items: [{
        inicio: '2026-11-04T16:00:00Z', fin: '2026-11-04T16:30:00Z',
      }],
    })
    await screen.findByRole('option', { name: /4 nov 2026/ })
  })

  it('ignora una respuesta tardía de la fecha anterior', async () => {
    let resolverFechaAnterior: ((resultado: unknown) => void) | undefined
    api.mockImplementation((ruta) => {
      if (String(ruta) === '/mis-turnos') return Promise.resolve({ items: [] }) as never
      if (String(ruta).startsWith('/portal/disponibilidad?fecha=')) {
        if (String(ruta).endsWith('2026-11-04')) {
          return Promise.resolve({ fecha: '2026-11-04', items: [{
            inicio: '2026-11-04T16:00:00Z', fin: '2026-11-04T16:30:00Z',
          }] }) as never
        }
        return new Promise((resolve) => { resolverFechaAnterior = resolve }) as never
      }
      return {} as never
    })
    render(<PortalPaciente token="token-paciente" />)

    fireEvent.change(screen.getByLabelText('Fecha'), { target: { value: '2026-11-04' } })
    await screen.findByRole('option', { name: /4 nov 2026/ })
    resolverFechaAnterior?.({ fecha: '2026-11-03', items: [slot] })

    await waitFor(() => expect(
      screen.queryByRole('option', { name: /3 nov 2026/ }),
    ).not.toBeInTheDocument())
    expect(screen.getByRole('option', { name: /4 nov 2026/ })).toBeInTheDocument()
  })

  it('reutiliza la clave tras una respuesta ambigua y la cambia para otro horario', async () => {
    let intentosReserva = 0
    let lecturasTurnos = 0
    let lecturasDisponibilidad = 0
    const otraFranja = {
      inicio: '2026-11-03T17:00:00Z', fin: '2026-11-03T17:30:00Z',
    }
    api.mockImplementation(async (ruta, opciones = {}) => {
      if (String(ruta) === '/mis-turnos' && opciones.method === 'POST') {
        intentosReserva += 1
        if (intentosReserva === 1) throw new Error('timeout ambiguo')
        return { ...turno, turno_id: 18 } as never
      }
      if (String(ruta) === '/mis-turnos') {
        lecturasTurnos += 1
        return { items: lecturasTurnos === 1 ? [] : [turno] } as never
      }
      if (String(ruta).startsWith('/portal/disponibilidad')) {
        lecturasDisponibilidad += 1
        return {
          fecha: '2026-11-03',
          items: lecturasDisponibilidad === 1 ? [slot] : [slot, otraFranja],
        } as never
      }
      return {} as never
    })
    render(<PortalPaciente token="token-paciente" />)
    fireEvent.change(await screen.findByLabelText('Horario disponible'), {
      target: { value: slot.inicio },
    })
    const boton = screen.getByRole('button', { name: 'Reservar turno' })
    fireEvent.click(boton)
    await screen.findByRole('alert')
    fireEvent.click(boton)
    await screen.findByText('Reserva realizada.')

    const reservas = () => api.mock.calls.filter(([ruta, opciones]) =>
      String(ruta) === '/mis-turnos' && opciones?.method === 'POST')
    const claves = reservas().map(([, opciones]) =>
      new Headers(opciones?.headers).get('Idempotency-Key'))
    expect(claves[1]).toBe(claves[0])

    fireEvent.change(await screen.findByLabelText('Horario disponible'), {
      target: { value: otraFranja.inicio },
    })
    fireEvent.click(boton)
    await waitFor(() => expect(reservas()).toHaveLength(3))
    const claveNuevoHorario = new Headers(reservas()[2][1]?.headers).get('Idempotency-Key')
    expect(claveNuevoHorario).toBeTruthy()
    expect(claveNuevoHorario).not.toBe(claves[0])
  })

  it('usa claves distintas para reprogramar y cancelar el mismo turno', async () => {
    api.mockImplementation(async (ruta) => {
      if (String(ruta).endsWith('/reprogramacion')) {
        return { ...turno, version: turno.version + 1 } as never
      }
      if (String(ruta).endsWith('/cancelacion')) {
        return { ...turno, estado: 'cancelado', version: turno.version + 1 } as never
      }
      if (String(ruta) === '/mis-turnos') return { items: [turno] } as never
      if (String(ruta).startsWith('/portal/disponibilidad')) {
        return { fecha: '2026-11-03', items: [slot] } as never
      }
      return {} as never
    })
    render(<PortalPaciente token="token-paciente" />)
    fireEvent.change(await screen.findByLabelText('Horario disponible'), {
      target: { value: slot.inicio },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Reprogramar al horario elegido' }))
    await screen.findByText('Turno reprogramado.')
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
    await screen.findByText('Turno cancelado.')

    const reprogramacion = api.mock.calls.find(([ruta]) =>
      String(ruta).endsWith('/reprogramacion'))
    const cancelacion = api.mock.calls.find(([ruta]) =>
      String(ruta).endsWith('/cancelacion'))
    const claveReprogramacion = new Headers(reprogramacion?.[1]?.headers)
      .get('Idempotency-Key')
    const claveCancelacion = new Headers(cancelacion?.[1]?.headers).get('Idempotency-Key')
    expect(claveReprogramacion).toBeTruthy()
    expect(claveCancelacion).toBeTruthy()
    expect(claveCancelacion).not.toBe(claveReprogramacion)
  })
})
