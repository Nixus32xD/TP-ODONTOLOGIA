import { readdir, rm } from 'node:fs/promises'
import path from 'node:path'

export default async function teardown() {
  const raizTemporal = process.env.ODONTOLOGIA_E2E_TEMP_ROOT
    ?? process.env.TEMP
    ?? process.env.TMP
  if (!raizTemporal) return

  const raiz = path.resolve(raizTemporal)
  let nombres: string[]
  try {
    nombres = await readdir(raiz)
  } catch {
    return
  }

  for (const nombre of nombres.filter((item) => item.startsWith('tp-odontologia-e2e-'))) {
    const destino = path.resolve(raiz, nombre)
    if (!destino.startsWith(`${raiz}${path.sep}`)) continue
    await rm(destino, { recursive: true, force: true })
  }
}
