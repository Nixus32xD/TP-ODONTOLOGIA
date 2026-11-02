import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, apiRequest } from '../api/cliente'
import Disponibilidad from './Disponibilidad'

vi.mock('../api/cliente', () => ({ apiRequest: vi.fn(), ApiError: class ApiError extends Error {
  constructor(readonly status: number, _codigo: string, _campo: string | null, mensaje: string) { super(mensaje) }
} }))

describe('configuración operativa de horarios, excepciones y bloqueos', () => {
  const api = vi.mocked(apiRequest)
  beforeEach(() => api.mockReset())

  it('deshabilita guardar y descarta el borrador anterior mientras carga otro recurso', async () => {
    let resolverHorarioSegundo: ((respuesta: { dias: { '1': { inicio: string; fin: string }[] } }) => void) | undefined
    api.mockImplementation((rutaBase) => {
      const ruta = String(rutaBase)
      if (ruta.startsWith('/profesionales?')) return Promise.resolve({ items: [
        { id: 'prof-1', nombre: 'Dra. Luna', activo: true },
        { id: 'prof-2', nombre: 'Dr. Sol', activo: true },
      ] }) as never
      if (ruta.startsWith('/boxes?')) return Promise.resolve({ items: [] }) as never
      if (ruta.startsWith('/bloqueos?')) return Promise.resolve({ items: [] }) as never
      if (ruta === '/horarios/profesional/prof-1') return Promise.resolve({
        dias: { '1': [{ inicio: '09:00', fin: '12:00' }] },
      }) as never
      if (ruta === '/horarios/profesional/prof-2') return new Promise((resolver) => {
        resolverHorarioSegundo = resolver as typeof resolverHorarioSegundo
      }) as never
      return Promise.resolve(undefined) as never
    })
    render(<Disponibilidad token="token-recepcion" />)

    expect(await screen.findByLabelText('Fin lunes 1')).toHaveValue('12:00')
    fireEvent.change(screen.getByLabelText('Fin lunes 1'), { target: { value: '11:00' } })
    fireEvent.change(screen.getByLabelText('Recurso'), { target: { value: 'prof-2' } })

    expect(await screen.findByText('Cargando configuración…')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Guardar horario semanal' })).toBeDisabled()
    expect(screen.queryByLabelText('Fin lunes 1')).not.toBeInTheDocument()

    resolverHorarioSegundo?.({ dias: { '1': [{ inicio: '13:00', fin: '15:00' }] } })
    expect(await screen.findByLabelText('Fin lunes 1')).toHaveValue('15:00')
  })

  it('lee y reemplaza el horario semanal; conserva lo vigente si el backend rechaza con 409', async () => {
    api.mockImplementation(async (rutaBase, opciones = {}) => {
      const ruta = String(rutaBase)
      if (ruta.startsWith('/profesionales?')) return { items: [{ id: 'prof-1', nombre: 'Dra. Luna', activo: true }] } as never
      if (ruta.startsWith('/boxes?')) return { items: [{ id: 'box-1', nombre: 'Box 1', activo: true }] } as never
      if (ruta.startsWith('/bloqueos?')) return { items: [] } as never
      if (ruta === '/horarios/profesional/prof-1' && opciones.method === undefined) {
        return { tipo_recurso: 'profesional', recurso_id: 'prof-1', dias: { '1': [{ inicio: '09:00', fin: '12:00' }] } } as never
      }
      if (ruta === '/horarios/profesional/prof-1' && opciones.method === 'PUT') {
        throw new ApiError(409, 'turnos_afectados', null, 'El cambio afecta turnos ya registrados.')
      }
      return undefined as never
    })
    render(<Disponibilidad token="token-recepcion" />)

    const inicio = await screen.findByLabelText('Inicio lunes 1')
    expect(inicio).toHaveValue('09:00')
    fireEvent.change(screen.getByLabelText('Fin lunes 1'), { target: { value: '11:00' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar horario semanal' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('El cambio afecta turnos ya registrados.')
    expect(await screen.findByText(/Horario vigente: .*09:00–12:00/)).toBeInTheDocument()
    expect(api).toHaveBeenCalledWith('/horarios/profesional/prof-1', expect.objectContaining({
      method: 'PUT', token: 'token-recepcion',
      body: JSON.stringify({ dias: { '1': [{ inicio: '09:00', fin: '11:00' }] } }),
    }))
  })

  it('crea y elimina una excepción y bloqueos sólo después de respuestas confirmadas', async () => {
    const llamadas: string[] = []
    let bloqueoExiste = false
    api.mockImplementation(async (rutaBase, opciones = {}) => {
      const ruta = String(rutaBase)
      llamadas.push(`${opciones.method ?? 'GET'} ${ruta}`)
      if (ruta.startsWith('/profesionales?')) return { items: [{ id: 'prof-1', nombre: 'Dra. Luna', activo: true }] } as never
      if (ruta.startsWith('/boxes?')) return { items: [] } as never
      if (ruta.startsWith('/bloqueos?')) return { items: bloqueoExiste ? [{
        id: 'bloqueo-1', tipo_recurso: 'profesional', recurso_id: 'prof-1',
        inicio: '2026-11-02T12:00:00-03:00', fin: '2026-11-02T13:00:00-03:00',
      }] : [] } as never
      if (ruta === '/horarios/profesional/prof-1') return { dias: {} } as never
      if (ruta.endsWith('/excepciones/2026-11-03') && opciones.method === 'GET') {
        throw new ApiError(404, 'recurso_desconocido', null, 'La excepción no existe.')
      }
      if (ruta.endsWith('/excepciones/2026-11-03') && opciones.method === 'PUT') {
        return { id: 'ex-1', fecha: '2026-11-03', tramos: [{ inicio: '10:00', fin: '11:00' }] } as never
      }
      if (ruta.endsWith('/excepciones/2026-11-03') && opciones.method === 'DELETE') return undefined as never
      if (ruta === '/bloqueos' && opciones.method === 'POST') {
        bloqueoExiste = true
        return { id: 'bloqueo-1', tipo_recurso: 'profesional', recurso_id: 'prof-1',
          inicio: '2026-11-02T12:00:00-03:00', fin: '2026-11-02T13:00:00-03:00' } as never
      }
      if (ruta === '/bloqueos/bloqueo-1' && opciones.method === 'DELETE') {
        bloqueoExiste = false
        return undefined as never
      }
      return undefined as never
    })
    render(<Disponibilidad token="token-admin" />)

    fireEvent.change(await screen.findByLabelText('Fecha de excepción'), { target: { value: '2026-11-03' } })
    fireEvent.click(screen.getByRole('button', { name: 'Consultar excepción' }))
    fireEvent.change(screen.getByLabelText('Inicio excepción 1'), { target: { value: '10:00' } })
    fireEvent.change(screen.getByLabelText('Fin excepción 1'), { target: { value: '11:00' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar excepción' }))
    expect(await screen.findByText('Excepción guardada.')).toBeInTheDocument()
    expect(api).toHaveBeenCalledWith('/horarios/profesional/prof-1/excepciones/2026-11-03', expect.objectContaining({
      method: 'PUT', body: JSON.stringify({ tramos: [{ inicio: '10:00', fin: '11:00' }] }), token: 'token-admin',
    }))
    fireEvent.click(screen.getByRole('button', { name: 'Eliminar excepción' }))
    await waitFor(() => expect(llamadas).toContain('DELETE /horarios/profesional/prof-1/excepciones/2026-11-03'))
    fireEvent.click(screen.getByLabelText('No atender ese día'))
    fireEvent.click(screen.getByRole('button', { name: 'Guardar excepción' }))
    await waitFor(() => expect(api).toHaveBeenCalledWith('/horarios/profesional/prof-1/excepciones/2026-11-03', expect.objectContaining({
      method: 'PUT', body: JSON.stringify({ tramos: [] }), token: 'token-admin',
    })))

    fireEvent.change(screen.getByLabelText('Inicio del bloqueo'), { target: { value: '2026-11-02T12:00' } })
    fireEvent.change(screen.getByLabelText('Fin del bloqueo'), { target: { value: '2026-11-02T13:00' } })
    fireEvent.click(screen.getByRole('button', { name: 'Crear bloqueo' }))
    expect(await screen.findByText('Bloqueo creado.')).toBeInTheDocument()
    expect(screen.getByRole('list', { name: 'Bloqueos registrados' }))
      .toHaveTextContent('Bloqueo 2026-11-02 12:00–13:00')
    fireEvent.click(screen.getByRole('button', { name: 'Eliminar bloqueo bloqueo-1' }))
    await waitFor(() => expect(llamadas).toContain('DELETE /bloqueos/bloqueo-1'))
  })
})
