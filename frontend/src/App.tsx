import Login from './pages/Login'
import { SessionProvider, useSession } from './auth/session'
import Agenda from './agenda/Agenda'
import Catalogos from './pages/Catalogos'
import Disponibilidad from './pages/Disponibilidad'
import AtencionesClinicas from './pages/AtencionesClinicas'
import PortalPaciente from './pages/PortalPaciente'
import CuentaCorriente from './pages/CuentaCorriente'

function InicioSesionActiva() {
  const { identidad, cerrar, token } = useSession()
  if (!identidad || !token) return null

  const esProfesional = identidad.rol === 'profesional'

  if (identidad.rol === 'paciente') {
    return (
      <main className="aplicacion">
        <header>
          <div>
            <h1>Agenda odontológica</h1>
            <p>Portal del paciente · demostración sintética</p>
          </div>
          <button type="button" onClick={() => void cerrar()}>Cerrar sesión</button>
        </header>
        <PortalPaciente token={token} />
      </main>
    )
  }

  return (
    <main className="aplicacion">
      <header>
        <div>
          <h1>Agenda odontológica</h1>
          <p>Sesión de {identidad.rol}</p>
        </div>
        <button type="button" onClick={() => void cerrar()}>Cerrar sesión</button>
      </header>
      <section aria-live="polite">
        <h2>{esProfesional ? 'Consulta de agenda propia' : 'Operación de agenda'}</h2>
        <p>
          {esProfesional
            ? 'La cuenta Profesional puede consultar únicamente su agenda.'
            : 'La agenda y sus cambios se confirman desde la API.'}
        </p>
      </section>
      <Agenda identidad={identidad} token={token} />
      {esProfesional && <AtencionesClinicas token={token} />}
      {identidad.rol !== 'profesional' && <>
        <Catalogos rol={identidad.rol} token={token} />
        <Disponibilidad token={token} />
        <CuentaCorriente rol={identidad.rol} token={token} />
      </>}
    </main>
  )
}

function ContenidoAutenticado() {
  const { identidad } = useSession()
  return identidad ? <InicioSesionActiva /> : <Login />
}

export default function App() {
  return (
    <SessionProvider>
      <ContenidoAutenticado />
    </SessionProvider>
  )
}
