import { useCallback, useEffect, useRef, useState } from 'react'
import { apiRequest, ApiError } from '../api/cliente'

type RolPersonal = 'administrador' | 'recepcion'
type Paciente = { id: string; nombre: string; activo: boolean }
type Movimiento = {
  id: string
  tipo: 'cargo' | 'cobro' | 'reversion'
  monto_ars: string
  concepto?: string
  motivo?: string
  created_at: string
  cargo_id?: string
  cobro_id?: string
}
type Cuenta = { items: Movimiento[]; saldo_ars: string }
type Props = { token: string; rol: RolPersonal }

function crearClave(): string {
  return globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

async function clavePersistida(firma: string): Promise<{ storageKey: string; clave: string }> {
  const cryptoApi = globalThis.crypto
  if (!cryptoApi?.subtle) throw new Error('No se pudo proteger la clave del reintento en este navegador.')
  const digest = await cryptoApi.subtle.digest('SHA-256', new TextEncoder().encode(firma))
  const huella = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('')
  const storageKey = `c19-idempotency:${huella}`
  const existente = localStorage.getItem(storageKey)
  if (existente) return { storageKey, clave: existente }
  const clave = crearClave()
  localStorage.setItem(storageKey, clave)
  return { storageKey, clave }
}

export default function CuentaCorriente({ token, rol }: Props) {
  const [pacientes, setPacientes] = useState<Paciente[]>([])
  const [pacienteId, setPacienteId] = useState('')
  const [cuenta, setCuenta] = useState<Cuenta>({ items: [], saldo_ars: '0.00' })
  const [montoCargo, setMontoCargo] = useState('')
  const [montoCobro, setMontoCobro] = useState('')
  const [montoReversion, setMontoReversion] = useState('')
  const [concepto, setConcepto] = useState('')
  const [motivo, setMotivo] = useState('')
  const [cargoId, setCargoId] = useState('')
  const [cobroId, setCobroId] = useState('')
  const [cargando, setCargando] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')
  const solicitudCuenta = useRef(0)

  const cargarCuenta = useCallback(async (id: string) => {
    if (!id) return false
    const solicitud = ++solicitudCuenta.current
    setCargando(true)
    setError('')
    try {
      const resultado = await apiRequest<Cuenta>(`/finanzas/pacientes/${encodeURIComponent(id)}`, { token })
      if (solicitud !== solicitudCuenta.current) return false
      setCuenta(resultado)
      setCargoId((actual) => actual && resultado.items.some((item) => item.id === actual && item.tipo === 'cargo')
        ? actual : resultado.items.find((item) => item.tipo === 'cargo')?.id ?? '')
      setCobroId((actual) => actual && resultado.items.some((item) => item.id === actual && item.tipo === 'cobro')
        ? actual : resultado.items.find((item) => item.tipo === 'cobro')?.id ?? '')
      return true
    } catch (cause) {
      if (solicitud === solicitudCuenta.current) {
        setError(cause instanceof Error ? cause.message : 'No se pudo consultar la cuenta corriente.')
      }
      return false
    } finally {
      if (solicitud === solicitudCuenta.current) setCargando(false)
    }
  }, [token])

  useEffect(() => {
    let vigente = true
    apiRequest<{ items: Paciente[] }>('/pacientes?limit=100&offset=0', { token })
      .then((resultado) => {
        if (!vigente) return
        const activos = resultado.items.filter((paciente) => paciente.activo)
        setPacientes(activos)
        setPacienteId(activos[0]?.id ?? '')
      })
      .catch((cause: unknown) => {
        if (vigente) setError(cause instanceof Error ? cause.message : 'No se pudieron cargar las fichas.')
      })
    return () => { vigente = false }
  }, [token])

  useEffect(() => { void cargarCuenta(pacienteId) }, [cargarCuenta, pacienteId])

  async function enviar(operacion: string, destino: string, payload: Record<string, string>,
                        ruta: string, limpiar: () => void) {
    if (!pacienteId || cargando || enviando) return
    const cuerpo = JSON.stringify(payload)
    const firmaLocal = `${operacion}:${destino}:${cuerpo}`
    setEnviando(true)
    setError('')
    try {
      const { storageKey, clave } = await clavePersistida(firmaLocal)
      await apiRequest(ruta, {
        token, method: 'POST',
        headers: { 'Idempotency-Key': clave },
        body: cuerpo,
      })
      if (await cargarCuenta(pacienteId)) {
        localStorage.removeItem(storageKey)
        limpiar()
      }
    } catch (cause) {
      const errorApi = cause instanceof ApiError ? cause : null
      setError(errorApi?.message ?? (cause instanceof Error ? cause.message : 'No se pudo registrar el movimiento.'))
    } finally {
      setEnviando(false)
    }
  }

  const cargos = cuenta.items.filter((item) => item.tipo === 'cargo')
  const cobros = cuenta.items.filter((item) => item.tipo === 'cobro')

  return (
    <section aria-labelledby="cuenta-corriente-titulo">
      <h2 id="cuenta-corriente-titulo">Cuenta corriente</h2>
      <p>Movimientos manuales de demostración en ARS. No se conectan medios de pago ni servicios fiscales.</p>
      <label>
        Paciente
        <select aria-label="Paciente" value={pacienteId} disabled={enviando || cargando}
          onChange={(event) => {
            solicitudCuenta.current += 1
            setCuenta({ items: [], saldo_ars: '0.00' })
            setCargoId('')
            setCobroId('')
            setError('')
            setCargando(Boolean(event.target.value))
            setPacienteId(event.target.value)
          }}>
          {pacientes.map((paciente) => <option key={paciente.id} value={paciente.id}>{paciente.nombre}</option>)}
        </select>
      </label>
      {error && <p role="alert">{error}</p>}
      {cargando && <p role="status">Consultando cuenta…</p>}
      <p role="status">Saldo: ARS {cuenta.saldo_ars}</p>

      <div className="formulario-financiero">
        <h3>Registrar cargo manual</h3>
        <label>Importe del cargo ARS<input aria-label="Importe del cargo ARS" inputMode="decimal" value={montoCargo}
          onChange={(event) => setMontoCargo(event.target.value)} /></label>
        <label>Concepto<input aria-label="Concepto" value={concepto}
          onChange={(event) => setConcepto(event.target.value)} /></label>
        <button type="button" disabled={!pacienteId || cargando || enviando}
          onClick={() => void enviar('cargo', pacienteId,
            { monto_ars: montoCargo, concepto },
            `/finanzas/pacientes/${encodeURIComponent(pacienteId)}/cargos`, () => {
              setMontoCargo(''); setConcepto('')
            })}>
          Registrar cargo
        </button>
      </div>

      <div className="formulario-financiero">
        <h3>Registrar cobro</h3>
        <label>Cargo<select aria-label="Cargo" value={cargoId} onChange={(event) => setCargoId(event.target.value)}>
          {cargos.map((cargo) => <option key={cargo.id} value={cargo.id}>{cargo.concepto ?? 'Cargo'} · {cargo.monto_ars}</option>)}
        </select></label>
        <label>Importe del cobro ARS<input aria-label="Importe del cobro ARS" inputMode="decimal" value={montoCobro}
          onChange={(event) => setMontoCobro(event.target.value)} /></label>
        <button type="button" disabled={!cargoId || cargando || enviando}
          onClick={() => void enviar('cobro', cargoId, { monto_ars: montoCobro },
            `/finanzas/cargos/${encodeURIComponent(cargoId)}/cobros`, () => setMontoCobro(''))}>
          Registrar cobro
        </button>
      </div>

      {rol === 'administrador' && <div className="formulario-financiero">
        <h3>Revertir cobro</h3>
        <label>Cobro<select aria-label="Cobro" value={cobroId} onChange={(event) => setCobroId(event.target.value)}>
          {cobros.map((cobro) => <option key={cobro.id} value={cobro.id}>{cobro.monto_ars} · {cobro.id}</option>)}
        </select></label>
        <label>Importe de reversión ARS<input aria-label="Importe de reversión ARS" inputMode="decimal" value={montoReversion}
          onChange={(event) => setMontoReversion(event.target.value)} /></label>
        <label>Motivo<input aria-label="Motivo" value={motivo}
          onChange={(event) => setMotivo(event.target.value)} /></label>
        <button type="button" disabled={!cobroId || cargando || enviando}
          onClick={() => void enviar('reversion', cobroId, { monto_ars: montoReversion, motivo },
            `/finanzas/cobros/${encodeURIComponent(cobroId)}/reversiones`, () => {
              setMontoReversion(''); setMotivo('')
            })}>
          Registrar reversión
        </button>
      </div>}

      <h3>Movimientos</h3>
      {cuenta.items.length === 0 ? <p>No hay movimientos registrados.</p> : <table>
        <thead><tr><th>Fecha</th><th>Tipo</th><th>Detalle</th><th>Importe ARS</th></tr></thead>
        <tbody>{cuenta.items.map((item) => <tr key={item.id}>
          <td>{new Date(item.created_at).toLocaleString('es-AR')}</td>
          <td>{item.tipo}</td><td>{item.concepto ?? item.motivo ?? 'Movimiento manual'}</td>
          <td>{item.monto_ars}</td>
        </tr>)}</tbody>
      </table>}
    </section>
  )
}
