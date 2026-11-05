import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../../api'
import Campo from '../../components/Campo'
import ErrorServidor from '../../components/ErrorServidor'

const VACIA = { titulo: '', tipo: 'tarea', peso: '', horas_estimadas: '', fecha_estimada: '' }

export default function Entregas() {
  const [params] = useSearchParams()
  const [materias, setMaterias] = useState([])
  const [progresos, setProgresos] = useState([])   // dependen de la materia elegida
  const [entregas, setEntregas] = useState([])
  const [materiaId, setMateriaId] = useState(params.get('materia') || '')
  const [progresoId, setProgresoId] = useState('')
  const [form, setForm] = useState(VACIA)
  const [error, setError] = useState(null)
  const [ok, setOk] = useState('')

  const cargarProgresos = (id) => api.get(`/api/inscripciones/${id}/progresos`).then(setProgresos)
  const cargarEntregas = () => api.get('/api/entregas' + (materiaId ? `?inscripcion_id=${materiaId}` : '')).then(setEntregas)

  useEffect(() => { api.get('/api/inscripciones').then(setMaterias) }, [])

  // CASCADA: al cambiar la materia se cargan SOLO los progresos de su asignatura.
  useEffect(() => {
    setProgresoId(''); setProgresos([])
    if (materiaId) cargarProgresos(materiaId)
    cargarEntregas()
  }, [materiaId])

  const progreso = progresos.find((p) => String(p.id) === progresoId)
  const disponible = progreso ? Math.round((100 - progreso.cargado) * 100) / 100 : null
  const cambiar = (c) => (e) => setForm({ ...form, [c]: e.target.value })

  const guardar = async (e) => {
    e.preventDefault(); setError(null); setOk('')
    try {
      const r = await api.post('/api/entregas', {
        inscripcion_id: Number(materiaId), progreso_id: Number(progresoId),
        titulo: form.titulo, tipo: form.tipo, peso: Number(form.peso),
        horas_estimadas: Number(form.horas_estimadas), fecha_estimada: form.fecha_estimada || null,
      })
      setOk(`"${r.titulo}" guardada: vale ${r.peso_final} % de la nota final.`)
      setForm(VACIA)
      cargarProgresos(materiaId); cargarEntregas()
    } catch (err) { setError(err) }
  }

  const borrar = async (en) => {
    if (!window.confirm(`¿Borrar "${en.titulo}"?`)) return
    await api.del(`/api/entregas/${en.id}`)
    if (materiaId) cargarProgresos(materiaId)
    cargarEntregas()
  }

  const nombreMateria = (id) => materias.find((m) => m.id === id)?.asignatura.nombre ?? ''

  return (
    <>
      <h1>Entregas</h1>
      <p className="sub">Carga las evaluaciones del sílabo de cada materia.</p>

      {materias.length === 0 ? (
        <div className="tarjeta vacio">Primero inscribe una materia en la pestaña Materias.</div>
      ) : (
        <div className="dos-columnas">
          <form className="tarjeta" onSubmit={guardar}>
            <h2>Nueva entrega</h2>
            <p className="sub sub--chica">El progreso se elige entre los de la materia seleccionada</p>
            <ErrorServidor error={error} />
            {ok && <div className="aviso aviso--ok">{ok}</div>}

            <Campo paso="1" etiqueta="Materia">
              <select required value={materiaId} onChange={(e) => setMateriaId(e.target.value)}>
                <option value="">Elegir materia…</option>
                {materias.map((m) => <option key={m.id} value={m.id}>{m.asignatura.nombre} · {m.periodo.nombre}</option>)}
              </select>
            </Campo>
            <Campo paso="2" etiqueta="Progreso" ayuda={materiaId ? null : 'Primero elige una materia.'}>
              <select required value={progresoId} onChange={(e) => setProgresoId(e.target.value)} disabled={!materiaId}>
                <option value="">Elegir progreso…</option>
                {progresos.map((p) => (
                  <option key={p.id} value={p.id}>
                    Progreso {p.numero} · {p.peso} % de la nota · {p.cargado}/100 cargado
                  </option>
                ))}
              </select>
            </Campo>
            <Campo etiqueta="Título"><input value={form.titulo} onChange={cambiar('titulo')} placeholder="Documento de Análisis" /></Campo>
            <div className="fila fila--3">
              <Campo etiqueta="Tipo">
                <select value={form.tipo} onChange={cambiar('tipo')}>
                  <option value="tarea">Tarea</option><option value="proyecto">Proyecto</option><option value="examen">Examen</option>
                </select>
              </Campo>
              <Campo etiqueta="Peso en el progreso (%)" ayuda={disponible != null ? `Disponible: ${disponible} %` : null}>
                <input type="number" step="any" value={form.peso} onChange={cambiar('peso')} />
              </Campo>
              <Campo etiqueta="Horas estimadas"><input type="number" step="0.5" value={form.horas_estimadas} onChange={cambiar('horas_estimadas')} /></Campo>
            </div>
            <Campo etiqueta="Fecha estimada (según el sílabo)">
              <input type="date" value={form.fecha_estimada} onChange={cambiar('fecha_estimada')} />
            </Campo>
            <div className="acciones"><button className="btn btn--primario" disabled={!progresoId}>Guardar entrega</button></div>
          </form>

          <div className="tarjeta">
            <h2>{materiaId ? `Entregas de ${nombreMateria(Number(materiaId))}` : 'Todas mis entregas'}</h2>
            <div className="tabla-scroll">
              <table>
                <thead><tr><th>Entrega</th>{!materiaId && <th>Materia</th>}<th>Progreso</th><th>Peso</th><th>En la nota final</th><th></th></tr></thead>
                <tbody>
                  {entregas.map((en) => (
                    <tr key={en.id}>
                      <td><b>{en.titulo}</b><br /><span className="tenue">{en.tipo}{en.fecha_estimada && ` · ${new Date(en.fecha_estimada + 'T00:00').toLocaleDateString('es-EC')}`}</span></td>
                      {!materiaId && <td>{nombreMateria(en.inscripcion_id)}</td>}
                      <td>P{en.progreso.numero}</td>
                      <td>{en.peso} %</td>
                      <td>{en.peso_final} %</td>
                      <td><button className="btn btn--peligro btn--mini" onClick={() => borrar(en)}>Borrar</button></td>
                    </tr>
                  ))}
                  {entregas.length === 0 && <tr><td colSpan="6" className="vacio">Sin entregas todavía.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
