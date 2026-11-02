import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../api/cliente'
import Catalogos from './Catalogos'

vi.mock('../api/cliente', () => ({ apiRequest: vi.fn() }))

describe('gestión de catálogos operativos', () => {
  const api = vi.mocked(apiRequest)
  beforeEach(() => api.mockReset())

  it('Recepción puede consultar y editar nombres, pero no cambiar estados', async () => {
    api.mockImplementation(async (rutaBase, opciones = {}) => {
      const ruta = String(rutaBase)
      if (ruta.startsWith('/profesionales?')) return { items: [{ id: 'prof-1', nombre: 'Dra. Luna', activo: true }] } as never
      if (ruta.startsWith('/boxes?')) return { items: [{ id: 'box-1', nombre: 'Box 1', activo: true }] } as never
      if (ruta.startsWith('/prestaciones?')) return { items: [{ id: 'pres-1', nombre: 'Control', activo: true, duracion_minutos: 30 }] } as never
      if (ruta === '/profesionales/prof-1' && opciones.method === 'PATCH') return { id: 'prof-1', nombre: 'Dra. Luna 2', activo: true } as never
      return undefined as never
    })
    render(<Catalogos rol="recepcion" token="token-recepcion" />)

    expect(await screen.findByLabelText('Nombre profesional Dra. Luna')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Nombre profesional Dra. Luna'), { target: { value: 'Dra. Luna 2' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar profesional Dra. Luna' }))

    expect(await screen.findByLabelText('Nombre profesional Dra. Luna')).toHaveValue('Dra. Luna 2')
    expect(screen.queryByRole('button', { name: /activar|desactivar/i })).not.toBeInTheDocument()
    expect(api).toHaveBeenCalledWith('/profesionales/prof-1', expect.objectContaining({
      method: 'PATCH', body: JSON.stringify({ nombre: 'Dra. Luna 2' }), token: 'token-recepcion',
    }))
  })

  it('Administrador puede cambiar el estado y el cambio se confirma tras responder la API', async () => {
    let activo = true
    api.mockImplementation(async (rutaBase, opciones = {}) => {
      const ruta = String(rutaBase)
      if (ruta.startsWith('/profesionales?')) return { items: [{ id: 'prof-1', nombre: 'Dra. Luna', activo }] } as never
      if (ruta.startsWith('/boxes?')) return { items: [] } as never
      if (ruta.startsWith('/prestaciones?')) return { items: [] } as never
      if (ruta === '/profesionales/prof-1' && opciones.method === 'PATCH') {
        activo = JSON.parse(String(opciones.body)).activo
        return { id: 'prof-1', nombre: 'Dra. Luna', activo } as never
      }
      return undefined as never
    })
    render(<Catalogos rol="administrador" token="token-admin" />)

    fireEvent.click(await screen.findByRole('button', { name: 'Desactivar profesional Dra. Luna' }))
    expect(await screen.findByText('Inactivo')).toBeInTheDocument()
    expect(api).toHaveBeenCalledWith('/profesionales/prof-1', expect.objectContaining({
      method: 'PATCH', body: JSON.stringify({ activo: false }), token: 'token-admin',
    }))
  })

  it('crea una prestación con su duración explícita sin asociarla al turno', async () => {
    api.mockImplementation(async (rutaBase, opciones = {}) => {
      const ruta = String(rutaBase)
      if (ruta.startsWith('/profesionales?') || ruta.startsWith('/boxes?')) return { items: [] } as never
      if (ruta.startsWith('/prestaciones?')) return { items: [] } as never
      if (ruta === '/prestaciones' && opciones.method === 'POST') return {
        id: 'pres-2', nombre: 'Consulta ficticia', duracion_minutos: 45, activo: true,
      } as never
      return undefined as never
    })
    render(<Catalogos rol="recepcion" token="token-recepcion" />)

    fireEvent.change(await screen.findByLabelText('Nueva prestación'), { target: { value: 'Consulta ficticia' } })
    fireEvent.change(screen.getByLabelText('Duración en minutos'), { target: { value: '45' } })
    fireEvent.click(screen.getByRole('button', { name: 'Crear prestación' }))

    expect(await screen.findByLabelText('Nombre prestación Consulta ficticia')).toHaveValue('Consulta ficticia')
    expect(api).toHaveBeenCalledWith('/prestaciones', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ nombre: 'Consulta ficticia', duracion_minutos: 45 }),
      token: 'token-recepcion',
    }))
  })
})
