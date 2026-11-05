import { useEffect, useState } from 'react'
import { api } from '../../api'
import ErrorServidor from '../../components/ErrorServidor'

export default function Usuarios() {
  const [usuarios, setUsuarios] = useState([])
  const [error, setError] = useState(null)
  const cargar = () => api.get('/api/admin/usuarios').then(setUsuarios)
  useEffect(() => { cargar() }, [])

  const alternar = async (u) => {
    setError(null)
    try { await api.patch(`/api/admin/usuarios/${u.id}`, { activo: !u.activo }); cargar() } catch (err) { setError(err) }
  }

  return (
    <>
      <h1>Usuarios</h1>
      <p className="sub">Un usuario desactivado ya no puede iniciar sesión.</p>
      <ErrorServidor error={error} />
      <div className="tarjeta tabla-scroll">
        <table>
          <thead><tr><th>Nombre</th><th>Correo</th><th>Rol</th><th>Estado</th><th></th></tr></thead>
          <tbody>
            {usuarios.map((u) => (
              <tr key={u.id}>
                <td>{u.nombre}</td><td>{u.correo}</td>
                <td><span className={'insignia' + (u.rol === 'admin' ? ' insignia--solida' : '')}>{u.rol}</span></td>
                <td>{u.activo ? 'Activo' : 'Desactivado'}</td>
                <td className="celda-acciones">
                  <button className={'btn btn--mini ' + (u.activo ? 'btn--peligro' : 'btn--suave')} onClick={() => alternar(u)}>
                    {u.activo ? 'Desactivar' : 'Activar'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
