import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../api/cliente'
import CuentaCorriente from './CuentaCorriente'

vi.mock('../api/cliente', async (importOriginal) => {
  const original = await importOriginal<typeof import('../api/cliente')>()
  return { ...original, apiRequest: vi.fn() }
})

describe('cuenta corriente del personal', () => {
  const api = vi.mocked(apiRequest)

  beforeEach(() => {
    api.mockReset()
    window.localStorage.clear()
    let saldo = '0.00'
    api.mockImplementation(async (ruta, options) => {
      if (String(ruta).startsWith('/pacientes?')) {
        return { items: [{ id: 'paciente-1', nombre: 'Paciente sintético', activo: true }], limit: 100, offset: 0 } as never
      }
      if (String(ruta) === '/finanzas/pacientes/paciente-1') {
        return { items: [], saldo_ars: saldo } as never
      }
      if (options?.method === 'POST') {
        saldo = '12.30'
        return { id: 'cargo-1', tipo: 'cargo', monto_ars: '12.30', saldo_ars: '12.30' } as never
      }
      return {} as never
    })
  })

  it('registra cargos con importe textual exacto y clave idempotente', async () => {
    render(<CuentaCorriente token="token-sintético" rol="recepcion" />)
    await screen.findByRole('option', { name: 'Paciente sintético' })
    fireEvent.change(screen.getByLabelText('Importe del cargo ARS'), { target: { value: '12.30' } })
    fireEvent.change(screen.getByLabelText('Concepto'), { target: { value: 'Control sintético' } })
    fireEvent.click(screen.getByRole('button', { name: 'Registrar cargo' }))

    await waitFor(() => expect(api).toHaveBeenCalledWith(
      '/finanzas/pacientes/paciente-1/cargos', expect.objectContaining({
        method: 'POST', headers: expect.objectContaining({ 'Idempotency-Key': expect.any(String) }),
        body: JSON.stringify({ monto_ars: '12.30', concepto: 'Control sintético' }),
      }),
    ))
    expect(await screen.findByText('Saldo: ARS 12.30')).toBeInTheDocument()
  })

  it('reserva la reversión al rol Administrador', async () => {
    const { rerender } = render(<CuentaCorriente token="token-sintético" rol="recepcion" />)
    await screen.findByRole('option', { name: 'Paciente sintético' })
    expect(screen.queryByRole('heading', { name: 'Revertir cobro' })).not.toBeInTheDocument()
    rerender(<CuentaCorriente token="token-sintético" rol="administrador" />)
    expect(await screen.findByRole('heading', { name: 'Revertir cobro' })).toBeInTheDocument()
  })

  it('reutiliza la clave al reintentar el mismo comando tras error de red', async () => {
    api.mockImplementation(async (ruta, options) => {
      if (String(ruta).startsWith('/pacientes?')) {
        return { items: [{ id: 'paciente-1', nombre: 'Paciente sintético', activo: true }], limit: 100, offset: 0 } as never
      }
      if (String(ruta) === '/finanzas/pacientes/paciente-1') return { items: [], saldo_ars: '0.00' } as never
      if (options?.method === 'POST') throw new Error('respuesta ambigua de red')
      return {} as never
    })
    render(<CuentaCorriente token="token-sintético" rol="administrador" />)
    await screen.findByRole('option', { name: 'Paciente sintético' })
    fireEvent.change(screen.getByLabelText('Importe del cargo ARS'), { target: { value: '4.50' } })
    fireEvent.change(screen.getByLabelText('Concepto'), { target: { value: 'Consulta' } })
    const boton = screen.getByRole('button', { name: 'Registrar cargo' })
    fireEvent.click(boton)
    await screen.findByRole('alert')
    fireEvent.click(boton)
    await waitFor(() => expect(api.mock.calls.filter(([ruta, options]) =>
      String(ruta).endsWith('/cargos') && options?.method === 'POST')).toHaveLength(2))
    const keys = api.mock.calls.filter(([ruta, options]) =>
      String(ruta).endsWith('/cargos') && options?.method === 'POST')
      .map(([, options]) => new Headers(options?.headers).get('Idempotency-Key'))
    expect(keys[0]).toBe(keys[1])
  })

  it('recupera la misma clave después de desmontar y montar de nuevo', async () => {
    let clavePrimera: string | null = null
    api.mockImplementation(async (ruta, options) => {
      if (String(ruta).startsWith('/pacientes?')) {
        return { items: [{ id: 'paciente-1', nombre: 'Paciente sintético', activo: true }], limit: 100, offset: 0 } as never
      }
      if (String(ruta) === '/finanzas/pacientes/paciente-1') return { items: [], saldo_ars: '0.00' } as never
      if (options?.method === 'POST') {
        const clave = new Headers(options?.headers).get('Idempotency-Key')
        if (clavePrimera === null) {
          clavePrimera = clave
          throw new Error('respuesta ambigua de red')
        }
        return { id: 'cargo-1', tipo: 'cargo', monto_ars: '4.50', saldo_ars: '4.50' } as never
      }
      return {} as never
    })
    const props = { token: 'token-sintético', rol: 'administrador' as const }
    const primera = render(<CuentaCorriente {...props} />)
    await screen.findByRole('option', { name: 'Paciente sintético' })
    fireEvent.change(screen.getByLabelText('Importe del cargo ARS'), { target: { value: '4.50' } })
    fireEvent.change(screen.getByLabelText('Concepto'), { target: { value: 'Consulta' } })
    fireEvent.click(screen.getByRole('button', { name: 'Registrar cargo' }))
    await screen.findByRole('alert')
    primera.unmount()

    render(<CuentaCorriente {...props} />)
    await screen.findByRole('option', { name: 'Paciente sintético' })
    fireEvent.change(screen.getByLabelText('Importe del cargo ARS'), { target: { value: '4.50' } })
    fireEvent.change(screen.getByLabelText('Concepto'), { target: { value: 'Consulta' } })
    fireEvent.click(screen.getByRole('button', { name: 'Registrar cargo' }))
    await waitFor(() => expect(api.mock.calls.filter(([ruta, options]) =>
      String(ruta).endsWith('/cargos') && options?.method === 'POST')).toHaveLength(2))
    const keys = api.mock.calls.filter(([ruta, options]) =>
      String(ruta).endsWith('/cargos') && options?.method === 'POST')
      .map(([, options]) => new Headers(options?.headers).get('Idempotency-Key'))
    expect(keys[0]).toBe(keys[1])
  })

  it('bloquea cobros de la cuenta anterior mientras cambia de paciente', async () => {
    let liberarCuentaDos: ((cuenta: { items: { id: string; tipo: 'cargo'; monto_ars: string; created_at: string }[]; saldo_ars: string }) => void) | undefined
    api.mockImplementation(async (ruta) => {
      if (String(ruta).startsWith('/pacientes?')) {
        return { items: [
          { id: 'paciente-1', nombre: 'Paciente uno', activo: true },
          { id: 'paciente-2', nombre: 'Paciente dos', activo: true },
        ], limit: 100, offset: 0 } as never
      }
      if (String(ruta) === '/finanzas/pacientes/paciente-1') {
        return { items: [{ id: 'cargo-uno', tipo: 'cargo', monto_ars: '10.00', concepto: 'Uno', created_at: '2026-11-02T10:00:00Z' }], saldo_ars: '10.00' } as never
      }
      if (String(ruta) === '/finanzas/pacientes/paciente-2') {
        return await new Promise<{ items: { id: string; tipo: 'cargo'; monto_ars: string; created_at: string }[]; saldo_ars: string }>((resolve) => { liberarCuentaDos = resolve }) as never
      }
      return {} as never
    })
    render(<CuentaCorriente token="token-sintético" rol="administrador" />)
    await screen.findByRole('option', { name: 'Paciente uno' })
    await screen.findByRole('option', { name: /Uno · 10.00/ })
    fireEvent.change(screen.getByLabelText('Paciente'), { target: { value: 'paciente-2' } })
    expect(await screen.findByText('Consultando cuenta…')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Registrar cobro' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Registrar reversión' })).toBeDisabled()
    liberarCuentaDos?.({ items: [], saldo_ars: '0.00' })
    await waitFor(() => expect(screen.queryByText('Consultando cuenta…')).not.toBeInTheDocument())
  })

  it('ignora una respuesta tardía de la cuenta que ya no está seleccionada', async () => {
    let liberarCuentaDos: ((cuenta: { items: { id: string; tipo: 'cargo'; monto_ars: string; concepto: string; created_at: string }[]; saldo_ars: string }) => void) | undefined
    api.mockImplementation(async (ruta) => {
      if (String(ruta).startsWith('/pacientes?')) {
        return { items: [
          { id: 'paciente-1', nombre: 'Paciente uno', activo: true },
          { id: 'paciente-2', nombre: 'Paciente dos', activo: true },
          { id: 'paciente-3', nombre: 'Paciente tres', activo: true },
        ], limit: 100, offset: 0 } as never
      }
      if (String(ruta) === '/finanzas/pacientes/paciente-1') return { items: [], saldo_ars: '0.00' } as never
      if (String(ruta) === '/finanzas/pacientes/paciente-2') {
        return await new Promise<{ items: { id: string; tipo: 'cargo'; monto_ars: string; concepto: string; created_at: string }[]; saldo_ars: string }>((resolve) => { liberarCuentaDos = resolve }) as never
      }
      if (String(ruta) === '/finanzas/pacientes/paciente-3') {
        return { items: [{ id: 'cargo-tres', tipo: 'cargo', monto_ars: '3.00', concepto: 'Tres', created_at: '2026-11-02T10:00:00Z' }], saldo_ars: '3.00' } as never
      }
      return {} as never
    })
    render(<CuentaCorriente token="token-sintético" rol="administrador" />)
    await screen.findByRole('option', { name: 'Paciente uno' })
    fireEvent.change(screen.getByLabelText('Paciente'), { target: { value: 'paciente-2' } })
    await screen.findByText('Consultando cuenta…')
    fireEvent.change(screen.getByLabelText('Paciente'), { target: { value: 'paciente-3' } })
    await screen.findByRole('option', { name: /Tres · 3.00/ })
    liberarCuentaDos?.({ items: [{ id: 'cargo-dos', tipo: 'cargo', monto_ars: '2.00', concepto: 'Dos', created_at: '2026-11-02T10:00:00Z' }], saldo_ars: '2.00' })
    await waitFor(() => expect(screen.getByLabelText('Paciente')).toHaveValue('paciente-3'))
    expect(screen.getByRole('option', { name: /Tres · 3.00/ })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: /Dos · 2.00/ })).not.toBeInTheDocument()
  })
})
