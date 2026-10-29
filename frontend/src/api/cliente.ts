// Cliente HTTP del frontend. Las rutas /api/* llegan al backend FastAPI mediante el proxy de Vite.

export type EstadoApi = { status: string }

export async function consultarSalud(): Promise<EstadoApi> {
  const respuesta = await fetch('/api/health')
  if (!respuesta.ok) {
    throw new Error(`La API respondió ${respuesta.status}`)
  }
  return (await respuesta.json()) as EstadoApi
}
