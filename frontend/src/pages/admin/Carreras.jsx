import { useEffect, useState } from 'react'
import { api } from '../../api'
import Campo from '../../components/Campo'
import ErrorServidor from '../../components/ErrorServidor'

export default function Carreras() {
  const [carreras, setCarreras] = useState([])
  const [form, setForm] = useState({ codigo: '', nombre: '' })
  const [editando, setEditando] = useState(null)
  const [error, setError] = useState(null)

  const cargar = () => api.get('/api/admin/carreras').then(setCarreras)
  useEffect(() => { cargar() }, [])

  const limpiar = () => { setForm({ codigo: '', nombre: '' }); setEditando(null) }

  const guardar = async (e) => {
    e.preventDefault(); setError(null)
    try {
      if (editando) await api.put(`/api/admin/carreras/${editando}`, form)
      else await api.post('/api/admin/carreras', form)
      limpiar(); cargar()
    } catch (err) { setError(err) }
  }

  const borrar = async (c) => {
    if (!window.confirm(`¿Borrar la carrera ${c.nombre}?`)) return
    setError(null)
    try { await api.del(`/api/admin/carreras/${c.id}`); cargar() } catch (err) { setError(err) }
  }

  return (
    <>
      <h1>Carreras</h1>
      <p className="sub">Cada asignatura pertenece a una carrera.</p>
      <ErrorServidor error={error} />
      <form className="tarjeta fila fila--form" onSubmit={guardar}>
        <Campo etiqueta="Código" ayuda="Entre 2 y 10 letras"><input value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })} placeholder="ISW" /></Campo>
        <Campo etiqueta="Nombre"><input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} /></Campo>
        <div className="acciones">
          {editando && <button type="button" className="btn btn--suave" onClick={limpiar}>Cancelar</button>}
          <button className="btn btn--primario">{editando ? 'Guardar cambios' : 'Agregar carrera'}</button>
        </div>
      </form>
      <div className="tarjeta tabla-scroll">
        <table>
          <thead><tr><th>Código</th><th>Nombre</th><th></th></tr></thead>
          <tbody>
            {carreras.map((c) => (
              <tr key={c.id}>
                <td><b>{c.codigo}</b></td><td>{c.nombre}</td>
                <td className="celda-acciones">
                  <button className="btn btn--suave btn--mini" onClick={() => { setEditando(c.id); setForm({ codigo: c.codigo, nombre: c.nombre }) }}>Editar</button>
                  <button className="btn btn--peligro btn--mini" onClick={() => borrar(c)}>Borrar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
