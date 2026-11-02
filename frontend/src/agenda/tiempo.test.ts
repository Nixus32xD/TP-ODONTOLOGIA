import { describe, expect, it } from 'vitest'
import { fechaLocalAISO, rangoAgenda, semanaDe } from './tiempo'

describe('conversión de fechas de agenda', () => {
  it('convierte un día de Mendoza a un rango offset-aware semiabierto', () => {
    expect(rangoAgenda('2026-11-02', 'dia')).toEqual({
      desde: '2026-11-02T00:00:00-03:00',
      hasta: '2026-11-03T00:00:00-03:00',
    })
  })

  it('representa la semana local de lunes a lunes', () => {
    expect(semanaDe('2026-11-04')).toBe('2026-11-02')
    expect(rangoAgenda('2026-11-04', 'semana')).toEqual({
      desde: '2026-11-02T00:00:00-03:00',
      hasta: '2026-11-09T00:00:00-03:00',
    })
    const { desde, hasta } = rangoAgenda('2026-11-04', 'semana')
    expect(Date.parse(hasta) - Date.parse(desde)).toBe(7 * 24 * 60 * 60 * 1000)
  })

  it('convierte una fecha local normal de Mendoza con su offset', () => {
    expect(fechaLocalAISO('2026-11-02', '09:15'))
      .toBe('2026-11-02T09:15:00-03:00')
  })

  it('rechaza fechas u horas locales inexistentes y ambiguas en una zona con DST', () => {
    expect(() => fechaLocalAISO('2026-02-30', '09:00')).toThrow('Fecha local inválida')
    expect(() => fechaLocalAISO('2026-03-08', '02:30', 'America/New_York'))
      .toThrow('Hora local inexistente')
    expect(() => fechaLocalAISO('2026-11-01', '01:30', 'America/New_York'))
      .toThrow('Hora local ambigua')
  })
})
