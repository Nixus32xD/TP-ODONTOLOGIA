import { apiRequest } from './cliente'

type Pagina<T> = { items: T[]; limit: number; offset: number }

export async function listarTodasLasPaginas<T>(ruta: string, token: string): Promise<T[]> {
  const elementos: T[] = []
  const limite = 100
  let offset = 0

  while (true) {
    const separador = ruta.includes('?') ? '&' : '?'
    const pagina = await apiRequest<Pagina<T>>(
      `${ruta}${separador}limit=${limite}&offset=${offset}`,
      { token },
    )
    elementos.push(...pagina.items)
    if (pagina.items.length < limite) return elementos
    offset += pagina.items.length
  }
}
