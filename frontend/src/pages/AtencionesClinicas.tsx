import { FormEvent, useCallback, useEffect, useState } from 'react'
import { apiRequest, ApiError } from '../api/cliente'

type Atencion = {
  turno_id: number
  paciente_id: string
  paciente_nombre: string
  inicio: string
  fin: string
}
type Hallazgo = { pieza_fdi: string; superficie_fdi: string; observacion: string | null }
type VersionOdontograma = {
  id: string
  version: number
  created_at: string
  hallazgos: Hallazgo[]
}
type Odontograma = { items: VersionOdontograma[]; version_vigente: number | null }
type Etapa = { orden: number; prestacion_id: string }
type Plan = {
  id: string
  estado: 'propuesto' | 'en_curso' | 'completado' | 'cancelado'
  created_at: string
  etapas: Etapa[]
}
const TAMANO_PAGINA = 25

function mensajeError(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : 'No se pudo completar la consulta clínica. Intente nuevamente.'
}

function fechaHora(valor: string): string {
  return new Intl.DateTimeFormat('es-AR', {
    timeZone: 'America/Argentina/Mendoza', dateStyle: 'short', timeStyle: 'short',
  }).format(new Date(valor))
}

export default function AtencionesClinicas({ token }: { token: string }) {
  const [atenciones, setAtenciones] = useState<Atencion[]>([])
  const [atencionesCargadas, setAtencionesCargadas] = useState(false)
  const [offsetAtenciones, setOffsetAtenciones] = useState(0)
  const [turnoSeleccionado, setTurnoSeleccionado] = useState('')
  const [odontograma, setOdontograma] = useState<Odontograma | null>(null)
  const [planes, setPlanes] = useState<Plan[]>([])
  const [error, setError] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)
  const [pieza, setPieza] = useState('')
  const [superficies, setSuperficies] = useState('')
  const [observacion, setObservacion] = useState('')
  const [prestacionesIds, setPrestacionesIds] = useState('')

  const atencionElegida = atenciones.find((item) => String(item.turno_id) === turnoSeleccionado)

  const recargarClinica = useCallback(async (pacienteId: string) => {
    const [nuevoOdontograma, nuevosPlanes] = await Promise.all([
      apiRequest<Odontograma>(`/pacientes/${encodeURIComponent(pacienteId)}/odontograma`, { token }),
      apiRequest<{ items: Plan[] }>(`/pacientes/${encodeURIComponent(pacienteId)}/planes`, { token }),
    ])
    setOdontograma(nuevoOdontograma)
    setPlanes(nuevosPlanes.items)
  }, [token])

  useEffect(() => {
    let vigente = true
    setAtencionesCargadas(false)
    setTurnoSeleccionado('')
    apiRequest<{ items: Atencion[]; limit: number; offset: number }>(
      `/profesional/atenciones-atendidas?limit=${TAMANO_PAGINA}&offset=${offsetAtenciones}`, { token },
    ).then((resultado) => {
      if (vigente) setAtenciones(resultado.items)
    }).catch((fallo: unknown) => {
      if (vigente) setError(mensajeError(fallo))
    }).finally(() => {
      if (vigente) setAtencionesCargadas(true)
    })
    return () => { vigente = false }
  }, [offsetAtenciones, token])

  useEffect(() => {
    if (!atencionElegida) {
      setOdontograma(null)
      setPlanes([])
      return
    }
    let vigente = true
    setError(null)
    setOcupado(true)
    recargarClinica(atencionElegida.paciente_id).catch((fallo: unknown) => {
      if (vigente) setError(mensajeError(fallo))
    }).finally(() => {
      if (vigente) setOcupado(false)
    })
    return () => { vigente = false }
  }, [atencionElegida, recargarClinica])

  async function registrarOdontograma(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    if (!atencionElegida) return
    setError(null)
    setOcupado(true)
    try {
      await apiRequest(`/pacientes/${encodeURIComponent(atencionElegida.paciente_id)}/odontograma`, {
        method: 'POST', token,
        body: JSON.stringify({ hallazgos: [{
          pieza_fdi: pieza.trim(),
          superficies: superficies.split(',').map((item) => item.trim()).filter(Boolean),
          observacion: observacion.trim() || null,
        }] }),
      })
      setPieza('')
      setSuperficies('')
      setObservacion('')
      await recargarClinica(atencionElegida.paciente_id)
    } catch (fallo) {
      setError(mensajeError(fallo))
    } finally {
      setOcupado(false)
    }
  }

  async function crearPlan(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    if (!atencionElegida) return
    setError(null)
    setOcupado(true)
    try {
      await apiRequest(`/pacientes/${encodeURIComponent(atencionElegida.paciente_id)}/planes`, {
        method: 'POST', token,
        body: JSON.stringify({ prestaciones_ids: prestacionesIds
          .split(',').map((item) => item.trim()).filter(Boolean) }),
      })
      setPrestacionesIds('')
      await recargarClinica(atencionElegida.paciente_id)
    } catch (fallo) {
      setError(mensajeError(fallo))
    } finally {
      setOcupado(false)
    }
  }

  async function cambiarEstado(planId: string, estado: 'en_curso' | 'completado' | 'cancelado') {
    setError(null)
    setOcupado(true)
    try {
      await apiRequest(`/planes/${encodeURIComponent(planId)}/estado`, {
        method: 'PATCH', token, body: JSON.stringify({ estado }),
      })
      if (atencionElegida) await recargarClinica(atencionElegida.paciente_id)
    } catch (fallo) {
      setError(mensajeError(fallo))
    } finally {
      setOcupado(false)
    }
  }

  return <section aria-labelledby="atenciones-clinicas-titulo">
    <h2 id="atenciones-clinicas-titulo">Atenciones clínicas</h2>
    {error && <p role="alert">{error}</p>}
    {!atencionesCargadas && <p role="status">Cargando atenciones atendidas…</p>}
    {atencionesCargadas && atenciones.length === 0 &&
      <p role="status">No hay atenciones atendidas para mostrar.</p>}
    {atenciones.length > 0 && <>
      <label htmlFor="atencion-atendida">Atención atendida</label>
      <select id="atencion-atendida" value={turnoSeleccionado}
        onChange={(evento) => setTurnoSeleccionado(evento.target.value)}>
        <option value="">Seleccione una atención</option>
        {atenciones.map((atencion) => <option key={atencion.turno_id} value={atencion.turno_id}>
          {atencion.paciente_nombre} — {fechaHora(atencion.inicio)}
        </option>)}
      </select>
      <p>Página {Math.floor(offsetAtenciones / TAMANO_PAGINA) + 1}</p>
      <button type="button" disabled={offsetAtenciones === 0 || !atencionesCargadas}
        onClick={() => setOffsetAtenciones((actual) => Math.max(0, actual - TAMANO_PAGINA))}>
        Atenciones anteriores
      </button>
      {atenciones.length === TAMANO_PAGINA && <button type="button"
        disabled={!atencionesCargadas}
        onClick={() => setOffsetAtenciones((actual) => actual + TAMANO_PAGINA)}>
        Atenciones siguientes
      </button>}
    </>}

    {atencionElegida && <>
      <p>Paciente seleccionado: {atencionElegida.paciente_nombre}</p>
      {ocupado && <p role="status">Consultando información clínica…</p>}
      {odontograma && <section aria-labelledby="odontograma-titulo">
        <h3 id="odontograma-titulo">Odontograma</h3>
        <p>Versión vigente: {odontograma.version_vigente ?? 'Sin versiones'}</p>
        {odontograma.items.map((version) => <article key={version.id}>
          <h4>Versión {version.version} — {fechaHora(version.created_at)}</h4>
          {version.hallazgos.length === 0
            ? <p>sin registros de hallazgo</p>
            : <ul>{version.hallazgos.map((hallazgo, indice) => <li key={`${hallazgo.pieza_fdi}-${hallazgo.superficie_fdi}-${indice}`}>
              Pieza {hallazgo.pieza_fdi}, superficie {hallazgo.superficie_fdi}
              {hallazgo.observacion && <p>{hallazgo.observacion}</p>}
            </li>)}</ul>}
        </article>)}
        <form onSubmit={(evento) => void registrarOdontograma(evento)}>
          <h4>Registrar nueva versión</h4>
          <label htmlFor="pieza-fdi">Pieza FDI</label>
          <input id="pieza-fdi" required maxLength={2} value={pieza}
            onChange={(evento) => setPieza(evento.target.value)} />
          <label htmlFor="superficies-fdi">Superficies (separadas por coma)</label>
          <input id="superficies-fdi" required value={superficies}
            onChange={(evento) => setSuperficies(evento.target.value)} />
          <label htmlFor="observacion-odontograma">Observación sintética (opcional)</label>
          <input id="observacion-odontograma" maxLength={500} value={observacion}
            onChange={(evento) => setObservacion(evento.target.value)} />
          <button type="submit" disabled={ocupado}>Registrar nueva versión</button>
        </form>
      </section>}

      {odontograma && <section aria-labelledby="planes-titulo">
        <h3 id="planes-titulo">Planes manuales</h3>
        <form onSubmit={(evento) => void crearPlan(evento)}>
          <label htmlFor="prestaciones-plan">IDs de prestaciones activas (separados por coma)</label>
          <input id="prestaciones-plan" required value={prestacionesIds}
            onChange={(evento) => setPrestacionesIds(evento.target.value)} />
          <button type="submit" disabled={ocupado}>Crear plan</button>
        </form>
        {planes.map((plan) => <article key={plan.id}>
          <h4>Plan {plan.id} — {plan.estado}</h4>
          <ol>{plan.etapas.map((etapa) => <li key={etapa.orden}>
            Prestación {etapa.prestacion_id}
          </li>)}</ol>
          {plan.estado === 'propuesto' && <>
            <button type="button" disabled={ocupado}
              onClick={() => void cambiarEstado(plan.id, 'en_curso')}>Iniciar plan</button>
            <button type="button" disabled={ocupado}
              onClick={() => void cambiarEstado(plan.id, 'cancelado')}>Cancelar plan</button>
          </>}
          {plan.estado === 'en_curso' && <>
            <button type="button" disabled={ocupado}
              onClick={() => void cambiarEstado(plan.id, 'completado')}>Completar plan</button>
            <button type="button" disabled={ocupado}
              onClick={() => void cambiarEstado(plan.id, 'cancelado')}>Cancelar plan</button>
          </>}
        </article>)}
      </section>}
    </>}
  </section>
}
