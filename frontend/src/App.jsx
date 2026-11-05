import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { useSesion } from './sesion'
import Login from './pages/Login'
import Registro from './pages/Registro'
import Asignaturas from './pages/admin/Asignaturas'
import Carreras from './pages/admin/Carreras'
import Periodos from './pages/admin/Periodos'
import Usuarios from './pages/admin/Usuarios'
import Materias from './pages/estudiante/Materias'
import Entregas from './pages/estudiante/Entregas'

// Solo deja entrar si hay sesión y el rol coincide. (Es comodidad visual:
// la protección real está en el backend, que responde 401/403.)
function Protegida({ rol, children }) {
  const { usuario } = useSesion()
  if (!usuario) return <Navigate to="/login" replace />
  if (usuario.rol !== rol) return <Navigate to={inicioDe(usuario)} replace />
  return children
}

export const inicioDe = (u) => (u?.rol === 'admin' ? '/admin/asignaturas' : '/materias')

export default function App() {
  const { usuario } = useSesion()
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/registro" element={<Registro />} />
      <Route element={<Protegida rol="admin"><Layout /></Protegida>}>
        <Route path="/admin/asignaturas" element={<Asignaturas />} />
        <Route path="/admin/carreras" element={<Carreras />} />
        <Route path="/admin/periodos" element={<Periodos />} />
        <Route path="/admin/usuarios" element={<Usuarios />} />
      </Route>
      <Route element={<Protegida rol="estudiante"><Layout /></Protegida>}>
        <Route path="/materias" element={<Materias />} />
        <Route path="/entregas" element={<Entregas />} />
      </Route>
      <Route path="*" element={<Navigate to={usuario ? inicioDe(usuario) : '/login'} replace />} />
    </Routes>
  )
}
