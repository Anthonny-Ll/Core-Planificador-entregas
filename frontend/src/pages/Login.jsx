import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import Campo from '../components/Campo'
import ErrorServidor from '../components/ErrorServidor'
import { useSesion } from '../sesion'
import { inicioDe } from '../App'

export default function Login() {
  const { usuario, entrar } = useSesion()
  const navegar = useNavigate()
  const [form, setForm] = useState({ correo: '', password: '' })
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)

  if (usuario) return <Navigate to={inicioDe(usuario)} replace />

  const enviar = async (e) => {
    e.preventDefault()
    setEnviando(true); setError(null)
    try {
      navegar(inicioDe(await entrar('/api/auth/login', form)))
    } catch (err) { setError(err) } finally { setEnviando(false) }
  }

  return (
    <div className="acceso">
      <form className="tarjeta acceso__caja" onSubmit={enviar}>
        <h1>Planificador de entregas</h1>
        <p className="sub">Inicia sesión para organizar tus entregas del semestre.</p>
        <ErrorServidor error={error} />
        <Campo etiqueta="Correo">
          <input type="email" required value={form.correo} autoComplete="username"
            onChange={(e) => setForm({ ...form, correo: e.target.value })} />
        </Campo>
        <Campo etiqueta="Contraseña">
          <input type="password" required value={form.password} autoComplete="current-password"
            onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </Campo>
        <button className="btn btn--primario btn--ancho" disabled={enviando}>
          {enviando ? 'Entrando…' : 'Entrar'}
        </button>
        <p className="acceso__pie">¿No tienes cuenta? <Link to="/registro">Regístrate como estudiante</Link></p>
      </form>
    </div>
  )
}
