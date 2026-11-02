import { FormEvent, useEffect, useState } from 'react'
import { apiRequest, ApiError } from '../api/cliente'
import { listarTodasLasPaginas } from '../api/paginacion'

type Rol = 'administrador' | 'recepcion'
type TipoCatalogo = 'profesionales' | 'boxes' | 'prestaciones'
type Recurso = { id: string; nombre: string; activo: boolean; duracion_minutos?: number }
type Colecciones = Record<TipoCatalogo, Recurso[]>

const catalogos: Array<{ tipo: TipoCatalogo; nombre: string; singular: string }> = [
  { tipo: 'profesionales', nombre: 'Profesionales', singular: 'profesional' },
  { tipo: 'boxes', nombre: 'Boxes', singular: 'box' },
  { tipo: 'prestaciones', nombre: 'Prestaciones', singular: 'prestación' },
]

const vacios: Colecciones = { profesionales: [], boxes: [], prestaciones: [] }

function mensaje(error: unknown): string {
  return error instanceof ApiError ? error.message : 'No se pudo completar la operación. Intente nuevamente.'
}

export default function Catalogos({ rol, token }: { rol: Rol; token: string }) {
  const [colecciones, setColecciones] = useState<Colecciones>(vacios)
  const [nombres, setNombres] = useState<Record<TipoCatalogo, string>>({
    profesionales: '', boxes: '', prestaciones: '',
  })
  const [duracionPrestacion, setDuracionPrestacion] = useState('30')
  const [borradores, setBorradores] = useState<Record<string, { nombre?: string; duracion_minutos?: number }>>({})
  const [cargando, setCargando] = useState(true)
  const [guardando, setGuardando] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [mensajeEstado, setMensajeEstado] = useState<string | null>(null)

  async function cargar() {
    setCargando(true)
    setError(null)
    try {
      const [profesionales, boxes, prestaciones] = await Promise.all([
        listarTodasLasPaginas<Recurso>('/profesionales', token),
        listarTodasLasPaginas<Recurso>('/boxes', token),
        listarTodasLasPaginas<Recurso>('/prestaciones', token),
      ])
      setColecciones({ profesionales, boxes, prestaciones })
    } catch (fallo) {
      setError(mensaje(fallo))
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => { void cargar() }, [token])

  async function crear(evento: FormEvent<HTMLFormElement>, tipo: TipoCatalogo) {
    evento.preventDefault()
    const nombre = nombres[tipo].trim()
    if (!nombre) return
    setGuardando(`nuevo-${tipo}`)
    setError(null)
    setMensajeEstado(null)
    try {
      const datos = tipo === 'prestaciones'
        ? { nombre, duracion_minutos: Number(duracionPrestacion) }
        : { nombre }
      const creado = await apiRequest<Recurso>(`/${tipo}`, {
        method: 'POST', token, body: JSON.stringify(datos),
      })
      setColecciones((actual) => ({ ...actual, [tipo]: [...actual[tipo], creado] }))
      setNombres((actual) => ({ ...actual, [tipo]: '' }))
      setMensajeEstado(`${catalogos.find((item) => item.tipo === tipo)?.singular} creado.`)
    } catch (fallo) {
      setError(mensaje(fallo))
    } finally {
      setGuardando(null)
    }
  }

  async function guardar(tipo: TipoCatalogo, recurso: Recurso, cambios: Partial<Recurso>) {
    const clave = `${tipo}-${recurso.id}`
    setGuardando(clave)
    setError(null)
    setMensajeEstado(null)
    try {
      const actualizado = await apiRequest<Recurso>(`/${tipo}/${recurso.id}`, {
        method: 'PATCH', token, body: JSON.stringify(cambios),
      })
      setColecciones((actual) => ({
        ...actual,
        [tipo]: actual[tipo].map((item) => item.id === actualizado.id ? actualizado : item),
      }))
      setBorradores((actual) => {
        const restantes = { ...actual }
        delete restantes[clave]
        return restantes
      })
      setMensajeEstado(`${catalogos.find((item) => item.tipo === tipo)?.singular} actualizado.`)
    } catch (fallo) {
      setError(mensaje(fallo))
    } finally {
      setGuardando(null)
    }
  }

  return <section aria-labelledby="titulo-catalogos">
    <h2 id="titulo-catalogos">Catálogos</h2>
    {cargando && <p role="status">Cargando catálogos…</p>}
    {error && <div role="alert"><p>{error}</p><button type="button" onClick={() => void cargar()}>Reintentar catálogos</button></div>}
    {mensajeEstado && <p role="status">{mensajeEstado}</p>}
    {!cargando && catalogos.map(({ tipo, nombre, singular }) => <section key={tipo} aria-labelledby={`titulo-${tipo}`}>
      <h3 id={`titulo-${tipo}`}>{nombre}</h3>
      <form onSubmit={(evento) => void crear(evento, tipo)}>
        <label htmlFor={`nuevo-${tipo}`}>{tipo === 'prestaciones' ? 'Nueva' : 'Nuevo'} {singular}</label>
        <input id={`nuevo-${tipo}`} required maxLength={120} value={nombres[tipo]}
          onChange={(evento) => setNombres((actual) => ({ ...actual, [tipo]: evento.target.value }))} />
        {tipo === 'prestaciones' && <>
          <label htmlFor="duracion-prestacion-nueva">Duración en minutos</label>
          <input id="duracion-prestacion-nueva" type="number" min="1" max="2147483647" required
            value={duracionPrestacion} onChange={(evento) => setDuracionPrestacion(evento.target.value)} />
        </>}
        <button type="submit" disabled={guardando === `nuevo-${tipo}`}>Crear {singular}</button>
      </form>
      {colecciones[tipo].length === 0
        ? <p role="status">No hay {nombre.toLowerCase()} registrados.</p>
        : <ul aria-label={nombre}>{colecciones[tipo].map((recurso) => {
          const clave = `${tipo}-${recurso.id}`
          return <li key={recurso.id}>
            <label htmlFor={`nombre-${clave}`}>Nombre {singular} {recurso.nombre}</label>
            <input id={`nombre-${clave}`} maxLength={120}
              value={borradores[clave]?.nombre ?? recurso.nombre}
              onChange={(evento) => setBorradores((actual) => ({
                ...actual, [clave]: { ...actual[clave], nombre: evento.target.value },
              }))} />
            {tipo === 'prestaciones' && <>
              <label htmlFor={`duracion-${clave}`}>Duración prestación {recurso.nombre}</label>
              <input id={`duracion-${clave}`} type="number" min="1" max="2147483647"
                value={borradores[clave]?.duracion_minutos ?? recurso.duracion_minutos}
                onChange={(evento) => setBorradores((actual) => ({
                  ...actual, [clave]: { ...actual[clave], duracion_minutos: Number(evento.target.value) },
                }))} />
            </>}
            <span>{recurso.activo ? 'Activo' : 'Inactivo'}</span>
            <button type="button" disabled={guardando === clave}
              onClick={() => void guardar(tipo, recurso, tipo === 'prestaciones'
                ? {
                  nombre: borradores[clave]?.nombre ?? recurso.nombre,
                  duracion_minutos: borradores[clave]?.duracion_minutos ?? recurso.duracion_minutos,
                }
                : { nombre: borradores[clave]?.nombre ?? recurso.nombre })}>
              Guardar {singular} {recurso.nombre}
            </button>
            {rol === 'administrador' && <button type="button" disabled={guardando === clave}
              onClick={() => void guardar(tipo, recurso, { activo: !recurso.activo })}>
              {recurso.activo ? 'Desactivar' : 'Activar'} {singular} {recurso.nombre}
            </button>}
          </li>
        })}</ul>}
    </section>)}
  </section>
}
