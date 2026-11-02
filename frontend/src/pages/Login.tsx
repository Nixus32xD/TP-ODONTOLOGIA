import { FormEvent, useState } from 'react'
import { useSession } from '../auth/session'

export default function Login() {
  const { iniciar, cargando, error, limpiarError } = useSession()
  const [identificador, setIdentificador] = useState('')
  const [password, setPassword] = useState('')

  function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    void iniciar(identificador, password)
  }

  return (
    <main className="pantalla-login">
      <h1>Agenda odontológica</h1>
      <form onSubmit={enviar} aria-busy={cargando}>
        <h2>Iniciar sesión</h2>
        <label htmlFor="identificador">Usuario</label>
        <input
          id="identificador"
          name="identificador"
          type="text"
          autoComplete="username"
          required
          value={identificador}
          onChange={(evento) => {
            setIdentificador(evento.target.value)
            if (error) limpiarError()
          }}
        />
        <label htmlFor="password">Contraseña</label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(evento) => {
            setPassword(evento.target.value)
            if (error) limpiarError()
          }}
        />
        {error && <p role="alert">{error}</p>}
        <button type="submit" disabled={cargando}>
          {cargando ? 'Ingresando…' : 'Iniciar sesión'}
        </button>
        <p role="status" aria-live="polite">{cargando ? 'Validando credenciales…' : ''}</p>
      </form>
    </main>
  )
}
