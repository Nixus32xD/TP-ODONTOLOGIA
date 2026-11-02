import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { apiRequest, ApiError, EVENTO_SESION_INVALIDA } from '../api/cliente'

export { EVENTO_SESION_INVALIDA }

export type Rol = 'administrador' | 'recepcion' | 'profesional' | 'paciente'

export type Identidad = {
  usuario_id: string
  identificador: string
  rol: Rol
  profesional_id: string | null
  paciente_id?: string | null
  expira_en: number
}

type RespuestaLogin = { access_token: string; expires_in: number }

type SessionContextValue = {
  token: string | null
  identidad: Identidad | null
  cargando: boolean
  error: string | null
  iniciar: (identificador: string, password: string) => Promise<void>
  cerrar: () => Promise<void>
  limpiarError: () => void
}

const SessionContext = createContext<SessionContextValue | null>(null)

function mensajeDeError(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'No se pudo completar la solicitud. Intente nuevamente.'
}

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [identidad, setIdentidad] = useState<Identidad | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const invalidar = useCallback(() => {
    setToken(null)
    setIdentidad(null)
  }, [])

  useEffect(() => {
    function manejarSesionInvalida() {
      invalidar()
      setError('La sesión expiró o dejó de ser válida. Inicie sesión nuevamente.')
    }
    window.addEventListener(EVENTO_SESION_INVALIDA, manejarSesionInvalida)
    return () => window.removeEventListener(EVENTO_SESION_INVALIDA, manejarSesionInvalida)
  }, [invalidar])

  const iniciar = useCallback(async (identificador: string, password: string) => {
    setCargando(true)
    setError(null)
    try {
      const respuesta = await apiRequest<RespuestaLogin>('/sesiones', {
        method: 'POST',
        body: JSON.stringify({ identificador, password }),
      })
      const actual = await apiRequest<Identidad>('/sesiones/actual', {
        token: respuesta.access_token,
      })
      if (!['administrador', 'recepcion', 'profesional', 'paciente'].includes(actual.rol)
        || (actual.rol === 'paciente' && !actual.paciente_id)) {
        throw new Error('El rol de la cuenta no está habilitado para esta interfaz.')
      }
      setToken(respuesta.access_token)
      setIdentidad(actual)
    } catch (errorDeAcceso) {
      invalidar()
      setError(mensajeDeError(errorDeAcceso))
    } finally {
      setCargando(false)
    }
  }, [invalidar])

  const cerrar = useCallback(async () => {
    const tokenActual = token
    setError(null)
    try {
      if (tokenActual) {
        await apiRequest<void>('/sesiones/actual', {
          method: 'DELETE',
          token: tokenActual,
        })
      }
    } catch {
      setError('Se cerró esta vista, pero no se pudo confirmar la revocación en el servidor.')
    } finally {
      invalidar()
    }
  }, [invalidar, token])

  const value = useMemo<SessionContextValue>(() => ({
    token,
    identidad,
    cargando,
    error,
    iniciar,
    cerrar,
    limpiarError: () => setError(null),
  }), [token, identidad, cargando, error, iniciar, cerrar])

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession(): SessionContextValue {
  const value = useContext(SessionContext)
  if (!value) throw new Error('useSession debe usarse dentro de SessionProvider.')
  return value
}
