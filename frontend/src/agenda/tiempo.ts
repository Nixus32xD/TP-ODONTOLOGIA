export const ZONA_AGENDA = 'America/Argentina/Mendoza'

type TipoRango = 'dia' | 'semana'
type PartesLocales = { year: number; month: number; day: number; hour: number; minute: number }

function parsearFechaHora(fecha: string, hora: string) {
  const f = /^(\d{4})-(\d{2})-(\d{2})$/.exec(fecha)
  const h = /^(\d{2}):(\d{2})$/.exec(hora)
  if (!f || !h) throw new Error('Fecha local inválida.')
  const [, y, m, d] = f
  const [, hh, mm] = h
  const valores = { year: Number(y), month: Number(m), day: Number(d), hour: Number(hh), minute: Number(mm) }
  const verificacion = new Date(Date.UTC(valores.year, valores.month - 1, valores.day))
  if (verificacion.getUTCFullYear() !== valores.year
      || verificacion.getUTCMonth() + 1 !== valores.month
      || verificacion.getUTCDate() !== valores.day
      || valores.hour > 23 || valores.minute > 59) {
    throw new Error('Fecha local inválida.')
  }
  return valores
}

function partesEnZona(instante: number, zona: string): PartesLocales {
  const partes = new Intl.DateTimeFormat('en-CA', {
    timeZone: zona,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(new Date(instante))
  const valor = (tipo: string) => Number(partes.find((parte) => parte.type === tipo)?.value)
  return {
    year: valor('year'), month: valor('month'), day: valor('day'),
    hour: valor('hour'), minute: valor('minute'),
  }
}

function coincide(a: PartesLocales, b: PartesLocales): boolean {
  return a.year === b.year && a.month === b.month && a.day === b.day
    && a.hour === b.hour && a.minute === b.minute
}

function offsetEnMinutos(instante: number, zona: string): number {
  const local = partesEnZona(instante, zona)
  const comoUtc = Date.UTC(local.year, local.month - 1, local.day, local.hour, local.minute)
  return (comoUtc - instante) / 60_000
}

function formatoOffset(minutos: number): string {
  const signo = minutos >= 0 ? '+' : '-'
  const total = Math.abs(minutos)
  return `${signo}${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
}

export function fechaLocalAISO(fecha: string, hora: string, zona = ZONA_AGENDA): string {
  const local = parsearFechaHora(fecha, hora)
  const instanteIngenuo = Date.UTC(
    local.year, local.month - 1, local.day, local.hour, local.minute,
  )
  const offsets = new Set([
    offsetEnMinutos(instanteIngenuo - 36 * 60 * 60_000, zona),
    offsetEnMinutos(instanteIngenuo, zona),
    offsetEnMinutos(instanteIngenuo + 36 * 60 * 60_000, zona),
  ])
  const candidatos = [...offsets]
    .map((offset) => ({ instante: instanteIngenuo - offset * 60_000, offset }))
    .filter(({ instante }) => coincide(partesEnZona(instante, zona), local))

  if (candidatos.length === 0) throw new Error('Hora local inexistente en la zona seleccionada.')
  if (candidatos.length > 1) throw new Error('Hora local ambigua en la zona seleccionada.')
  const { offset } = candidatos[0]
  return `${fecha}T${hora}:00${formatoOffset(offset)}`
}

function sumarDias(fecha: string, dias: number): string {
  const { year, month, day } = parsearFechaHora(fecha, '00:00')
  const resultado = new Date(Date.UTC(year, month - 1, day + dias))
  return resultado.toISOString().slice(0, 10)
}

export function semanaDe(fecha: string): string {
  const { year, month, day } = parsearFechaHora(fecha, '00:00')
  const diaSemana = new Date(Date.UTC(year, month - 1, day)).getUTCDay()
  return sumarDias(fecha, -((diaSemana + 6) % 7))
}

export function rangoAgenda(fecha: string, tipo: TipoRango) {
  const inicio = tipo === 'semana' ? semanaDe(fecha) : sumarDias(fecha, 0)
  const fin = sumarDias(inicio, tipo === 'semana' ? 7 : 1)
  return {
    desde: fechaLocalAISO(inicio, '00:00'),
    hasta: fechaLocalAISO(fin, '00:00'),
  }
}

export function mostrarFechaHora(valor: string): string {
  return new Intl.DateTimeFormat('es-AR', {
    timeZone: ZONA_AGENDA,
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(valor))
}
