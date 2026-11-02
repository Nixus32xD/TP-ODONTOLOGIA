import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest, ApiError } from '../api/cliente'
import Agenda from './Agenda'
import { rangoAgenda } from './tiempo'

vi.mock('../api/cliente', async (importOriginal) => {
  const original = await importOriginal<typeof import('../api/cliente')>()
  return { ...original, apiRequest: vi.fn() }
})

const identidadBase = {
  usuario_id: 'usuario-demo', identificador: 'demo', profesional_id: null,
  expira_en: 1_800_000_000,
}
const turnoOperativo = {
  id: 'turno-1', paciente_id: 'paciente-1', paciente_nombre: 'Ana Pérez',
  profesional_id: 'prof-1', profesional_nombre: 'Dra. Luna', box_id: 'box-1',
  box_nombre: 'Box 1', inicio: '2026-11-02T09:00:00-03:00',
  fin: '2026-11-02T09:30:00-03:00', estado: 'reservado', version: 2,
}

function fechaActualEnMendoza() {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Argentina/Mendoza', year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(new Date())
}
const listaProfesionales = { items: [{ id: 'prof-1', nombre: 'Dra. Luna', activo: true }] }
const listaBoxes = { items: [{ id: 'box-1', nombre: 'Box 1', activo: true }] }
const listaPacientes = { items: [{ id: 'paciente-1', nombre: 'Paciente ejemplo', telefono: null, activo: true }] }

describe('consulta de agenda', () => {
  const api = vi.mocked(apiRequest)
  beforeEach(() => {
    api.mockReset()
  })

  it('consulta y muestra la agenda diaria operativa con rango local offset-aware', async () => {
    api.mockResolvedValueOnce({ items: [turnoOperativo], limit: 50, offset: 0 })
      .mockResolvedValueOnce(listaProfesionales).mockResolvedValueOnce(listaBoxes).mockResolvedValueOnce(listaPacientes)
    render(<Agenda identidad={{ ...identidadBase, rol: 'recepcion' }} token="token-recepcion" />)

    expect(await screen.findByText('Paciente: Ana Pérez')).toBeInTheDocument()
    expect(screen.getAllByText('Dra. Luna')).toHaveLength(2)
    expect(screen.getAllByText('Box 1')).toHaveLength(2)
    expect(screen.getAllByText('reservado')).toHaveLength(2)
    expect(api).toHaveBeenCalledWith(expect.stringMatching(/^\/turnos\?/), expect.objectContaining({ token: 'token-recepcion' }))
    const ruta = String(api.mock.calls[0][0])
    const rango = rangoAgenda(fechaActualEnMendoza(), 'dia')
    expect(ruta).toContain(`desde=${encodeURIComponent(rango.desde)}`)
    expect(ruta).toContain(`hasta=${encodeURIComponent(rango.hasta)}`)
  })

  it('excluye recursos y pacientes inactivos de las selecciones para altas', async () => {
    api.mockImplementation(async (rutaBase) => {
      const ruta = String(rutaBase)
      if (ruta.startsWith('/turnos?')) return { items: [], limit: 50, offset: 0 } as never
      if (ruta.startsWith('/profesionales?')) return { items: [
        { id: 'prof-activo', nombre: 'Dra. Activa', activo: true },
        { id: 'prof-inactivo', nombre: 'Dra. Inactiva', activo: false },
      ] } as never
      if (ruta.startsWith('/boxes?')) return { items: [
        { id: 'box-activo', nombre: 'Box activo', activo: true },
        { id: 'box-inactivo', nombre: 'Box inactivo', activo: false },
      ] } as never
      if (ruta.startsWith('/pacientes?')) return { items: [
        { id: 'paciente-activo', nombre: 'Paciente activo', telefono: null, activo: true },
        { id: 'paciente-inactivo', nombre: 'Paciente inactivo', telefono: null, activo: false },
      ] } as never
      if (ruta.startsWith('/disponibilidad?')) return { items: [] } as never
      return undefined as never
    })
    render(<Agenda identidad={{ ...identidadBase, rol: 'recepcion' }} token="token-recepcion" />)

    expect(await screen.findByRole('option', { name: 'Dra. Activa' })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: 'Dra. Inactiva' })).not.toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Box activo' })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: 'Box inactivo' })).not.toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Profesional para disponibilidad'), { target: { value: 'prof-activo' } })
    fireEvent.change(screen.getByLabelText('Box para disponibilidad'), { target: { value: 'box-activo' } })
    fireEvent.click(screen.getByRole('button', { name: 'Consultar disponibilidad' }))
    expect(await screen.findByRole('option', { name: 'Paciente activo' })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: 'Paciente inactivo' })).not.toBeInTheDocument()
  })

  it('consulta una semana de lunes a lunes', async () => {
    api.mockResolvedValueOnce({ items: [], limit: 50, offset: 0 })
      .mockResolvedValueOnce(listaProfesionales).mockResolvedValueOnce(listaBoxes).mockResolvedValueOnce(listaPacientes)
      .mockResolvedValue({ items: [], limit: 50, offset: 0 })
    render(<Agenda identidad={{ ...identidadBase, rol: 'administrador' }} token="token-admin" />)
    await screen.findByRole('option', { name: 'Dra. Luna' })
    await screen.findByRole('option', { name: 'Box 1' })
    await screen.findByText('No hay turnos para este período.')
    fireEvent.click(screen.getByRole('button', { name: 'Semana' }))

    await waitFor(() => expect(api).toHaveBeenCalledTimes(5))
    const ruta = String(api.mock.calls[4][0])
    const rango = rangoAgenda(fechaActualEnMendoza(), 'semana')
    expect(ruta).toContain(`desde=${encodeURIComponent(rango.desde)}`)
    expect(ruta).toContain(`hasta=${encodeURIComponent(rango.hasta)}`)
  })

  it('envía filtros y respeta la paginación informada por la API', async () => {
    api.mockResolvedValueOnce({ items: [], limit: 50, offset: 0 })
      .mockResolvedValueOnce(listaProfesionales).mockResolvedValueOnce(listaBoxes).mockResolvedValueOnce(listaPacientes)
      .mockResolvedValueOnce({ items: Array.from({ length: 25 }, (_, i) => ({ ...turnoOperativo, id: `turno-filtro-${i}` })), limit: 25, offset: 0 })
      .mockResolvedValueOnce({ items: Array.from({ length: 25 }, (_, i) => ({ ...turnoOperativo, id: `turno-pagina-${i}` })), limit: 25, offset: 25 })
    render(<Agenda identidad={{ ...identidadBase, rol: 'administrador' }} token="token-admin" />)
    await screen.findByText('No hay turnos para este período.')
    fireEvent.change(screen.getByLabelText('Profesional'), { target: { value: 'prof-1' } })
    fireEvent.change(screen.getByLabelText('Box'), { target: { value: 'box-1' } })
    fireEvent.change(screen.getByLabelText('Estado'), { target: { value: 'reservado' } })
    fireEvent.change(screen.getByLabelText('Cantidad por página'), { target: { value: '25' } })
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))
    await waitFor(() => expect(api).toHaveBeenCalledTimes(5))
    const filtrada = String(api.mock.calls[4][0])
    expect(filtrada).toContain('profesional_id=prof-1')
    expect(filtrada).toContain('box_id=box-1')
    expect(filtrada).toContain('estado=reservado')
    expect(filtrada).toContain('limit=25')
    expect(filtrada).toContain('offset=0')

    fireEvent.click(screen.getByRole('button', { name: 'Página siguiente' }))
    await waitFor(() => expect(api).toHaveBeenCalledTimes(6))
    expect(String(api.mock.calls[5][0])).toContain('offset=25')
  })

  it('Professional ve sólo sus campos reducidos y no envía filtro de profesional', async () => {
    api.mockResolvedValue({ items: [{ inicio: turnoOperativo.inicio, fin: turnoOperativo.fin, paciente_nombre: 'Ana Pérez' }], limit: 50, offset: 0 })
    render(<Agenda identidad={{ ...identidadBase, rol: 'profesional', profesional_id: 'prof-vinculado' }} token="token-prof" />)

    expect(await screen.findByText('Paciente: Ana Pérez')).toBeInTheDocument()
    expect(screen.queryByText('Dra. Luna')).not.toBeInTheDocument()
    expect(screen.queryByText('Box 1')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Profesional')).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Consultar disponibilidad orientativa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /crear|confirmar|cancelar|atendido|ausencia|reprogramar/i })).not.toBeInTheDocument()
    expect(String(api.mock.calls[0][0])).not.toContain('profesional_id=')
    expect(api.mock.calls.some(([ruta]) => ruta === '/boxes?limit=100&offset=0')).toBe(false)
  })

  it('Recepción consulta disponibilidad orientativa con los recursos seleccionados', async () => {
    api.mockResolvedValueOnce({ items: [], limit: 50, offset: 0 })
      .mockResolvedValueOnce(listaProfesionales).mockResolvedValueOnce(listaBoxes).mockResolvedValueOnce(listaPacientes)
      .mockResolvedValueOnce({ fecha: '2026-11-02', items: [{ inicio: turnoOperativo.inicio, fin: turnoOperativo.fin }] })
    render(<Agenda identidad={{ ...identidadBase, rol: 'recepcion' }} token="token-recepcion" />)
    await screen.findByRole('option', { name: 'Dra. Luna' })
    await screen.findByRole('option', { name: 'Box 1' })
    fireEvent.change(screen.getByLabelText('Profesional para disponibilidad'), { target: { value: 'prof-1' } })
    fireEvent.change(screen.getByLabelText('Box para disponibilidad'), { target: { value: 'box-1' } })
    fireEvent.change(screen.getByLabelText('Duración en minutos'), { target: { value: '30' } })
    fireEvent.click(screen.getByRole('button', { name: 'Consultar disponibilidad' }))

    expect(await screen.findByText(/9:00/)).toBeInTheDocument()
    const consulta = api.mock.calls[4]
    expect(String(consulta[0])).toContain('/disponibilidad?')
    expect(String(consulta[0])).toContain('profesional_id=prof-1')
    expect(String(consulta[0])).toContain('box_id=box-1')
    expect(String(consulta[0])).toContain('duracion_minutos=30')
    expect(consulta[1]).toEqual(expect.objectContaining({ token: 'token-recepcion' }))
  })

  it('crea el turno sólo tras confirmación, con duración explícita y sin prestación asociada', async () => {
    let confirmarAlta: (() => void) | undefined
    api.mockImplementation(async (ruta, opciones = {}) => {
      if (ruta.startsWith('/turnos?')) return { items: [], limit: 50, offset: 0 } as never
      if (ruta.startsWith('/profesionales?')) return listaProfesionales as never
      if (ruta.startsWith('/boxes?')) return listaBoxes as never
      if (ruta.startsWith('/pacientes?')) return {
        items: [{ id: 'paciente-1', nombre: 'Paciente ejemplo', telefono: null, activo: true }],
        limit: 50, offset: 0,
      } as never
      if (ruta.startsWith('/disponibilidad?')) return {
        fecha: fechaActualEnMendoza(), items: [{ inicio: turnoOperativo.inicio, fin: turnoOperativo.fin }],
      } as never
      if (ruta === '/turnos' && opciones.method === 'POST') {
        return new Promise((resolve) => {
          confirmarAlta = () => resolve({
            id: 17, paciente_id: 'paciente-1', profesional_id: 'prof-1', box_id: 'box-1',
            inicio: turnoOperativo.inicio, fin: turnoOperativo.fin, estado: 'reservado',
          })
        }) as never
      }
      return undefined as never
    })
    render(<Agenda identidad={{ ...identidadBase, rol: 'recepcion' }} token="token-recepcion" />)
    await screen.findByRole('option', { name: 'Dra. Luna' })
    await screen.findByRole('option', { name: 'Box 1' })
    fireEvent.change(screen.getByLabelText('Profesional para disponibilidad'), { target: { value: 'prof-1' } })
    fireEvent.change(screen.getByLabelText('Box para disponibilidad'), { target: { value: 'box-1' } })
    fireEvent.change(screen.getByLabelText('Duración en minutos'), { target: { value: '30' } })
    fireEvent.click(screen.getByRole('button', { name: 'Consultar disponibilidad' }))
    await screen.findByRole('option', { name: 'Paciente ejemplo' })
    fireEvent.change(screen.getByLabelText('Paciente'), { target: { value: 'paciente-1' } })
    fireEvent.click(await screen.findByRole('button', { name: /Elegir horario/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Registrar turno' }))

    expect(await screen.findByText('Registrando turno…')).toBeInTheDocument()
    expect(screen.queryByText('Turno reservado.')).not.toBeInTheDocument()
    const solicitud = api.mock.calls.find(([ruta, opciones]) => ruta === '/turnos' && opciones?.method === 'POST')
    expect(JSON.parse(String(solicitud?.[1]?.body))).toEqual({
      paciente_id: 'paciente-1', profesional_id: 'prof-1', box_id: 'box-1',
      inicio: turnoOperativo.inicio, fin: turnoOperativo.fin,
    })

    confirmarAlta?.()
    expect(await screen.findByText('Turno reservado.')).toBeInTheDocument()
  })

  it('un conflicto de alta no muestra éxito y vuelve a consultar la agenda', async () => {
    let consultas = 0
    api.mockImplementation(async (ruta) => {
      if (ruta.startsWith('/turnos?')) {
        consultas += 1
        return { items: [], limit: 50, offset: 0 } as never
      }
      if (ruta.startsWith('/profesionales?')) return listaProfesionales as never
      if (ruta.startsWith('/boxes?')) return listaBoxes as never
      if (ruta.startsWith('/pacientes?')) return listaPacientes as never
      if (ruta.startsWith('/disponibilidad?')) return {
        fecha: fechaActualEnMendoza(), items: [{ inicio: turnoOperativo.inicio, fin: turnoOperativo.fin }],
      } as never
      if (ruta === '/turnos') throw new ApiError(409, 'conflicto_box', 'box_id', 'El intervalo ya no está disponible.')
      return undefined as never
    })
    render(<Agenda identidad={{ ...identidadBase, rol: 'recepcion' }} token="token-recepcion" />)
    await screen.findByRole('option', { name: 'Dra. Luna' })
    await screen.findByRole('option', { name: 'Box 1' })
    fireEvent.change(screen.getByLabelText('Profesional para disponibilidad'), { target: { value: 'prof-1' } })
    fireEvent.change(screen.getByLabelText('Box para disponibilidad'), { target: { value: 'box-1' } })
    fireEvent.click(screen.getByRole('button', { name: 'Consultar disponibilidad' }))
    await screen.findByRole('option', { name: 'Paciente ejemplo' })
    fireEvent.change(screen.getByLabelText('Paciente'), { target: { value: 'paciente-1' } })
    fireEvent.click(await screen.findByRole('button', { name: /Elegir horario/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Registrar turno' }))

    expect(await screen.findByText('El intervalo ya no está disponible.')).toBeInTheDocument()
    expect(screen.queryByText('Turno reservado.')).not.toBeInTheDocument()
    await waitFor(() => expect(consultas).toBe(2))
  })

  it('crea una ficha mínima, la selecciona por el ID devuelto y no envía datos clínicos', async () => {
    const nueva = { id: 'paciente-nuevo', nombre: 'Eva Ejemplo', telefono: '+54 261 555-0101', activo: true }
    api.mockImplementation(async (ruta, opciones = {}) => {
      if (ruta.startsWith('/turnos?')) return { items: [], limit: 50, offset: 0 } as never
      if (ruta.startsWith('/profesionales?')) return listaProfesionales as never
      if (ruta.startsWith('/boxes?')) return listaBoxes as never
      if (ruta.startsWith('/pacientes?')) return listaPacientes as never
      if (ruta === '/pacientes' && opciones.method === 'POST') return nueva as never
      if (ruta.startsWith('/disponibilidad?')) return {
        fecha: fechaActualEnMendoza(), items: [{ inicio: turnoOperativo.inicio, fin: turnoOperativo.fin }],
      } as never
      return undefined as never
    })
    render(<Agenda identidad={{ ...identidadBase, rol: 'recepcion' }} token="token-recepcion" />)
    await screen.findByRole('option', { name: 'Dra. Luna' })
    await screen.findByRole('option', { name: 'Box 1' })
    fireEvent.change(screen.getByLabelText('Profesional para disponibilidad'), { target: { value: 'prof-1' } })
    fireEvent.change(screen.getByLabelText('Box para disponibilidad'), { target: { value: 'box-1' } })
    fireEvent.click(screen.getByRole('button', { name: 'Consultar disponibilidad' }))
    await screen.findByRole('option', { name: 'Paciente ejemplo' })
    fireEvent.change(screen.getByLabelText('Nombre de ficha nueva'), { target: { value: 'Eva Ejemplo' } })
    fireEvent.change(screen.getByLabelText('Teléfono de ficha nueva'), { target: { value: '+54 261 555-0101' } })
    fireEvent.click(screen.getByRole('button', { name: 'Crear ficha de paciente' }))

    expect(await screen.findByRole('option', { name: 'Eva Ejemplo' })).toBeInTheDocument()
    expect(screen.getByLabelText('Paciente')).toHaveValue('paciente-nuevo')
    const solicitud = api.mock.calls.find(([ruta, opciones]) => ruta === '/pacientes' && opciones?.method === 'POST')
    expect(JSON.parse(String(solicitud?.[1]?.body))).toEqual({ nombre: 'Eva Ejemplo', telefono: '+54 261 555-0101' })
  })

  it('Recepción confirma un turno vigente por el endpoint de estado y recarga el resultado', async () => {
    let estado = 'reservado'
    api.mockImplementation(async (ruta, opciones = {}) => {
      if (ruta.startsWith('/turnos?')) return {
        items: [{ ...turnoOperativo, id: 17, estado }], limit: 50, offset: 0,
      } as never
      if (ruta.startsWith('/profesionales?')) return listaProfesionales as never
      if (ruta.startsWith('/boxes?')) return listaBoxes as never
      if (ruta.startsWith('/pacientes?')) return listaPacientes as never
      if (ruta === '/turnos/17/confirmacion' && opciones.method === 'POST') {
        estado = 'confirmado'
        return { id: 17, estado } as never
      }
      return undefined as never
    })
    render(<Agenda identidad={{ ...identidadBase, rol: 'recepcion' }} token="token-recepcion" />)

    fireEvent.click(await screen.findByRole('button', { name: 'Confirmar' }))
    expect(await screen.findByText('confirmado')).toBeInTheDocument()
    expect(api).toHaveBeenCalledWith('/turnos/17/confirmacion', expect.objectContaining({ method: 'POST', token: 'token-recepcion' }))
  })

  it('anuncia una transición pendiente y no cambia el estado antes de la respuesta', async () => {
    let estado = 'reservado'
    let confirmar: (() => void) | undefined
    api.mockImplementation(async (ruta, opciones = {}) => {
      if (ruta.startsWith('/turnos?')) return {
        items: [{ ...turnoOperativo, id: 17, estado }], limit: 50, offset: 0,
      } as never
      if (ruta.startsWith('/profesionales?')) return listaProfesionales as never
      if (ruta.startsWith('/boxes?')) return listaBoxes as never
      if (ruta.startsWith('/pacientes?')) return listaPacientes as never
      if (ruta === '/turnos/17/confirmacion' && opciones.method === 'POST') {
        return new Promise((resolve) => { confirmar = () => { estado = 'confirmado'; resolve({ id: 17, estado }) } }) as never
      }
      return undefined as never
    })
    render(<Agenda identidad={{ ...identidadBase, rol: 'recepcion' }} token="token-recepcion" />)

    fireEvent.click(await screen.findByRole('button', { name: 'Confirmar' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Actualizando estado del turno…')
    expect(screen.getByRole('button', { name: 'Confirmar' })).toBeDisabled()
    expect(screen.getByRole('list', { name: 'Turnos de la agenda' })).toHaveTextContent('reservado')

    confirmar?.()
    expect(await screen.findByText('confirmado')).toBeInTheDocument()
  })

  it.each([
    ['reservado', 'cancelado', 'cancelacion', 'Cancelar'],
    ['confirmado', 'atendido', 'atencion', 'Marcar atendido'],
    ['confirmado', 'ausente', 'ausencia', 'Registrar ausencia'],
    ['confirmado', 'cancelado', 'cancelacion', 'Cancelar'],
  ] as const)('aplica transición %s -> %s desde la API', async (estadoInicial, destino, endpoint, accion) => {
    let estado: string = estadoInicial
    api.mockImplementation(async (ruta, opciones = {}) => {
      if (ruta.startsWith('/turnos?')) return {
        items: [{ ...turnoOperativo, id: 17, estado }], limit: 50, offset: 0,
      } as never
      if (ruta.startsWith('/profesionales?')) return listaProfesionales as never
      if (ruta.startsWith('/boxes?')) return listaBoxes as never
      if (ruta.startsWith('/pacientes?')) return listaPacientes as never
      if (ruta === `/turnos/17/${endpoint}` && opciones.method === 'POST') {
        estado = destino
        return { id: 17, estado } as never
      }
      return undefined as never
    })
    render(<Agenda identidad={{ ...identidadBase, rol: 'administrador' }} token="token-admin" />)

    fireEvent.click(await screen.findByRole('button', { name: accion }))
    await waitFor(() => expect(screen.getByRole('list', { name: 'Turnos de la agenda' })).toHaveTextContent(destino))
    expect(api).toHaveBeenCalledWith(`/turnos/17/${endpoint}`, expect.objectContaining({ method: 'POST', token: 'token-admin' }))
  })

  it('un conflicto de transición conserva la respuesta del servidor y recarga la agenda', async () => {
    let consultas = 0
    api.mockImplementation(async (ruta) => {
      if (ruta.startsWith('/turnos?')) {
        consultas += 1
        return { items: [{ ...turnoOperativo, id: 17 }], limit: 50, offset: 0 } as never
      }
      if (ruta.startsWith('/profesionales?')) return listaProfesionales as never
      if (ruta.startsWith('/boxes?')) return listaBoxes as never
      if (ruta.startsWith('/pacientes?')) return listaPacientes as never
      if (ruta === '/turnos/17/confirmacion') throw new ApiError(409, 'transicion_invalida', null, 'La transición ya no está permitida.')
      return undefined as never
    })
    render(<Agenda identidad={{ ...identidadBase, rol: 'recepcion' }} token="token-recepcion" />)

    fireEvent.click(await screen.findByRole('button', { name: 'Confirmar' }))
    expect(await screen.findByText('La transición ya no está permitida.')).toBeInTheDocument()
    expect(screen.getByRole('list', { name: 'Turnos de la agenda' })).toHaveTextContent('reservado')
    expect(screen.getByRole('button', { name: 'Confirmar' })).toBeInTheDocument()
    await waitFor(() => expect(consultas).toBe(2))
  })

  it('reprograma un turno vigente con versión y recursos actuales sin cambiar paciente ni duración', async () => {
    api.mockImplementation(async (ruta, opciones = {}) => {
      if (ruta.startsWith('/turnos?')) return {
        items: [{ ...turnoOperativo, id: 17, version: 2 }], limit: 50, offset: 0,
      } as never
      if (ruta.startsWith('/profesionales?')) return listaProfesionales as never
      if (ruta.startsWith('/boxes?')) return listaBoxes as never
      if (ruta.startsWith('/pacientes?')) return listaPacientes as never
      if (ruta === '/turnos/17/reprogramacion' && opciones.method === 'POST') return {
        id: 17, paciente_id: 'paciente-1', profesional_id: 'prof-1', box_id: 'box-1',
        inicio: '2026-11-03T13:00:00Z', fin: '2026-11-03T13:30:00Z', estado: 'reservado', version: 3,
      } as never
      return undefined as never
    })
    render(<Agenda identidad={{ ...identidadBase, rol: 'recepcion' }} token="token-recepcion" />)

    fireEvent.click(await screen.findByRole('button', { name: 'Reprogramar' }))
    fireEvent.change(screen.getByLabelText('Nuevo inicio'), { target: { value: '2026-11-03T10:00' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar reprogramación' }))

    await waitFor(() => expect(api).toHaveBeenCalledWith('/turnos/17/reprogramacion', expect.objectContaining({ method: 'POST' })))
    const solicitud = api.mock.calls.find(([ruta]) => ruta === '/turnos/17/reprogramacion')
    expect(JSON.parse(String(solicitud?.[1]?.body))).toEqual({
      version: 2,
      inicio: '2026-11-03T10:00:00-03:00',
      fin: '2026-11-03T13:30:00.000Z',
      profesional_id: 'prof-1', box_id: 'box-1',
    })
  })

  it.each([
    ['hora local inexistente', '2007-12-30T00:30', 'Hora local inexistente en la zona seleccionada.'],
    ['cruce de medianoche', '2026-11-03T23:45', 'El turno no puede cruzar la medianoche.'],
  ])('explica el error de %s al reprogramar', async (_caso, nuevoInicio, mensajeEsperado) => {
    api.mockImplementation(async (ruta) => {
      if (ruta.startsWith('/turnos?')) return {
        items: [{ ...turnoOperativo, id: 17, version: 2 }], limit: 50, offset: 0,
      } as never
      if (ruta.startsWith('/profesionales?')) return listaProfesionales as never
      if (ruta.startsWith('/boxes?')) return listaBoxes as never
      if (ruta.startsWith('/pacientes?')) return listaPacientes as never
      return undefined as never
    })
    render(<Agenda identidad={{ ...identidadBase, rol: 'recepcion' }} token="token-recepcion" />)

    fireEvent.click(await screen.findByRole('button', { name: 'Reprogramar' }))
    fireEvent.change(screen.getByLabelText('Nuevo inicio'), { target: { value: nuevoInicio } })
    expect(screen.getByLabelText('Nuevo inicio')).toHaveValue(nuevoInicio)
    fireEvent.submit(screen.getByLabelText('Nuevo inicio').closest('form')!)

    expect(await screen.findByRole('alert')).toHaveTextContent(mensajeEsperado)
    expect(api).not.toHaveBeenCalledWith('/turnos/17/reprogramacion', expect.anything())
  })

  it('ante conflicto de reprogramación conserva la versión vigente y recarga la agenda', async () => {
    let consultas = 0
    api.mockImplementation(async (ruta) => {
      if (ruta.startsWith('/turnos?')) {
        consultas += 1
        return { items: [{ ...turnoOperativo, id: 17, version: consultas > 1 ? 3 : 2 }], limit: 50, offset: 0 } as never
      }
      if (ruta.startsWith('/profesionales?')) return listaProfesionales as never
      if (ruta.startsWith('/boxes?')) return listaBoxes as never
      if (ruta.startsWith('/pacientes?')) return listaPacientes as never
      if (ruta === '/turnos/17/reprogramacion') {
        throw new ApiError(409, 'version_desactualizada', 'version', 'El turno cambió; revise la agenda actualizada.')
      }
      return undefined as never
    })
    render(<Agenda identidad={{ ...identidadBase, rol: 'recepcion' }} token="token-recepcion" />)

    fireEvent.click(await screen.findByRole('button', { name: 'Reprogramar' }))
    fireEvent.change(screen.getByLabelText('Nuevo inicio'), { target: { value: '2026-11-03T10:00' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar reprogramación' }))

    expect(await screen.findByText('El turno cambió; revise la agenda actualizada.')).toBeInTheDocument()
    expect(screen.getByRole('list', { name: 'Turnos de la agenda' })).toHaveTextContent('Versión: 3')
    expect(screen.queryByText('Reprogramación confirmada.')).not.toBeInTheDocument()
    await waitFor(() => expect(consultas).toBe(2))
  })
})
