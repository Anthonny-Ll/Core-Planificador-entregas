import { useEffect, useState } from 'react'
import { api } from '../../api'
import Campo from '../../components/Campo'
import ErrorServidor from '../../components/ErrorServidor'

const VACIO = { nombre: '', fecha_inicio: '', fecha_fin: '', activo: false }
const fecha = (iso) => new Date(iso + 'T00:00').toLocaleDateString('es-EC')

export default function Periodos() {
  const [periodos, setPeriodos] = useState([])
  const [form, setForm] = useState(VACIO)
  const [editando, setEditando] = useState(null)
  const [error, setError] = useState(null)

  const cargar = () => api.get('/api/admin/periodos').then(setPeriodos)
  useEffect(() => { cargar() }, [])
  const limpiar = () => { setForm(VACIO); setEditando(null) }

  const guardar = async (e) => {
    e.preventDefault(); setError(null)
    try {
      if (editando) await api.put(`/api/admin/periodos/${editando}`, form)
      else await api.post('/api/admin/periodos', form)
      limpiar(); cargar()
    } catch (err) { setError(err) }
  }

  const borrar = async (p) => {
    if (!window.confirm(`¿Borrar el período ${p.nombre}?`)) return
    setError(null)
    try { await api.del(`/api/admin/periodos/${p.id}`); cargar() } catch (err) { setError(err) }
  }

  return (
    <>
      <h1>Períodos académicos</h1>
      <p className="sub">Solo un período puede estar activo a la vez.</p>
      <ErrorServidor error={error} />
      <form className="tarjeta fila fila--form" onSubmit={guardar}>
        <Campo etiqueta="Nombre" ayuda="Ej. 2026-2"><input required value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} /></Campo>
        <Campo etiqueta="Inicio"><input type="date" required value={form.fecha_inicio} onChange={(e) => setForm({ ...form, fecha_inicio: e.target.value })} /></Campo>
        <Campo etiqueta="Fin"><input type="date" required value={form.fecha_fin} onChange={(e) => setForm({ ...form, fecha_fin: e.target.value })} /></Campo>
        <label className="check"><input type="checkbox" checked={form.activo} onChange={(e) => setForm({ ...form, activo: e.target.checked })} /> Activo</label>
        <div className="acciones">
          {editando && <button type="button" className="btn btn--suave" onClick={limpiar}>Cancelar</button>}
          <button className="btn btn--primario">{editando ? 'Guardar cambios' : 'Agregar período'}</button>
        </div>
      </form>
      <div className="tarjeta tabla-scroll">
        <table>
          <thead><tr><th>Período</th><th>Inicio</th><th>Fin</th><th>Estado</th><th></th></tr></thead>
          <tbody>
            {periodos.map((p) => (
              <tr key={p.id}>
                <td><b>{p.nombre}</b></td><td>{fecha(p.fecha_inicio)}</td><td>{fecha(p.fecha_fin)}</td>
                <td>{p.activo ? <span className="insignia insignia--solida">Activo</span> : <span className="insignia">Inactivo</span>}</td>
                <td className="celda-acciones">
                  <button className="btn btn--suave btn--mini" onClick={() => { setEditando(p.id); setForm({ nombre: p.nombre, fecha_inicio: p.fecha_inicio, fecha_fin: p.fecha_fin, activo: p.activo }) }}>Editar</button>
                  <button className="btn btn--peligro btn--mini" onClick={() => borrar(p)}>Borrar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
