import { expect, request, test } from '@playwright/test'

function fechaEnMendoza(diasAdelante: number): string {
  const hoy = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Argentina/Mendoza', year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(new Date())
  const [anio, mes, dia] = hoy.split('-').map(Number)
  return new Date(Date.UTC(anio, mes - 1, dia + diasAdelante)).toISOString().slice(0, 10)
}

async function ingresarRecepcion(page: import('@playwright/test').Page) {
  const respuestaLogin = page.waitForResponse((respuesta) =>
    respuesta.url().endsWith('/api/sesiones') && respuesta.request().method() === 'POST')
  await page.goto('/')
  await page.getByLabel('Usuario').fill('recepcion.e2e')
  await page.getByLabel('Contraseña').fill('Clave-E2E-recepcion-2026!')
  await page.getByRole('button', { name: 'Iniciar sesión' }).click()
  const token = (await (await respuestaLogin).json()).access_token as string
  await expect(page.getByRole('heading', { name: 'Operación de agenda' })).toBeVisible()
  return token
}

async function consultarDisponibilidad(page: import('@playwright/test').Page, fecha: string) {
  await page.getByLabel('Fecha', { exact: true }).fill(fecha)
  await page.getByLabel('Fecha de disponibilidad').fill(fecha)
  await page.getByLabel('Profesional para disponibilidad').selectOption({ label: 'Dra. E2E' })
  await page.getByLabel('Box para disponibilidad').selectOption({ label: 'Box E2E' })
  await page.getByLabel('Duración en minutos', { exact: true }).first().fill('30')
  await page.getByRole('button', { name: 'Consultar disponibilidad' }).click()
  const opcion = page.getByRole('list', { name: 'Opciones disponibles' }).locator('li').first()
  await expect(opcion.getByRole('button', { name: 'Elegir horario' })).toBeVisible()
  return opcion
}

test('teclado y foco visible alcanzan la pantalla de acceso', async ({ page }) => {
  await page.goto('/')
  await page.keyboard.press('Tab')

  const usuario = page.getByLabel('Usuario')
  await expect(usuario).toBeFocused()
  expect(await usuario.evaluate((element) => getComputedStyle(element).outlineWidth)).toBe('3px')
  await page.keyboard.press('Tab')
  await expect(page.getByLabel('Contraseña')).toBeFocused()
})

test('recepción consulta, crea, reprograma, confirma, cancela y revoca sesión', async ({ page }) => {
  const token = await ingresarRecepcion(page)
  const fecha = fechaEnMendoza(3)
  const opcion = await consultarDisponibilidad(page, fecha)
  await opcion.getByRole('button', { name: 'Elegir horario' }).click()
  await page.getByLabel('Paciente').selectOption({ label: 'Paciente Ficticio E2E' })
  await page.getByRole('button', { name: 'Registrar turno' }).click()
  await expect(page.getByText('Turno reservado.', { exact: true })).toBeVisible()
  const agenda = page.getByRole('list', { name: 'Turnos de la agenda' })
  await expect(agenda).toContainText('Paciente Ficticio E2E')

  await page.getByRole('button', { name: 'Reprogramar' }).click()
  await page.getByLabel('Nuevo inicio').fill(`${fecha}T10:00`)
  await page.getByRole('button', { name: 'Guardar reprogramación' }).click()
  await expect(page.getByText('Reprogramación confirmada.', { exact: true })).toBeVisible()
  await expect(agenda).toContainText('10:00')

  await page.getByRole('button', { name: 'Confirmar' }).click()
  await expect(agenda).toContainText('confirmado')
  await page.getByRole('button', { name: 'Cancelar', exact: true }).click()
  await expect(agenda).toContainText('cancelado')

  await page.getByRole('button', { name: 'Cerrar sesión' }).click()
  await expect(page.getByRole('heading', { name: 'Iniciar sesión' })).toBeVisible()
  const api = await request.newContext({ baseURL: 'http://127.0.0.1:8180' })
  const revocada = await api.get('/sesiones/actual', { headers: { Authorization: `Bearer ${token}` } })
  expect(revocada.status()).toBe(401)
  await api.dispose()
})

test('Profesional selecciona una atención sintética y consulta su odontograma y plan', async ({ page }) => {
  await page.goto('/')
  await page.getByLabel('Usuario').fill('profesional.e2e')
  await page.getByLabel('Contraseña').fill('Clave-E2E-profesional-2026!')
  await page.getByRole('button', { name: 'Iniciar sesión' }).click()
  await expect(page.getByRole('heading', { name: 'Atenciones clínicas' })).toBeVisible()

  const seleccion = page.getByLabel('Atención atendida')
  await expect(seleccion.locator('option').nth(1)).toContainText('Paciente Ficticio E2E')
  await seleccion.selectOption({ index: 1 })

  await expect(page.getByRole('heading', { name: 'Odontograma' })).toBeVisible()
  await expect(page.getByText('Versión vigente: 1')).toBeVisible()
  await expect(page.getByText('sin registros de hallazgo')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Planes manuales' })).toBeVisible()
  await expect(page.getByText('Plan plan-e2e — propuesto')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Crear turno' })).toHaveCount(0)
})

test('un solapamiento agregado por API se muestra como conflicto y no como alta exitosa', async ({ page }) => {
  const token = await ingresarRecepcion(page)
  const fecha = fechaEnMendoza(5)
  const opcion = await consultarDisponibilidad(page, fecha)
  const horarios = opcion.locator('time')
  const inicio = await horarios.nth(0).getAttribute('datetime')
  const fin = await horarios.nth(1).getAttribute('datetime')
  await opcion.getByRole('button', { name: 'Elegir horario' }).click()
  await page.getByLabel('Paciente').selectOption({ label: 'Paciente Ficticio E2E' })

  const api = await request.newContext({ baseURL: 'http://127.0.0.1:8180' })
  const [profesionales, boxes, pacientes] = await Promise.all([
    api.get('/profesionales?limit=100&offset=0', { headers: { Authorization: `Bearer ${token}` } }),
    api.get('/boxes?limit=100&offset=0', { headers: { Authorization: `Bearer ${token}` } }),
    api.get('/pacientes?limit=100&offset=0', { headers: { Authorization: `Bearer ${token}` } }),
  ])
  const profesional = (await profesionales.json()).items.find((item: { nombre: string }) => item.nombre === 'Dra. E2E')
  const box = (await boxes.json()).items.find((item: { nombre: string }) => item.nombre === 'Box E2E')
  const paciente = (await pacientes.json()).items.find((item: { nombre: string }) => item.nombre === 'Paciente Ficticio E2E')
  const creadaDesdeApi = await api.post('/turnos', {
    headers: { Authorization: `Bearer ${token}` },
    data: { paciente_id: paciente.id, profesional_id: profesional.id, box_id: box.id, inicio, fin },
  })
  expect(creadaDesdeApi.status()).toBe(201)

  await page.getByRole('button', { name: 'Registrar turno' }).click()
  await expect(page.locator('[role="alert"]').filter({ hasText: 'El profesional ya está ocupado' })).toBeVisible()
  await expect(page.getByText('Turno reservado.')).toHaveCount(0)
  await expect(page.getByRole('list', { name: 'Turnos de la agenda' })).toContainText('Paciente Ficticio E2E')
  await api.dispose()
})
