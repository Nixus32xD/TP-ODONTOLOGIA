// Pantallas previstas en el roadmap. Se implementan cuando se propongan sus changes.
const pantallas = [
  { nombre: 'Inicio de sesión del personal (JWT)', change: 'C-03' },
  { nombre: 'Agenda diaria y semanal de recepción', change: 'C-11' },
  { nombre: 'Alta de turno con conflictos explicados', change: 'C-11' },
]

export default function Pendientes() {
  return (
    <section>
      <h2>Pantallas planificadas</h2>
      <ul>
        {pantallas.map((p) => (
          <li key={p.nombre}>
            {p.nombre} — <strong>{p.change}</strong>
          </li>
        ))}
      </ul>
    </section>
  )
}
