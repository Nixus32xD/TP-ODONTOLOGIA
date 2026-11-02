import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { apiRequest } from '../api/cliente'
import { SessionProvider } from '../auth/session'
import Login from './Login'

vi.mock('../api/cliente', async (importOriginal) => {
  const original = await importOriginal<typeof import('../api/cliente')>()
  return { ...original, apiRequest: vi.fn() }
})

describe('Login', () => {
  it('permite recorrer usuario, contraseña y envío sólo con el teclado', async () => {
    const user = userEvent.setup()
    render(<SessionProvider><Login /></SessionProvider>)

    await user.tab()
    expect(document.activeElement).toBe(screen.getByLabelText('Usuario'))
    await user.tab()
    expect(document.activeElement).toBe(screen.getByLabelText('Contraseña'))
    await user.tab()
    const enviar = screen.getByRole('button', { name: 'Iniciar sesión' })
    expect(document.activeElement).toBe(enviar)
  })

  it('anuncia el envío pendiente y bloquea el doble envío', async () => {
    const api = vi.mocked(apiRequest)
    api.mockReset().mockImplementation(() => new Promise(() => undefined))
    render(<SessionProvider><Login /></SessionProvider>)
    fireEvent.change(screen.getByLabelText('Usuario'), { target: { value: 'recepcion-demo' } })
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'password-demo' } })
    fireEvent.click(screen.getByRole('button', { name: 'Iniciar sesión' }))

    expect(await screen.findByRole('status')).toHaveTextContent('Validando credenciales…')
    expect(screen.getByRole('button', { name: 'Ingresando…' })).toBeDisabled()
  })

  it('presenta controles etiquetados y envía credenciales al backend', async () => {
    const api = vi.mocked(apiRequest)
    api.mockReset()
    api.mockResolvedValueOnce({ access_token: 'token-temporal', expires_in: 1800 })
      .mockResolvedValueOnce({
        usuario_id: 'usuario-recepcion', identificador: 'recepcion-demo',
        rol: 'recepcion', profesional_id: null, expira_en: 1_800_000_000,
      })
    render(<SessionProvider><Login /></SessionProvider>)

    fireEvent.change(screen.getByLabelText('Usuario'), { target: { value: 'recepcion-demo' } })
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'password-demo' } })
    fireEvent.click(screen.getByRole('button', { name: 'Iniciar sesión' }))

    await waitFor(() => expect(api).toHaveBeenNthCalledWith(2, '/sesiones/actual', {
      token: 'token-temporal',
    }))
    expect(api).toHaveBeenNthCalledWith(1, '/sesiones', {
      method: 'POST',
      body: JSON.stringify({ identificador: 'recepcion-demo', password: 'password-demo' }),
    })
  })

  it('expone errores de login sin escribir credenciales ni token en storage', async () => {
    const api = vi.mocked(apiRequest)
    api.mockReset().mockRejectedValue(new Error('Credenciales inválidas.'))
    render(<SessionProvider><Login /></SessionProvider>)

    fireEvent.change(screen.getByLabelText('Usuario'), { target: { value: 'cuenta-demo' } })
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'password-demo' } })
    fireEvent.click(screen.getByRole('button', { name: 'Iniciar sesión' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo completar la solicitud.')
    expect(window.localStorage.length).toBe(0)
    expect(window.sessionStorage.length).toBe(0)
  })
})
