import { useEffect, useState } from 'react'
import { consultarSalud } from './api/cliente.ts'
import Pendientes from './pages/Pendientes.tsx'

export default function App() {
  const [estado, setEstado] = useState('consultando…')

  useEffect(() => {
    consultarSalud()
      .then((r) => setEstado(r.status === 'ok' ? 'API disponible' : `estado: ${r.status}`))
      .catch((error: Error) => setEstado(`sin conexión (${error.message})`))
  }, [])

  return (
    <main style={{ fontFamily: 'system-ui, sans-serif', maxWidth: 720, margin: '2rem auto', padding: '0 1rem' }}>
      <h1>Agenda odontológica</h1>
      <p>
        Backend (<code>GET /health</code>): <strong>{estado}</strong>
      </p>
      <Pendientes />
    </main>
  )
}
