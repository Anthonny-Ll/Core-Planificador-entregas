import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Campo from '../components/Campo'
import ErrorServidor from '../components/ErrorServidor'
import { useSesion } from '../sesion'

export default function Registro() {
  const { entrar } = useSesion()
  const navegar = useNavigate()
  const [form, setForm] = useState({ nombre: '', correo: '', password: '' })
  const [error, setError] = useState(null)
  const cambiar = (c) => (e) => setForm({ ...form, [c]: e.target.value })

  const enviar = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      await entrar('/api/auth/registro', form)
      navegar('/materias')
    } catch (err) { setError(err) }
  }

  return (
    <div className="acceso">
      <form className="tarjeta acceso__caja" onSubmit={enviar}>
        <h1>Crear cuenta</h1>
        <p className="sub">Las cuentas nuevas siempre son de estudiante.</p>
        <ErrorServidor error={error} />
        <Campo etiqueta="Nombre completo"><input required value={form.nombre} onChange={cambiar('nombre')} /></Campo>
        <Campo etiqueta="Correo"><input type="email" required value={form.correo} onChange={cambiar('correo')} /></Campo>
        <Campo etiqueta="Contraseña" ayuda="Mínimo 8 caracteres, con letras y números.">
          <input type="password" required value={form.password} onChange={cambiar('password')} />
        </Campo>
        <button className="btn btn--primario btn--ancho">Crear cuenta</button>
        <p className="acceso__pie">¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link></p>
      </form>
    </div>
  )
}
