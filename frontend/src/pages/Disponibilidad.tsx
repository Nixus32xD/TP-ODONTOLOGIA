import { FormEvent, useEffect, useState } from 'react'
import { apiRequest, ApiError } from '../api/cliente'
import { listarTodasLasPaginas } from '../api/paginacion'
import { fechaLocalAISO } from '../agenda/tiempo'

type Recurso = { id: string; nombre: string; activo: boolean }
type Tramo = { inicio: string; fin: string }
type Dias = Record<string, Tramo[]>
type Bloqueo = { id: string; tipo_recurso: string; recurso_id: string; inicio: string; fin: string }
const diasSemana = [
  ['1', 'lunes'], ['2', 'martes'], ['3', 'miércoles'], ['4', 'jueves'],
  ['5', 'viernes'], ['6', 'sábado'], ['7', 'domingo'],
]

function mensaje(error: unknown): string {
  return error instanceof ApiError ? error.message : 'No se pudo completar la operación. Intente nuevamente.'
}

function nombreRecurso(recursos: Recurso[], id: string): string {
  return recursos.find((recurso) => recurso.id === id)?.nombre ?? id
}

function fechaHora(valor: string) {
  const partes = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Argentina/Mendoza', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(new Date(valor))
  const parte = (tipo: string) => partes.find((item) => item.type === tipo)?.value ?? ''
  return `${parte('year')}-${parte('month')}-${parte('day')}T${parte('hour')}:${parte('minute')}`
}

export default function Disponibilidad({ token }: { token: string }) {
  const [profesionales, setProfesionales] = useState<Recurso[]>([])
  const [boxes, setBoxes] = useState<Recurso[]>([])
  const [tipo, setTipo] = useState<'profesional' | 'box'>('profesional')
  const [recursoId, setRecursoId] = useState('')
  const [horarioVigente, setHorarioVigente] = useState<Dias>({})
  const [horarioBorrador, setHorarioBorrador] = useState<Dias>({})
  const [horarioRecursoCargado, setHorarioRecursoCargado] = useState<string | null>(null)
  const [cargando, setCargando] = useState(true)
  const [guardando, setGuardando] = useState(false)
  const [tramosExcepcion, setTramosExcepcion] = useState<Tramo[]>([{ inicio: '', fin: '' }])
  const [diaExcepcionCerrado, setDiaExcepcionCerrado] = useState(false)
  const [fechaExcepcion, setFechaExcepcion] = useState('')
  const [excepcionExiste, setExcepcionExiste] = useState(false)
  const [cargandoExcepcion, setCargandoExcepcion] = useState(false)
  const [guardandoExcepcion, setGuardandoExcepcion] = useState(false)
  const [fechaInicioBloqueo, setFechaInicioBloqueo] = useState('')
  const [fechaFinBloqueo, setFechaFinBloqueo] = useState('')
  const [bloqueos, setBloqueos] = useState<Bloqueo[]>([])
  const [bloqueoEnCurso, setBloqueoEnCurso] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [estado, setEstado] = useState<string | null>(null)

  const recursos = tipo === 'profesional' ? profesionales : boxes

  async function cargarRecursosYBloqueos() {
    setCargando(true)
    setError(null)
    try {
      const [nuevosProfesionales, nuevosBoxes, nuevosBloqueos] = await Promise.all([
        listarTodasLasPaginas<Recurso>('/profesionales', token),
        listarTodasLasPaginas<Recurso>('/boxes', token),
        listarTodasLasPaginas<Bloqueo>('/bloqueos', token),
      ])
      setProfesionales(nuevosProfesionales)
      setBoxes(nuevosBoxes)
      setBloqueos(nuevosBloqueos)
      if (!nuevosProfesionales.length && nuevosBoxes.length) {
        setTipo('box')
        setRecursoId((actual) => actual || nuevosBoxes[0].id)
      } else {
        setRecursoId((actual) => actual || nuevosProfesionales[0]?.id || '')
      }
    } catch (fallo) {
      setError(mensaje(fallo))
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => { void cargarRecursosYBloqueos() }, [token])

  useEffect(() => {
    if (!recursoId || !recursos.some((recurso) => recurso.id === recursoId)) {
      setHorarioVigente({})
      setHorarioBorrador({})
      setHorarioRecursoCargado(null)
      setCargando(false)
      return
    }
    let activa = true
    setCargando(true)
    setError(null)
    setHorarioRecursoCargado(null)
    void apiRequest<{ dias: Dias }>(`/horarios/${tipo}/${recursoId}`, { token })
      .then((respuesta) => {
        if (!activa) return
        setHorarioVigente(respuesta.dias)
        setHorarioBorrador(respuesta.dias)
        setHorarioRecursoCargado(`${tipo}:${recursoId}`)
      })
      .catch((fallo: unknown) => { if (activa) setError(mensaje(fallo)) })
      .finally(() => { if (activa) setCargando(false) })
    return () => { activa = false }
  }, [recursoId, recursos, tipo, token])

  function seleccionarRecurso(siguienteTipo: 'profesional' | 'box', siguienteId: string) {
    setHorarioVigente({})
    setHorarioBorrador({})
    setHorarioRecursoCargado(null)
    setCargando(Boolean(siguienteId))
    setError(null)
    setEstado(null)
    setTipo(siguienteTipo)
    setRecursoId(siguienteId)
  }

  function cambiarTramoHorario(dia: string, indice: number, campo: keyof Tramo, valor: string) {
    setHorarioBorrador((actual) => ({
      ...actual,
      [dia]: (actual[dia] ?? []).map((tramo, posicion) => posicion === indice
        ? { ...tramo, [campo]: valor } : tramo),
    }))
  }

  async function guardarHorario(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setGuardando(true)
    setError(null)
    setEstado(null)
    try {
      const respuesta = await apiRequest<{ dias: Dias }>(`/horarios/${tipo}/${recursoId}`, {
        method: 'PUT', token, body: JSON.stringify({ dias: horarioBorrador }),
      })
      setHorarioVigente(respuesta.dias)
      setHorarioBorrador(respuesta.dias)
      setEstado('Horario semanal guardado.')
    } catch (fallo) {
      setError(mensaje(fallo))
    } finally {
      setGuardando(false)
    }
  }

  async function consultarExcepcion(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    if (!fechaExcepcion) return
    setCargandoExcepcion(true)
    setError(null)
    setEstado(null)
    try {
      const respuesta = await apiRequest<{ tramos: Tramo[] }>(
        `/horarios/${tipo}/${recursoId}/excepciones/${fechaExcepcion}`, { token },
      )
      setTramosExcepcion(respuesta.tramos.length ? respuesta.tramos : [{ inicio: '', fin: '' }])
      setDiaExcepcionCerrado(respuesta.tramos.length === 0)
      setExcepcionExiste(true)
    } catch (fallo) {
      if (fallo instanceof ApiError && fallo.status === 404) {
        setTramosExcepcion([{ inicio: '', fin: '' }])
        setDiaExcepcionCerrado(false)
        setExcepcionExiste(false)
        setEstado('No hay una excepción registrada para esa fecha.')
      } else setError(mensaje(fallo))
    } finally {
      setCargandoExcepcion(false)
    }
  }

  async function guardarExcepcion(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setGuardandoExcepcion(true)
    setError(null)
    setEstado(null)
    try {
      await apiRequest(`/horarios/${tipo}/${recursoId}/excepciones/${fechaExcepcion}`, {
        method: 'PUT', token, body: JSON.stringify({ tramos: diaExcepcionCerrado ? [] : tramosExcepcion }),
      })
      setExcepcionExiste(true)
      setEstado('Excepción guardada.')
    } catch (fallo) {
      setError(mensaje(fallo))
    } finally {
      setGuardandoExcepcion(false)
    }
  }

  async function eliminarExcepcion() {
    setGuardandoExcepcion(true)
    setError(null)
    setEstado(null)
    try {
      await apiRequest(`/horarios/${tipo}/${recursoId}/excepciones/${fechaExcepcion}`, { method: 'DELETE', token })
      setExcepcionExiste(false)
      setTramosExcepcion([{ inicio: '', fin: '' }])
      setDiaExcepcionCerrado(false)
      setEstado('Excepción eliminada.')
    } catch (fallo) {
      setError(mensaje(fallo))
    } finally {
      setGuardandoExcepcion(false)
    }
  }

  async function crearBloqueo(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setBloqueoEnCurso(true)
    setError(null)
    setEstado(null)
    try {
      const [fechaI, horaI] = fechaInicioBloqueo.split('T')
      const [fechaF, horaF] = fechaFinBloqueo.split('T')
      const nuevo = await apiRequest<Bloqueo>('/bloqueos', {
        method: 'POST', token,
        body: JSON.stringify({
          tipo_recurso: tipo, recurso_id: recursoId,
          inicio: fechaLocalAISO(fechaI, horaI), fin: fechaLocalAISO(fechaF, horaF),
        }),
      })
      setBloqueos((actuales) => [...actuales, nuevo])
      setEstado('Bloqueo creado.')
    } catch (fallo) {
      setError(mensaje(fallo))
    } finally {
      setBloqueoEnCurso(false)
    }
  }

  async function eliminarBloqueo(bloqueoId: string) {
    setBloqueoEnCurso(true)
    setError(null)
    setEstado(null)
    try {
      await apiRequest(`/bloqueos/${bloqueoId}`, { method: 'DELETE', token })
      setBloqueos((actuales) => actuales.filter((item) => item.id !== bloqueoId))
      setEstado('Bloqueo eliminado.')
    } catch (fallo) {
      setError(mensaje(fallo))
    } finally {
      setBloqueoEnCurso(false)
    }
  }

  return <section aria-labelledby="titulo-disponibilidad-config">
    <h2 id="titulo-disponibilidad-config">Horarios y bloqueos</h2>
    {cargando && <p role="status">Cargando configuración…</p>}
    {error && <p role="alert">{error}</p>}
    {estado && <p role="status">{estado}</p>}
    <label htmlFor="tipo-recurso-config">Tipo de recurso</label>
    <select id="tipo-recurso-config" value={tipo} onChange={(evento) => {
      const siguiente = evento.target.value as 'profesional' | 'box'
      seleccionarRecurso(siguiente, siguiente === 'profesional' ? profesionales[0]?.id ?? '' : boxes[0]?.id ?? '')
    }}>
      <option value="profesional">Profesional</option><option value="box">Box</option>
    </select>
    <label htmlFor="recurso-config">Recurso</label>
    <select id="recurso-config" value={recursoId} onChange={(evento) => seleccionarRecurso(tipo, evento.target.value)}>
      <option value="">Seleccione</option>
      {recursos.map((recurso) => <option key={recurso.id} value={recurso.id}>
        {recurso.nombre}{recurso.activo ? '' : ' (inactivo)'}
      </option>)}
    </select>

    <form onSubmit={(evento) => void guardarHorario(evento)}>
      <h3>Horario semanal</h3>
      {diasSemana.map(([dia, nombreDia]) => <fieldset key={dia}>
        <legend>{nombreDia}</legend>
        {(horarioBorrador[dia] ?? []).map((tramo, indice) => <div key={`${dia}-${indice}`}>
          <label htmlFor={`inicio-${dia}-${indice}`}>Inicio {nombreDia} {indice + 1}</label>
          <input id={`inicio-${dia}-${indice}`} type="time" required value={tramo.inicio}
            onChange={(evento) => cambiarTramoHorario(dia, indice, 'inicio', evento.target.value)} />
          <label htmlFor={`fin-${dia}-${indice}`}>Fin {nombreDia} {indice + 1}</label>
          <input id={`fin-${dia}-${indice}`} type="time" required value={tramo.fin}
            onChange={(evento) => cambiarTramoHorario(dia, indice, 'fin', evento.target.value)} />
          <button type="button" onClick={() => setHorarioBorrador((actual) => ({
            ...actual, [dia]: actual[dia].filter((_item, posicion) => posicion !== indice),
          }))}>Quitar tramo {nombreDia} {indice + 1}</button>
        </div>)}
        <button type="button" onClick={() => setHorarioBorrador((actual) => ({
          ...actual, [dia]: [...(actual[dia] ?? []), { inicio: '', fin: '' }],
        }))}>Agregar tramo {nombreDia}</button>
      </fieldset>)}
      {diasSemana.some(([dia]) => (horarioVigente[dia] ?? []).length > 0) && <p>
        Horario vigente: {Object.entries(horarioVigente).flatMap(([dia, tramos]) =>
          tramos.map((tramo) => `${diasSemana[Number(dia) - 1][1]} ${tramo.inicio}–${tramo.fin}`),
        ).join(', ')}
      </p>}
      <button type="submit" disabled={cargando || guardando || !recursoId
        || horarioRecursoCargado !== `${tipo}:${recursoId}`}>Guardar horario semanal</button>
    </form>

    <form onSubmit={(evento) => void consultarExcepcion(evento)}>
      <h3>Excepción por fecha</h3>
      <label htmlFor="fecha-excepcion">Fecha de excepción</label>
      <input id="fecha-excepcion" type="date" required value={fechaExcepcion}
        onChange={(evento) => setFechaExcepcion(evento.target.value)} />
      <button type="submit" disabled={cargandoExcepcion || !recursoId}>Consultar excepción</button>
    </form>
    {fechaExcepcion && <form onSubmit={(evento) => void guardarExcepcion(evento)}>
      <h4>{excepcionExiste ? 'Editar excepción' : 'Nueva excepción'}</h4>
      <label htmlFor="excepcion-cerrada">No atender ese día</label>
      <input id="excepcion-cerrada" type="checkbox" checked={diaExcepcionCerrado}
        onChange={(evento) => {
          setDiaExcepcionCerrado(evento.target.checked)
          setTramosExcepcion(evento.target.checked ? [] : (actual) => actual.length ? actual : [{ inicio: '', fin: '' }])
        }} />
      {!diaExcepcionCerrado && tramosExcepcion.map((tramo, indice) => <div key={`ex-${indice}`}>
        <label htmlFor={`inicio-ex-${indice}`}>Inicio excepción {indice + 1}</label>
        <input id={`inicio-ex-${indice}`} type="time" required value={tramo.inicio}
          onChange={(evento) => setTramosExcepcion((actual) => actual.map((item, posicion) =>
            posicion === indice ? { ...item, inicio: evento.target.value } : item))} />
        <label htmlFor={`fin-ex-${indice}`}>Fin excepción {indice + 1}</label>
        <input id={`fin-ex-${indice}`} type="time" required value={tramo.fin}
          onChange={(evento) => setTramosExcepcion((actual) => actual.map((item, posicion) =>
            posicion === indice ? { ...item, fin: evento.target.value } : item))} />
      </div>)}
      {!diaExcepcionCerrado && <button type="button" onClick={() => setTramosExcepcion((actual) => [...actual, { inicio: '', fin: '' }])}>
        Agregar tramo a excepción
      </button>}
      <button type="submit" disabled={guardandoExcepcion}>Guardar excepción</button>
      {excepcionExiste && <button type="button" disabled={guardandoExcepcion} onClick={() => void eliminarExcepcion()}>
        Eliminar excepción
      </button>}
    </form>}

    <section aria-labelledby="titulo-bloqueos">
      <h3 id="titulo-bloqueos">Bloqueos</h3>
      <form onSubmit={(evento) => void crearBloqueo(evento)}>
        <label htmlFor="inicio-bloqueo">Inicio del bloqueo</label>
        <input id="inicio-bloqueo" type="datetime-local" required value={fechaInicioBloqueo}
          onChange={(evento) => setFechaInicioBloqueo(evento.target.value)} />
        <label htmlFor="fin-bloqueo">Fin del bloqueo</label>
        <input id="fin-bloqueo" type="datetime-local" required value={fechaFinBloqueo}
          onChange={(evento) => setFechaFinBloqueo(evento.target.value)} />
        <button type="submit" disabled={bloqueoEnCurso || !recursoId}>Crear bloqueo</button>
      </form>
      {bloqueos.length === 0 ? <p role="status">No hay bloqueos registrados.</p> : <ul aria-label="Bloqueos registrados">
        {bloqueos.map((bloqueo) => <li key={bloqueo.id}>
          Bloqueo {fechaHora(bloqueo.inicio).replace('T', ' ')}–{fechaHora(bloqueo.fin).slice(11)} · {bloqueo.tipo_recurso} {nombreRecurso(bloqueo.tipo_recurso === 'profesional' ? profesionales : boxes, bloqueo.recurso_id)}
          <button type="button" disabled={bloqueoEnCurso} onClick={() => void eliminarBloqueo(bloqueo.id)}>
            Eliminar bloqueo {bloqueo.id}
          </button>
        </li>)}
      </ul>}
    </section>
  </section>
}
