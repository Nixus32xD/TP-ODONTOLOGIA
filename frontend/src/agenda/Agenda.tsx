import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { apiRequest, ApiError } from '../api/cliente'
import { listarTodasLasPaginas } from '../api/paginacion'
import type { Identidad } from '../auth/session'
import { fechaLocalAISO, mostrarFechaHora, rangoAgenda } from './tiempo'

type FilaOperativa = {
  id: number
  paciente_id: string
  paciente_nombre: string
  profesional_id: string
  profesional_nombre: string
  box_id: string
  box_nombre: string
  inicio: string
  fin: string
  estado: string
  version: number
}
type FilaProfesional = { inicio: string; fin: string; paciente_nombre: string }
type PaginaTurnos<T> = { items: T[]; limit: number; offset: number }
type Recurso = { id: string; nombre: string; activo: boolean }
type Paciente = {
  id: string; nombre: string; telefono: string | null; activo: boolean
  acepta_recordatorios: boolean
}
type Disponibilidad = { fecha: string; items: Array<{ inicio: string; fin: string }> }

type Props = { identidad: Identidad; token: string }
type Vista = 'dia' | 'semana'

function hoyEnMendoza(): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Argentina/Mendoza', year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(new Date())
}

function mensaje(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error && [
    'Fecha local inválida.',
    'Hora local inexistente en la zona seleccionada.',
    'Hora local ambigua en la zona seleccionada.',
    'El turno no puede cruzar la medianoche.',
  ].includes(error.message)) return error.message
  return 'No se pudo cargar la agenda. Intente nuevamente.'
}

function fechaHoraInput(valor: string): string {
  const partes = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Argentina/Mendoza', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(new Date(valor))
  const obtener = (tipo: string) => partes.find((parte) => parte.type === tipo)?.value ?? ''
  return `${obtener('year')}-${obtener('month')}-${obtener('day')}T${obtener('hour')}:${obtener('minute')}`
}

function fechaHoraEnMendoza(valor: string): { fecha: string; hora: string } {
  const partes = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Argentina/Mendoza', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(new Date(valor))
  const obtener = (tipo: string) => partes.find((parte) => parte.type === tipo)?.value ?? ''
  return { fecha: `${obtener('year')}-${obtener('month')}-${obtener('day')}`, hora: `${obtener('hour')}:${obtener('minute')}` }
}

function diaSiguiente(fecha: string): string {
  const [year, month, day] = fecha.split('-').map(Number)
  return new Date(Date.UTC(year, month - 1, day + 1)).toISOString().slice(0, 10)
}

export default function Agenda({ identidad, token }: Props) {
  const operativo = identidad.rol !== 'profesional'
  const [fecha, setFecha] = useState(hoyEnMendoza)
  const [vista, setVista] = useState<Vista>('dia')
  const [profesionalFiltro, setProfesionalFiltro] = useState('')
  const [boxFiltro, setBoxFiltro] = useState('')
  const [estadoFiltro, setEstadoFiltro] = useState('')
  const [limite, setLimite] = useState(50)
  const [limiteSeleccionado, setLimiteSeleccionado] = useState(50)
  const [offset, setOffset] = useState(0)
  const [filtrosAplicados, setFiltrosAplicados] = useState({ profesional: '', box: '', estado: '' })
  const [pagina, setPagina] = useState<PaginaTurnos<FilaOperativa | FilaProfesional>>({ items: [], limit: 50, offset: 0 })
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [profesionales, setProfesionales] = useState<Recurso[]>([])
  const [boxes, setBoxes] = useState<Recurso[]>([])
  const [pacientes, setPacientes] = useState<Paciente[]>([])
  const [fechaDisponibilidad, setFechaDisponibilidad] = useState(hoyEnMendoza)
  const [profesionalDisponibilidad, setProfesionalDisponibilidad] = useState('')
  const [boxDisponibilidad, setBoxDisponibilidad] = useState('')
  const [duracion, setDuracion] = useState('30')
  const [opciones, setOpciones] = useState<Disponibilidad['items'] | null>(null)
  const [cargandoDisponibilidad, setCargandoDisponibilidad] = useState(false)
  const [errorDisponibilidad, setErrorDisponibilidad] = useState<string | null>(null)
  const [pacienteSeleccionado, setPacienteSeleccionado] = useState('')
  const [nombrePacienteNuevo, setNombrePacienteNuevo] = useState('')
  const [telefonoPacienteNuevo, setTelefonoPacienteNuevo] = useState('')
  const [aceptaRecordatoriosNuevo, setAceptaRecordatoriosNuevo] = useState(false)
  const [creandoPaciente, setCreandoPaciente] = useState(false)
  const [errorPaciente, setErrorPaciente] = useState<string | null>(null)
  const [pacienteConsentimientoId, setPacienteConsentimientoId] = useState('')
  const [guardandoConsentimiento, setGuardandoConsentimiento] = useState(false)
  const [errorConsentimiento, setErrorConsentimiento] = useState<string | null>(null)
  const [consentimientoActualizado, setConsentimientoActualizado] = useState(false)
  const [horarioSeleccionado, setHorarioSeleccionado] = useState<Disponibilidad['items'][number] | null>(null)
  const [registrando, setRegistrando] = useState(false)
  const [errorAlta, setErrorAlta] = useState<string | null>(null)
  const [altaConfirmada, setAltaConfirmada] = useState(false)
  const [estadoEnCurso, setEstadoEnCurso] = useState<number | null>(null)
  const [errorEstado, setErrorEstado] = useState<string | null>(null)
  const [turnoReprogramar, setTurnoReprogramar] = useState<FilaOperativa | null>(null)
  const [inicioReprogramacion, setInicioReprogramacion] = useState('')
  const [profesionalDestino, setProfesionalDestino] = useState('')
  const [boxDestino, setBoxDestino] = useState('')
  const [guardandoReprogramacion, setGuardandoReprogramacion] = useState(false)
  const [errorReprogramacion, setErrorReprogramacion] = useState<string | null>(null)
  const [reprogramacionConfirmada, setReprogramacionConfirmada] = useState(false)

  const rango = useMemo(() => rangoAgenda(fecha, vista), [fecha, vista])
  const cargarAgenda = useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      const params = new URLSearchParams({ desde: rango.desde, hasta: rango.hasta, limit: String(limite), offset: String(offset) })
      if (operativo && filtrosAplicados.profesional) params.set('profesional_id', filtrosAplicados.profesional)
      if (operativo && filtrosAplicados.box) params.set('box_id', filtrosAplicados.box)
      if (operativo && filtrosAplicados.estado) params.set('estado', filtrosAplicados.estado)
      const resultado = await apiRequest<PaginaTurnos<FilaOperativa | FilaProfesional>>(`/turnos?${params}`, { token })
      setPagina(resultado)
    } catch (fallo) {
      setError(mensaje(fallo))
    } finally {
      setCargando(false)
    }
  }, [filtrosAplicados, limite, offset, operativo, rango.desde, rango.hasta, token])

  useEffect(() => { void cargarAgenda() }, [cargarAgenda])

  useEffect(() => {
    if (!operativo) return
    let activa = true
    void Promise.all([
      listarTodasLasPaginas<Recurso>('/profesionales', token),
      listarTodasLasPaginas<Recurso>('/boxes', token),
      listarTodasLasPaginas<Paciente>('/pacientes', token),
    ]).then(([listaProfesionales, listaBoxes, listaPacientes]) => {
      if (!activa) return
      setProfesionales(listaProfesionales.filter((recurso) => recurso.activo))
      setBoxes(listaBoxes.filter((recurso) => recurso.activo))
      setPacientes(listaPacientes)
      setPacienteConsentimientoId((actual) => actual || listaPacientes[0]?.id || '')
    }).catch((fallo: unknown) => {
      if (activa) setErrorDisponibilidad(mensaje(fallo))
    })
    return () => { activa = false }
  }, [operativo, token])

  function aplicarFiltros(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setOffset(0)
    setLimite(limiteSeleccionado)
    setFiltrosAplicados({ profesional: profesionalFiltro, box: boxFiltro, estado: estadoFiltro })
  }

  async function consultarDisponibilidad(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    if (!profesionalDisponibilidad || !boxDisponibilidad || Number(duracion) <= 0) return
    setCargandoDisponibilidad(true)
    setErrorDisponibilidad(null)
    setOpciones(null)
    setHorarioSeleccionado(null)
    setAltaConfirmada(false)
    try {
      const params = new URLSearchParams({
        fecha: fechaDisponibilidad,
        profesional_id: profesionalDisponibilidad,
        box_id: boxDisponibilidad,
        duracion_minutos: duracion,
      })
      const resultado = await apiRequest<Disponibilidad>(`/disponibilidad?${params}`, { token })
      setOpciones(resultado.items)
    } catch (fallo) {
      setErrorDisponibilidad(mensaje(fallo))
    } finally {
      setCargandoDisponibilidad(false)
    }
  }

  async function registrarTurno(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    if (!pacienteSeleccionado || !profesionalDisponibilidad || !boxDisponibilidad || !horarioSeleccionado) return
    setRegistrando(true)
    setErrorAlta(null)
    setAltaConfirmada(false)
    try {
      await apiRequest('/turnos', {
        method: 'POST',
        token,
        body: JSON.stringify({
          paciente_id: pacienteSeleccionado,
          profesional_id: profesionalDisponibilidad,
          box_id: boxDisponibilidad,
          inicio: horarioSeleccionado.inicio,
          fin: horarioSeleccionado.fin,
        }),
      })
      await cargarAgenda()
      setAltaConfirmada(true)
      setOpciones(null)
      setHorarioSeleccionado(null)
    } catch (fallo) {
      setErrorAlta(mensaje(fallo))
      if (fallo instanceof ApiError && fallo.status === 409) {
        setErrorDisponibilidad('La opción dejó de estar disponible. Consulte nuevamente.')
        await cargarAgenda()
      }
    } finally {
      setRegistrando(false)
    }
  }

  async function crearFichaPaciente(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setCreandoPaciente(true)
    setErrorPaciente(null)
    try {
      const paciente = await apiRequest<Paciente>('/pacientes', {
        method: 'POST', token,
        body: JSON.stringify({
          nombre: nombrePacienteNuevo,
          telefono: telefonoPacienteNuevo || null,
          acepta_recordatorios: aceptaRecordatoriosNuevo,
        }),
      })
      setPacientes((actuales) => [...actuales.filter((actual) => actual.id !== paciente.id), paciente])
      setPacienteSeleccionado(paciente.id)
      setNombrePacienteNuevo('')
      setTelefonoPacienteNuevo('')
      setAceptaRecordatoriosNuevo(false)
    } catch (fallo) {
      setErrorPaciente(mensaje(fallo))
    } finally {
      setCreandoPaciente(false)
    }
  }

  async function cambiarConsentimientoPaciente() {
    const paciente = pacientes.find((actual) => actual.id === pacienteConsentimientoId)
    if (!paciente) return
    setGuardandoConsentimiento(true)
    setErrorConsentimiento(null)
    setConsentimientoActualizado(false)
    try {
      const actualizado = await apiRequest<Paciente>(
        `/pacientes/${encodeURIComponent(paciente.id)}`, {
          method: 'PATCH', token,
          body: JSON.stringify({ acepta_recordatorios: !paciente.acepta_recordatorios }),
        })
      setPacientes((actuales) => actuales.map((actual) =>
        actual.id === actualizado.id ? actualizado : actual))
      setConsentimientoActualizado(true)
    } catch (fallo) {
      setErrorConsentimiento(mensaje(fallo))
    } finally {
      setGuardandoConsentimiento(false)
    }
  }

  async function cambiarEstado(turnoId: number, accion: 'confirmacion' | 'cancelacion' | 'atencion' | 'ausencia') {
    setEstadoEnCurso(turnoId)
    setErrorEstado(null)
    try {
      await apiRequest(`/turnos/${turnoId}/${accion}`, { method: 'POST', token })
      await cargarAgenda()
    } catch (fallo) {
      setErrorEstado(mensaje(fallo))
      if (fallo instanceof ApiError && fallo.status === 409) await cargarAgenda()
    } finally {
      setEstadoEnCurso(null)
    }
  }

  function iniciarReprogramacion(turno: FilaOperativa) {
    setTurnoReprogramar(turno)
    setInicioReprogramacion(fechaHoraInput(turno.inicio))
    setProfesionalDestino(turno.profesional_id)
    setBoxDestino(turno.box_id)
    setErrorReprogramacion(null)
    setReprogramacionConfirmada(false)
  }

  async function guardarReprogramacion(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    if (!turnoReprogramar || !profesionalDestino || !boxDestino) return
    setGuardandoReprogramacion(true)
    setErrorReprogramacion(null)
    setReprogramacionConfirmada(false)
    try {
      const [fecha, hora] = inicioReprogramacion.split('T')
      const inicio = fechaLocalAISO(fecha, hora)
      const duracionMs = Date.parse(turnoReprogramar.fin) - Date.parse(turnoReprogramar.inicio)
      const fin = new Date(Date.parse(inicio) + duracionMs).toISOString()
      const finLocal = fechaHoraEnMendoza(fin)
      if (finLocal.fecha !== fecha && !(finLocal.fecha === diaSiguiente(fecha) && finLocal.hora === '00:00')) {
        throw new Error('El turno no puede cruzar la medianoche.')
      }
      await apiRequest(`/turnos/${turnoReprogramar.id}/reprogramacion`, {
        method: 'POST', token,
        body: JSON.stringify({
          version: turnoReprogramar.version,
          inicio,
          fin,
          profesional_id: profesionalDestino,
          box_id: boxDestino,
        }),
      })
      setTurnoReprogramar(null)
      await cargarAgenda()
      setReprogramacionConfirmada(true)
    } catch (fallo) {
      setErrorReprogramacion(mensaje(fallo))
      if (fallo instanceof ApiError && fallo.status === 409) await cargarAgenda()
    } finally {
      setGuardandoReprogramacion(false)
    }
  }

  return (
    <section aria-labelledby="titulo-agenda">
      <h2 id="titulo-agenda">{operativo ? 'Agenda del consultorio' : 'Mi agenda'}</h2>
      <div className="controles-agenda">
        <label htmlFor="fecha-agenda">Fecha</label>
        <input id="fecha-agenda" type="date" value={fecha} onChange={(evento) => { setOffset(0); setFecha(evento.target.value) }} />
        <button type="button" aria-pressed={vista === 'dia'} onClick={() => { setOffset(0); setVista('dia') }}>Día</button>
        <button type="button" aria-pressed={vista === 'semana'} onClick={() => { setOffset(0); setVista('semana') }}>Semana</button>
      </div>

      {operativo && <form onSubmit={aplicarFiltros}>
        <h3>Filtros</h3>
        <label htmlFor="filtro-profesional">Profesional</label>
        <input id="filtro-profesional" value={profesionalFiltro} onChange={(evento) => setProfesionalFiltro(evento.target.value)} />
        <label htmlFor="filtro-box">Box</label>
        <input id="filtro-box" value={boxFiltro} onChange={(evento) => setBoxFiltro(evento.target.value)} />
        <label htmlFor="filtro-estado">Estado</label>
        <select id="filtro-estado" value={estadoFiltro} onChange={(evento) => setEstadoFiltro(evento.target.value)}>
          <option value="">Todos</option>
          {['reservado', 'confirmado', 'atendido', 'ausente', 'cancelado'].map((estado) => <option key={estado}>{estado}</option>)}
        </select>
        <label htmlFor="limite-pagina">Cantidad por página</label>
        <select id="limite-pagina" value={limiteSeleccionado} onChange={(evento) => setLimiteSeleccionado(Number(evento.target.value))}>
          {[25, 50, 100].map((cantidad) => <option key={cantidad} value={cantidad}>{cantidad}</option>)}
        </select>
        <button type="submit">Aplicar filtros</button>
      </form>}

      {cargando && <p role="status">Cargando agenda…</p>}
      {error && <div role="alert"><p>{error}</p><button type="button" onClick={() => void cargarAgenda()}>Reintentar agenda</button></div>}
      {errorEstado && <p role="alert">{errorEstado}</p>}
      {estadoEnCurso !== null && <p role="status">Actualizando estado del turno…</p>}
      {!cargando && !error && pagina.items.length === 0 && <p role="status">No hay turnos para este período.</p>}
      {!cargando && !error && pagina.items.length > 0 && <ul aria-label="Turnos de la agenda">
        {pagina.items.map((turno, indice) => <li key={'id' in turno ? turno.id : `${turno.inicio}-${indice}`}>
          <p><time dateTime={turno.inicio}>{mostrarFechaHora(turno.inicio)}</time> – <time dateTime={turno.fin}>{mostrarFechaHora(turno.fin)}</time></p>
          <p>Paciente: {turno.paciente_nombre}</p>
          {operativo && 'profesional_nombre' in turno && <>
            <p>{turno.profesional_nombre}</p><p>{turno.box_nombre}</p>
            <p>{turno.estado}</p><p>Versión: {turno.version}</p>
            {turno.estado === 'reservado' && <>
              <button type="button" disabled={estadoEnCurso === turno.id} onClick={() => void cambiarEstado(turno.id, 'confirmacion')}>Confirmar</button>
              <button type="button" disabled={estadoEnCurso === turno.id} onClick={() => void cambiarEstado(turno.id, 'cancelacion')}>Cancelar</button>
            </>}
            {turno.estado === 'confirmado' && <>
              <button type="button" disabled={estadoEnCurso === turno.id} onClick={() => void cambiarEstado(turno.id, 'atencion')}>Marcar atendido</button>
              <button type="button" disabled={estadoEnCurso === turno.id} onClick={() => void cambiarEstado(turno.id, 'ausencia')}>Registrar ausencia</button>
              <button type="button" disabled={estadoEnCurso === turno.id} onClick={() => void cambiarEstado(turno.id, 'cancelacion')}>Cancelar</button>
            </>}
            {(turno.estado === 'reservado' || turno.estado === 'confirmado') && <button
              type="button"
              disabled={guardandoReprogramacion}
              onClick={() => iniciarReprogramacion(turno)}
            >Reprogramar</button>}
          </>}
        </li>)}
      </ul>}
      {turnoReprogramar && <form onSubmit={(evento) => void guardarReprogramacion(evento)}>
        <h3>Reprogramar turno</h3>
        <label htmlFor="nuevo-inicio">Nuevo inicio</label>
        <input
          id="nuevo-inicio"
          type="datetime-local"
          required
          value={inicioReprogramacion}
          onChange={(evento) => setInicioReprogramacion(evento.target.value)}
        />
        <label htmlFor="profesional-destino">Profesional</label>
        <select id="profesional-destino" required value={profesionalDestino}
          onChange={(evento) => setProfesionalDestino(evento.target.value)}>
          <option value="">Seleccione</option>
          {profesionales.map((profesional) => <option key={profesional.id} value={profesional.id}>{profesional.nombre}</option>)}
        </select>
        <label htmlFor="box-destino">Box</label>
        <select id="box-destino" required value={boxDestino}
          onChange={(evento) => setBoxDestino(evento.target.value)}>
          <option value="">Seleccione</option>
          {boxes.map((box) => <option key={box.id} value={box.id}>{box.nombre}</option>)}
        </select>
        {guardandoReprogramacion && <p role="status">Guardando reprogramación…</p>}
        {errorReprogramacion && <p role="alert">{errorReprogramacion}</p>}
        <button type="submit" disabled={guardandoReprogramacion}>Guardar reprogramación</button>
        <button type="button" disabled={guardandoReprogramacion} onClick={() => setTurnoReprogramar(null)}>Cancelar edición</button>
      </form>}
      {reprogramacionConfirmada && <p role="status">Reprogramación confirmada.</p>}
      {operativo && <nav aria-label="Paginación de agenda">
        <button type="button" disabled={offset === 0 || cargando} onClick={() => setOffset(Math.max(0, offset - limite))}>Página anterior</button>
        <span>Página {Math.floor(offset / limite) + 1}</span>
        <button type="button" disabled={pagina.items.length < pagina.limit || cargando} onClick={() => setOffset(offset + limite)}>Página siguiente</button>
      </nav>}

      {operativo && <section aria-labelledby="titulo-consentimiento-recordatorios">
        <h3 id="titulo-consentimiento-recordatorios">Preferencia de recordatorios</h3>
        <p>Gestione la preferencia explícita de la ficha. Los avisos de esta demo son simulados.</p>
        <label htmlFor="paciente-consentimiento">Paciente para consentimiento</label>
        <select id="paciente-consentimiento" value={pacienteConsentimientoId}
          disabled={guardandoConsentimiento}
          onChange={(evento) => {
            setPacienteConsentimientoId(evento.target.value)
            setConsentimientoActualizado(false)
            setErrorConsentimiento(null)
          }}>
          <option value="">Seleccione</option>
          {pacientes.map((paciente) => <option key={paciente.id} value={paciente.id}>
            {paciente.nombre}{paciente.activo ? '' : ' (inactivo)'}
          </option>)}
        </select>
        {pacientes.length === 0 && <p role="status">No hay fichas de pacientes.</p>}
        {pacientes.some((paciente) => paciente.id === pacienteConsentimientoId) && <>
          <p role="status">Consentimiento: {pacientes.find(
            (paciente) => paciente.id === pacienteConsentimientoId)?.acepta_recordatorios
            ? 'habilitado' : 'deshabilitado'}</p>
          <button type="button" disabled={guardandoConsentimiento}
            onClick={() => void cambiarConsentimientoPaciente()}>
            {guardandoConsentimiento ? 'Guardando preferencia…' :
              pacientes.find((paciente) => paciente.id === pacienteConsentimientoId)
                ?.acepta_recordatorios ? 'Deshabilitar recordatorios' : 'Habilitar recordatorios'}
          </button>
        </>}
        {errorConsentimiento && <p role="alert">{errorConsentimiento}</p>}
        {consentimientoActualizado && <p role="status">Preferencia de recordatorios actualizada.</p>}
      </section>}

      {operativo && <section aria-labelledby="titulo-disponibilidad">
        <h3 id="titulo-disponibilidad">Consultar disponibilidad orientativa</h3>
        <form onSubmit={(evento) => void consultarDisponibilidad(evento)}>
          <label htmlFor="fecha-disponibilidad">Fecha de disponibilidad</label>
          <input id="fecha-disponibilidad" type="date" required value={fechaDisponibilidad} onChange={(evento) => setFechaDisponibilidad(evento.target.value)} />
          <label htmlFor="prof-disponibilidad">Profesional para disponibilidad</label>
          <select id="prof-disponibilidad" required value={profesionalDisponibilidad} onChange={(evento) => setProfesionalDisponibilidad(evento.target.value)}>
            <option value="">Seleccione</option>
            {profesionales.map((profesional) => <option key={profesional.id} value={profesional.id}>{profesional.nombre}</option>)}
          </select>
          <label htmlFor="box-disponibilidad">Box para disponibilidad</label>
          <select id="box-disponibilidad" required value={boxDisponibilidad} onChange={(evento) => setBoxDisponibilidad(evento.target.value)}>
            <option value="">Seleccione</option>
            {boxes.map((box) => <option key={box.id} value={box.id}>{box.nombre}</option>)}
          </select>
          <label htmlFor="duracion-disponibilidad">Duración en minutos</label>
          <input id="duracion-disponibilidad" type="number" min="1" required value={duracion} onChange={(evento) => setDuracion(evento.target.value)} />
          <button type="submit" disabled={cargandoDisponibilidad}>Consultar disponibilidad</button>
        </form>
        {cargandoDisponibilidad && <p role="status">Consultando disponibilidad…</p>}
        {errorDisponibilidad && <p role="alert">{errorDisponibilidad}</p>}
        {opciones && (opciones.length === 0 ? <p role="status">No hay opciones disponibles.</p> : <ul aria-label="Opciones disponibles">
          {opciones.map((opcion) => <li key={opcion.inicio}>
            <time dateTime={opcion.inicio}>{mostrarFechaHora(opcion.inicio)}</time> – <time dateTime={opcion.fin}>{mostrarFechaHora(opcion.fin)}</time>
            <button type="button" aria-pressed={horarioSeleccionado?.inicio === opcion.inicio} onClick={() => setHorarioSeleccionado(opcion)}>Elegir horario</button>
          </li>)}
        </ul>)}
        <p>Las opciones son orientativas; el servidor valida nuevamente al crear el turno.</p>
        {opciones && <form onSubmit={(evento) => void registrarTurno(evento)}>
          <h4>Registrar turno</h4>
          <label htmlFor="paciente-turno">Paciente</label>
          <select id="paciente-turno" required value={pacienteSeleccionado} onChange={(evento) => setPacienteSeleccionado(evento.target.value)}>
            <option value="">Seleccione</option>
            {pacientes.filter((paciente) => paciente.activo).map((paciente) => <option key={paciente.id} value={paciente.id}>{paciente.nombre}</option>)}
          </select>
          {horarioSeleccionado && <p role="status">Horario seleccionado: {mostrarFechaHora(horarioSeleccionado.inicio)}</p>}
          <button type="submit" disabled={registrando || !horarioSeleccionado || !pacienteSeleccionado}>
            {registrando ? 'Registrando turno…' : 'Registrar turno'}
          </button>
        </form>}
        {opciones && <form onSubmit={(evento) => void crearFichaPaciente(evento)}>
          <h4>Crear ficha mínima de paciente</h4>
          <label htmlFor="nombre-paciente-nuevo">Nombre de ficha nueva</label>
          <input id="nombre-paciente-nuevo" required maxLength={120} value={nombrePacienteNuevo}
            onChange={(evento) => setNombrePacienteNuevo(evento.target.value)} />
          <label htmlFor="telefono-paciente-nuevo">Teléfono de ficha nueva</label>
          <input id="telefono-paciente-nuevo" value={telefonoPacienteNuevo}
            onChange={(evento) => setTelefonoPacienteNuevo(evento.target.value)} />
          <label htmlFor="consentimiento-paciente-nuevo">
            Acepta recibir recordatorios simulados
          </label>
          <input id="consentimiento-paciente-nuevo" type="checkbox"
            checked={aceptaRecordatoriosNuevo}
            onChange={(evento) => setAceptaRecordatoriosNuevo(evento.target.checked)} />
          <button type="submit" disabled={creandoPaciente}>
            {creandoPaciente ? 'Creando ficha…' : 'Crear ficha de paciente'}
          </button>
          {errorPaciente && <p role="alert">{errorPaciente}</p>}
        </form>}
        {errorAlta && <p role="alert">{errorAlta}</p>}
        {altaConfirmada && <p role="status">Turno reservado.</p>}
      </section>}
    </section>
  )
}
