import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from './api/cliente'
import App from './App'

vi.mock('./api/cliente', async (importOriginal) => {
  const original = await importOriginal<typeof import('./api/cliente')>()
  return { ...original, apiRequest: vi.fn() }
})

describe('aplicación por rol', () => {
  const api = vi.mocked(apiRequest)

  beforeEach(() => api.mockReset())

  function mockConsultasDeAgenda() {
    api.mockImplementation(async () => ({ items: [], limit: 50, offset: 0 }) as never)
  }

  it.each(['administrador', 'recepcion'] as const)(
    'muestra la vista operativa a %s', async (rol) => {
      api.mockResolvedValueOnce({ access_token: 'token-operativo', expires_in: 3600 })
        .mockResolvedValueOnce({
          usuario_id: 'usuario-demo', identificador: `${rol}-demo`, rol,
          profesional_id: null, expira_en: 1_800_000_000,
        })
      mockConsultasDeAgenda()
      render(<App />)
      fireEvent.change(screen.getByLabelText('Usuario'), { target: { value: `${rol}-demo` } })
      fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'password-demo' } })
      fireEvent.click(screen.getByRole('button', { name: 'Iniciar sesión' }))

      expect(await screen.findByRole('heading', { name: 'Operación de agenda' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Cerrar sesión' })).toBeInTheDocument()
    },
  )

  it('limita a Profesional a la consulta propia y no muestra acciones de escritura', async () => {
    api.mockResolvedValueOnce({ access_token: 'token-profesional', expires_in: 3600 })
      .mockResolvedValueOnce({
        usuario_id: 'usuario-profesional', identificador: 'profesional-demo',
        rol: 'profesional', profesional_id: 'profesional-A', expira_en: 1_800_000_000,
      })
    mockConsultasDeAgenda()
    render(<App />)
    fireEvent.change(screen.getByLabelText('Usuario'), { target: { value: 'profesional-demo' } })
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'password-demo' } })
    fireEvent.click(screen.getByRole('button', { name: 'Iniciar sesión' }))

    expect(await screen.findByRole('heading', { name: 'Consulta de agenda propia' }))
      .toBeInTheDocument()
    for (const accion of ['Crear turno', 'Confirmar', 'Cancelar', 'Marcar atendido', 'Registrar ausencia', 'Reprogramar']) {
      expect(screen.queryByRole('button', { name: accion })).not.toBeInTheDocument()
    }
  })
})
