// Cliente HTTP del frontend. El proxy de Vite envía /api/* a FastAPI.

export type EstadoApi = { status: string }
export const EVENTO_SESION_INVALIDA = 'agenda:sesion-invalida'

export type ErrorApiPublico = {
  codigo: string
  campo: string | null
  mensaje: string
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly codigo: string,
    readonly campo: string | null,
    mensaje: string,
  ) {
    super(mensaje)
    this.name = 'ApiError'
  }
}

export type OpcionesApi = Omit<RequestInit, 'headers'> & {
  token?: string
  headers?: HeadersInit
}

export async function apiRequest<T>(ruta: string, opciones: OpcionesApi = {}): Promise<T> {
  const { token, headers: headersIniciales, ...init } = opciones
  const headers = new Headers(headersIniciales)
  headers.set('Accept', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (init.body !== undefined && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  let respuesta: Response
  try {
    respuesta = await fetch(`/api${ruta.startsWith('/') ? ruta : `/${ruta}`}`, {
      ...init,
      headers,
    })
  } catch {
    throw new ApiError(0, 'api_no_disponible', null, 'No se pudo conectar con la API.')
  }

  if (!respuesta.ok) {
    if (respuesta.status === 401 && typeof window !== 'undefined') {
      window.dispatchEvent(new Event(EVENTO_SESION_INVALIDA))
    }
    let error: ErrorApiPublico | undefined
    try {
      const cuerpo: unknown = await respuesta.json()
      if (cuerpo && typeof cuerpo === 'object') {
        const problema = cuerpo as Partial<ErrorApiPublico>
        if (typeof problema.codigo === 'string' && typeof problema.mensaje === 'string') {
          error = {
            codigo: problema.codigo,
            campo: typeof problema.campo === 'string' ? problema.campo : null,
            mensaje: problema.mensaje,
          }
        }
      }
    } catch {
      // El detalle interno del transporte no se expone en el mensaje de usuario.
    }
    throw new ApiError(
      respuesta.status,
      error?.codigo ?? 'api_error',
      error?.campo ?? null,
      error?.mensaje ?? `La API respondió ${respuesta.status}.`,
    )
  }

  if (respuesta.status === 204) return undefined as T
  return (await respuesta.json()) as T
}

export function consultarSalud(): Promise<EstadoApi> {
  return apiRequest<EstadoApi>('/health')
}
