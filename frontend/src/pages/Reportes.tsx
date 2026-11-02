import { useState } from 'react'
import { ApiError, apiRequest, EVENTO_SESION_INVALIDA } from '../api/cliente'

type RolPersonal = 'administrador' | 'recepcion'
type TotalesEstado = Record<string, { cantidad: number; minutos: number }>
type RecursoReporte = {
  recurso_id: string
  minutos_disponibles: number
  minutos_ocupados: number
  ocupacion_porcentaje: number | null
}
type DiaAgenda = {
  fecha: string
  estados: TotalesEstado
  recursos: { profesionales: RecursoReporte[]; boxes: RecursoReporte[] }
}
type ReporteAgenda = { desde: string; hasta: string; zona: string; dias: DiaAgenda[] }
type TotalFinanciero = { cantidad: number; importe_ars: string }
type DiaFinanciero = {
  fecha: string
  cargos: TotalFinanciero
  cobros: TotalFinanciero
  reversiones: TotalFinanciero
  neto_ars: string
  saldo_cierre_ars: string
}
type ReporteFinanciero = {
  desde: string
  hasta: string
  saldo_apertura_ars: string
  dias: DiaFinanciero[]
}
type Props = { rol: RolPersonal; token: string }

const ESTADOS = [
  ['reservado', 'Reservados'],
  ['confirmado', 'Confirmados'],
  ['atendido', 'Atendidos'],
  ['ausente', 'Ausentes'],
  ['cancelado', 'Cancelados'],
] as const

function fechaLocalActual(): string {
  const partes = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Argentina/Mendoza', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(new Date())
  const obtener = (tipo: string) => partes.find((parte) => parte.type === tipo)?.value ?? ''
  return `${obtener('year')}-${obtener('month')}-${obtener('day')}`
}

function siguienteFecha(fecha: string): string {
  const [year, month, day] = fecha.split('-').map(Number)
  const siguiente = new Date(Date.UTC(year, month - 1, day + 1))
  return `${siguiente.getUTCFullYear()}-${String(siguiente.getUTCMonth() + 1).padStart(2, '0')}-${String(siguiente.getUTCDate()).padStart(2, '0')}`
}

export default function Reportes({ rol, token }: Props) {
  const hoy = fechaLocalActual()
  const [desde, setDesde] = useState(hoy)
  const [hasta, setHasta] = useState(siguienteFecha(hoy))
  const [agenda, setAgenda] = useState<ReporteAgenda | null>(null)
  const [finanzas, setFinanzas] = useState<ReporteFinanciero | null>(null)
  const [cargando, setCargando] = useState(false)
  const [descargando, setDescargando] = useState('')
  const [error, setError] = useState('')

  async function consultar() {
    const consulta = `desde=${encodeURIComponent(desde)}&hasta=${encodeURIComponent(hasta)}`
    setCargando(true)
    setError('')
    try {
      if (rol === 'administrador') {
        const [resultadoAgenda, resultadoFinanzas] = await Promise.all([
          apiRequest<ReporteAgenda>(`/reportes/agenda?${consulta}`, { token }),
          apiRequest<ReporteFinanciero>(`/reportes/finanzas?${consulta}`, { token }),
        ])
        setAgenda(resultadoAgenda)
        setFinanzas(resultadoFinanzas)
      } else {
        setAgenda(await apiRequest<ReporteAgenda>(`/reportes/agenda?${consulta}`, { token }))
        setFinanzas(null)
      }
    } catch (causa) {
      setError(causa instanceof Error ? causa.message : 'No se pudieron consultar los reportes.')
      setAgenda(null)
      setFinanzas(null)
    } finally {
      setCargando(false)
    }
  }

  async function descargar(tipo: 'agenda' | 'finanzas') {
    setDescargando(tipo)
    setError('')
    const consulta = new URLSearchParams({ desde, hasta }).toString()
    try {
      const ruta = tipo === 'agenda' ? 'agenda' : 'finanzas'
      const respuesta = await fetch(`/api/reportes/${ruta}.csv?${consulta}`, {
        headers: { Authorization: `Bearer ${token}`, Accept: 'text/csv' },
      })
      if (!respuesta.ok) {
        if (respuesta.status === 401) window.dispatchEvent(new Event(EVENTO_SESION_INVALIDA))
        let mensaje = `La API respondió ${respuesta.status}.`
        try {
          const problema = await respuesta.json() as { mensaje?: string }
          if (problema.mensaje) mensaje = problema.mensaje
        } catch {
          // No se publica información interna si la respuesta de error no es JSON.
        }
        throw new ApiError(respuesta.status, 'api_error', null, mensaje)
      }
      const blob = await respuesta.blob()
      const url = URL.createObjectURL(blob)
      const enlace = document.createElement('a')
      enlace.href = url
      enlace.download = `${tipo === 'agenda' ? 'agenda-operativa' : 'finanzas'}-${desde}-${hasta}.csv`
      document.body.append(enlace)
      enlace.click()
      enlace.remove()
      URL.revokeObjectURL(url)
    } catch (causa) {
      setError(causa instanceof Error ? causa.message : 'No se pudo descargar el reporte.')
    } finally {
      setDescargando('')
    }
  }

  return (
    <section aria-labelledby="reportes-titulo">
      <h2 id="reportes-titulo">Reportes operativos</h2>
      <p>Agregados locales por fecha de Mendoza. El rango incluye Desde y excluye Hasta, hasta 31 días.</p>
      <div className="filtros-reportes">
        <label>Desde<input type="date" value={desde} onChange={(evento) => setDesde(evento.target.value)} /></label>
        <label>Hasta (exclusivo)<input type="date" value={hasta} onChange={(evento) => setHasta(evento.target.value)} /></label>
        <button type="button" onClick={() => void consultar()} disabled={cargando || !desde || !hasta}>
          {cargando ? 'Consultando…' : 'Consultar reportes'}
        </button>
      </div>
      {error && <p role="alert">{error}</p>}

      {agenda && <section aria-labelledby="resumen-agenda-titulo">
        <h3 id="resumen-agenda-titulo">Resumen de agenda</h3>
        <p>{agenda.desde} a {agenda.hasta} · {agenda.zona}</p>
        <button type="button" disabled={Boolean(descargando)}
          onClick={() => void descargar('agenda')}>Descargar agenda CSV</button>
        {agenda.dias.map((dia) => <div key={dia.fecha}>
          <h4>{dia.fecha}</h4>
          <table>
            <caption>Turnos por estado</caption>
            <thead><tr><th>Estado</th><th>Cantidad</th><th>Minutos planificados</th></tr></thead>
            <tbody>{ESTADOS.map(([estado, etiqueta]) => <tr key={estado}>
              <th scope="row">{etiqueta}</th>
              <td>{dia.estados[estado]?.cantidad ?? 0}</td>
              <td>{dia.estados[estado]?.minutos ?? 0}</td>
            </tr>)}</tbody>
          </table>
          {([['Profesionales', dia.recursos.profesionales], ['Boxes', dia.recursos.boxes]] as const)
            .map(([titulo, recursos]) => <table key={titulo}>
              <caption>{titulo} · capacidad disponible y ocupación</caption>
              <thead><tr><th>Recurso</th><th>Disponibles</th><th>Ocupados</th><th>Ocupación</th></tr></thead>
              <tbody>{recursos.map((recurso) => <tr key={recurso.recurso_id}>
                <th scope="row">{recurso.recurso_id}</th>
                <td>{recurso.minutos_disponibles}</td>
                <td>{recurso.minutos_ocupados}</td>
                <td>{recurso.ocupacion_porcentaje === null ? 'Sin capacidad' : `${recurso.ocupacion_porcentaje}%`}</td>
              </tr>)}</tbody>
            </table>)}
        </div>)}
      </section>}

      {rol === 'administrador' && finanzas && <section aria-labelledby="resumen-financiero-titulo">
        <h3 id="resumen-financiero-titulo">Resumen financiero</h3>
        <p>Saldo de apertura: ARS {finanzas.saldo_apertura_ars}</p>
        <button type="button" disabled={Boolean(descargando)}
          onClick={() => void descargar('finanzas')}>Descargar finanzas CSV</button>
        <table>
          <caption>Cargos, cobros, reversiones y saldo diario</caption>
          <thead><tr><th>Fecha</th><th>Cargos ARS</th><th>Cobros ARS</th>
            <th>Reversiones ARS</th><th>Neto ARS</th><th>Saldo de cierre ARS</th></tr></thead>
          <tbody>{finanzas.dias.map((dia) => <tr key={dia.fecha}>
            <th scope="row">{dia.fecha}</th><td>{dia.cargos.importe_ars}</td>
            <td>{dia.cobros.importe_ars}</td><td>{dia.reversiones.importe_ars}</td>
            <td>{dia.neto_ars}</td><td>{dia.saldo_cierre_ars}</td>
          </tr>)}</tbody>
        </table>
      </section>}
    </section>
  )
}
