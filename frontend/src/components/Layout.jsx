import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useSesion } from '../sesion'

const MENUS = {
  admin: [
    ['/admin/asignaturas', 'Asignaturas'],
    ['/admin/carreras', 'Carreras'],
    ['/admin/periodos', 'Períodos'],
    ['/admin/usuarios', 'Usuarios'],
  ],
  estudiante: [
    ['/materias', 'Materias'],
    ['/entregas', 'Entregas'],
  ],
}

export default function Layout() {
  const { usuario, salir } = useSesion()
  const navegar = useNavigate()
  const iniciales = usuario.nombre.split(' ').map((p) => p[0]).slice(0, 2).join('').toUpperCase()

  return (
    <>
      <header className="nav">
        <span className="nav__logo">
          Planificador{usuario.rol === 'admin' && <small> · Administración</small>}
        </span>
        <nav className="nav__links">
          {MENUS[usuario.rol].map(([ruta, texto]) => (
            <NavLink key={ruta} to={ruta} className={({ isActive }) => 'nav__link' + (isActive ? ' nav__link--on' : '')}>
              {texto}
            </NavLink>
          ))}
        </nav>
        <div className="nav__usuario">
          <span className="nav__avatar" title={usuario.correo}>{iniciales}</span>
          <button className="btn btn--suave" onClick={() => { salir(); navegar('/login') }}>Salir</button>
        </div>
      </header>
      <main className="pagina"><Outlet /></main>
    </>
  )
}
