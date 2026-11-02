import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../api/cliente'
import { EVENTO_SESION_INVALIDA, SessionProvider, useSession } from './session'

vi.mock('../api/cliente', async (importOriginal) => {
  const original = await importOriginal<typeof import('../api/cliente')>()
  return { ...original, apiRequest: vi.fn() }
})

const identidad = {
  usuario_id: 'usuario-profesional',
  identificador: 'odontologo-demo',
  rol: 'profesional',
  profesional_id: 'profesional-A',
  expira_en: 1_800_000_000,
}

function Probe() {
  const sesion = useSession()
  return (
    <section>
      <p data-testid="identidad">{sesion.identidad?.rol ?? 'sin sesión'}</p>
      {sesion.error && <p role="alert">{sesion.error}</p>}
      <button onClick={() => void sesion.iniciar('odontologo-demo', 'password-demo')}>
        Entrar
      </button>
      <button onClick={() => void sesion.cerrar()}>Salir</button>
    </section>
  )
}

describe('sesión en memoria', () => {
  const api = vi.mocked(apiRequest)

  beforeEach(() => {
    api.mockReset()
  })

  it('valida identidad con el bearer antes de habilitar la sesión', async () => {
    api.mockResolvedValueOnce({ access_token: 'token-temporal', expires_in: 3600 })
      .mockResolvedValueOnce(identidad)
    const persistir = vi.spyOn(Storage.prototype, 'setItem')
    render(<SessionProvider><Probe /></SessionProvider>)

    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    await waitFor(() => expect(screen.getByTestId('identidad')).toHaveTextContent('profesional'))
    expect(api).toHaveBeenNthCalledWith(1, '/sesiones', {
      method: 'POST',
      body: JSON.stringify({ identificador: 'odontologo-demo', password: 'password-demo' }),
    })
    expect(api).toHaveBeenNthCalledWith(2, '/sesiones/actual', { token: 'token-temporal' })
    expect(persistir).not.toHaveBeenCalled()
    expect(window.localStorage.length).toBe(0)
    expect(window.sessionStorage.length).toBe(0)
  })

  it.each(['administrador', 'recepcion'] as const)(
    'permite el acceso de %s sin vínculo profesional', async (rol) => {
      api.mockResolvedValueOnce({ access_token: `token-${rol}`, expires_in: 3600 })
        .mockResolvedValueOnce({ ...identidad, rol, profesional_id: null })
      render(<SessionProvider><Probe /></SessionProvider>)

      fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

      await waitFor(() => expect(screen.getByTestId('identidad')).toHaveTextContent(rol))
    },
  )

  it('elimina la sesión en memoria cuando cualquier request informa 401', async () => {
    api.mockResolvedValueOnce({ access_token: 'token-temporal', expires_in: 3600 })
      .mockResolvedValueOnce(identidad)
    render(<SessionProvider><Probe /></SessionProvider>)
    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    await waitFor(() => expect(screen.getByTestId('identidad')).toHaveTextContent('profesional'))

    act(() => window.dispatchEvent(new Event(EVENTO_SESION_INVALIDA)))

    expect(screen.getByTestId('identidad')).toHaveTextContent('sin sesión')
    expect(screen.getByRole('alert')).toHaveTextContent('La sesión expiró o dejó de ser válida. Inicie sesión nuevamente.')
  })

  it('intenta revocar la sesión y la borra localmente aunque falle la revocación', async () => {
    api.mockResolvedValueOnce({ access_token: 'token-temporal', expires_in: 3600 })
      .mockResolvedValueOnce(identidad)
      .mockRejectedValueOnce(new Error('fallo de red'))
    render(<SessionProvider><Probe /></SessionProvider>)
    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    await waitFor(() => expect(screen.getByTestId('identidad')).toHaveTextContent('profesional'))

    fireEvent.click(screen.getByRole('button', { name: 'Salir' }))

    await waitFor(() => expect(screen.getByTestId('identidad')).toHaveTextContent('sin sesión'))
    expect(api).toHaveBeenNthCalledWith(3, '/sesiones/actual', {
      method: 'DELETE', token: 'token-temporal',
    })
  })
})
