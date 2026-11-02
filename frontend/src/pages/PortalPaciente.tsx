import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { apiRequest, ApiError } from '../api/cliente'

type Turno = {
  turno_id: number
  inicio: string
  fin: string
  estado: string
  version: number
}
type Franja = { inicio: string; fin: string }
type ListaTurnos = { items: Turno[] }
type Disponibilidad = { fecha: string; items: Franja[] }

function hoyMendoza(): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Argentina/Mendoza', year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(new Date())
}

function sumarDia(fecha: string): string {
  const [year, month, day] = fecha.split('-').map(Number)
  return new Date(Date.UTC(year, month - 1, day + 1)).toISOString().slice(0, 10)
}

function nuevaClaveIdempotente(): string {
  return globalThis.crypto?.randomUUID?.() ?? `portal-${Date.now()}-${Math.random().toString(36).slice(2)}`
}

type ClaveOperacion = { identidad: string; valor: string }

function mostrarFecha(valor: string): string {
  return new Intl.DateTimeFormat('es-AR', {
    timeZone: 'America/Argentina/Mendoza', dateStyle: 'medium', timeStyle: 'short',
  }).format(new Date(valor))
}

function mensaje(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'No se pudo completar la operación. Intente nuevamente.'
}

export default function PortalPaciente({ token }: { token: string }) {
  const fechaInicial = useMemo(() => sumarDia(hoyMendoza()), [])
  const [fecha, setFecha] = useState(fechaInicial)
  const [turnos, setTurnos] = useState<Turno[]>([])
  const [franjas, setFranjas] = useState<Franja[]>([])
  const [seleccionada, setSeleccionada] = useState('')
  const [cargando, setCargando] = useState(true)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [estado, setEstado] = useState<string | null>(null)
  const solicitudFranjas = useRef(0)
  const clavesPendientes = useRef(new Map<string, string>())

  function obtenerClaveOperacion(operacion: string, objetivo: string, payload: object): ClaveOperacion {
    const identidad = JSON.stringify([operacion, objetivo, payload])
    let valor = clavesPendientes.current.get(identidad)
    if (!valor) {
      valor = nuevaClaveIdempotente()
      clavesPendientes.current.set(identidad, valor)
    }
    return { identidad, valor }
  }

  const cargarTurnos = useCallback(async () => {
    const resultado = await apiRequest<ListaTurnos>('/mis-turnos', { token })
    setTurnos(resultado.items)
  }, [token])

  const cargarFranjas = useCallback(async (dia: string) => {
    const solicitud = ++solicitudFranjas.current
    setFranjas([])
    setSeleccionada('')
    const resultado = await apiRequest<Disponibilidad>(
      `/portal/disponibilidad?fecha=${encodeURIComponent(dia)}`, { token })
    if (solicitud === solicitudFranjas.current) setFranjas(resultado.items)
  }, [token])

  useEffect(() => {
    let activa = true
    setCargando(true)
    setError(null)
    void Promise.all([cargarTurnos(), cargarFranjas(fecha)])
      .catch((fallo: unknown) => { if (activa) setError(mensaje(fallo)) })
      .finally(() => { if (activa) setCargando(false) })
    return () => { activa = false }
  }, [cargarFranjas, cargarTurnos, fecha])

  async function ejecutar(operacion: () => Promise<Turno>, confirmacion: string,
                          claveOperacion: ClaveOperacion) {
    setGuardando(true)
    setError(null)
    setEstado(null)
    try {
      await operacion()
      await Promise.all([cargarTurnos(), cargarFranjas(fecha)])
      clavesPendientes.current.delete(claveOperacion.identidad)
      setEstado(confirmacion)
    } catch (fallo) {
      setError(mensaje(fallo))
    } finally {
      setGuardando(false)
    }
  }

  function reservar(evento: FormEvent) {
    evento.preventDefault()
    if (!seleccionada) return
    const payload = { inicio: seleccionada }
    const clave = obtenerClaveOperacion('reserva', 'nuevo', payload)
    void ejecutar(() => apiRequest<Turno>('/mis-turnos', {
      method: 'POST', token, headers: { 'Idempotency-Key': clave.valor },
      body: JSON.stringify(payload),
    }), 'Reserva realizada.', clave)
  }

  return (
    <section aria-labelledby="portal-paciente-titulo">
      <h2 id="portal-paciente-titulo">Mis turnos</h2>
      <p>Portal de demostración con datos sintéticos. Los turnos de este ejemplo duran 30 minutos.</p>

      <form onSubmit={reservar}>
        <h3>Reservar un horario</h3>
        <label htmlFor="fecha-portal">Fecha</label>
        <input id="fecha-portal" type="date" value={fecha} min={hoyMendoza()}
          onChange={(evento) => {
            solicitudFranjas.current += 1
            setFranjas([])
            setSeleccionada('')
            setFecha(evento.target.value)
          }} />
        <label htmlFor="franja-portal">Horario disponible</label>
        <select id="franja-portal" value={seleccionada}
          onChange={(evento) => setSeleccionada(evento.target.value)}>
          <option value="">Seleccioná un horario</option>
          {franjas.map((franja) => (
            <option key={franja.inicio} value={franja.inicio}>
              {mostrarFecha(franja.inicio)}
            </option>
          ))}
        </select>
        <button type="submit" disabled={guardando || !seleccionada}>Reservar turno</button>
      </form>

      {cargando && <p role="status">Cargando tus turnos…</p>}
      {error && <p role="alert">{error}</p>}
      {estado && <p role="status">{estado}</p>}
      {!cargando && turnos.length === 0 && <p>No tenés turnos registrados.</p>}
      {turnos.length > 0 && <ul aria-label="Turnos propios">
        {turnos.map((turno) => (
          <li key={turno.turno_id}>
            <p>{mostrarFecha(turno.inicio)} · {turno.estado}</p>
            {['reservado', 'confirmado'].includes(turno.estado) && <>
              <button type="button" disabled={guardando} onClick={() => {
                const payload = {}
                const clave = obtenerClaveOperacion(
                  'cancelacion', String(turno.turno_id), payload)
                void ejecutar(
                  () => apiRequest<Turno>(`/mis-turnos/${turno.turno_id}/cancelacion`, {
                    method: 'POST', token, headers: { 'Idempotency-Key': clave.valor },
                  }), 'Turno cancelado.', clave)
              }}>Cancelar</button>
              <button type="button" disabled={guardando || !seleccionada} onClick={() => {
                const payload = { version: turno.version, inicio: seleccionada }
                const clave = obtenerClaveOperacion(
                  'reprogramacion', String(turno.turno_id), payload)
                void ejecutar(
                  () => apiRequest<Turno>(`/mis-turnos/${turno.turno_id}/reprogramacion`, {
                    method: 'POST', token, headers: { 'Idempotency-Key': clave.valor },
                    body: JSON.stringify(payload),
                  }), 'Turno reprogramado.', clave)
              }}>Reprogramar al horario elegido</button>
            </>}
          </li>
        ))}
      </ul>}
    </section>
  )
}
