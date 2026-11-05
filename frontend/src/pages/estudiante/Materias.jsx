import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api'
import Campo from '../../components/Campo'
import ErrorServidor from '../../components/ErrorServidor'

const COLORES = [['#1f6feb', 'Azul'], ['#1a7f37', 'Verde'], ['#bf3989', 'Rosa'], ['#9a6700', 'Mostaza'], ['#6e40c9', 'Morado'], ['#cf222e', 'Rojo']]

export default function Materias() {
  const [periodos, setPeriodos] = useState([])
  const [carreras, setCarreras] = useState([])
  const [asignaturas, setAsignaturas] = useState([])   // dependen de la carrera elegida
  const [cargandoAsig, setCargandoAsig] = useState(false)
  const [inscripciones, setInscripciones] = useState([])
  const [form, setForm] = useState({ periodo_id: '', carrera_id: '', asignatura_id: '', nota_meta: '', color: COLORES[0][0] })
  const [error, setError] = useState(null)
  const [ok, setOk] = useState('')

  const cargarInscripciones = () => api.get('/api/inscripciones').then(setInscripciones)

  useEffect(() => {
    api.get('/api/catalogo/periodos').then((ps) => {
      setPeriodos(ps)
      const activo = ps.find((p) => p.activo)
      if (activo) setForm((f) => ({ ...f, periodo_id: String(activo.id) }))
    })
    api.get('/api/catalogo/carreras').then(setCarreras)
    cargarInscripciones()
  }, [])

  // CASCADA: cada vez que cambia la carrera se piden SOLO sus asignaturas al backend.
  useEffect(() => {
    setForm((f) => ({ ...f, asignatura_id: '' }))
    setAsignaturas([])
    if (!form.carrera_id) return
    setCargandoAsig(true)
    api.get(`/api/catalogo/carreras/${form.carrera_id}/asignaturas`)
      .then(setAsignaturas)
      .finally(() => setCargandoAsig(false))
  }, [form.carrera_id])

  const cambiar = (c) => (e) => setForm({ ...form, [c]: e.target.value })
  const yaInscrita = (asigId) => inscripciones.some(
    (i) => i.asignatura.id === asigId && String(i.periodo.id) === form.periodo_id)
  const elegida = asignaturas.find((a) => String(a.id) === form.asignatura_id)

  const inscribir = async (e) => {
    e.preventDefault(); setError(null); setOk('')
    try {
      const r = await api.post('/api/inscripciones', {
        periodo_id: Number(form.periodo_id),
        asignatura_id: Number(form.asignatura_id),
        nota_meta: form.nota_meta === '' ? null : Number(form.nota_meta),
        color: form.color,
      })
      setOk(`${r.asignatura.nombre} inscrita en ${r.periodo.nombre}.`)
      setForm({ ...form, asignatura_id: '', nota_meta: '' })
      cargarInscripciones()
    } catch (err) { setError(err) }
  }

  const quitar = async (i) => {
    if (!window.confirm(`¿Quitar ${i.asignatura.nombre}? Se borran también sus entregas.`)) return
    await api.del(`/api/inscripciones/${i.id}`); cargarInscripciones()
  }

  return (
    <>
      <h1>Mis materias</h1>
      <p className="sub">Inscribe las materias que cursas este período y ponles una nota meta.</p>

      <div className="dos-columnas">
        <form className="tarjeta" onSubmit={inscribir}>
          <h2>Inscribir materia</h2>
          <p className="sub sub--chica">Cada lista se carga según lo elegido en la anterior</p>
          <ErrorServidor error={error} />
          {ok && <div className="aviso aviso--ok">{ok}</div>}

          <Campo paso="1" etiqueta="Período académico">
            <select required value={form.periodo_id} onChange={cambiar('periodo_id')}>
              <option value="">Elegir período…</option>
              {periodos.map((p) => <option key={p.id} value={p.id}>{p.nombre}{p.activo ? ' (actual)' : ''}</option>)}
            </select>
          </Campo>
          <Campo paso="2" etiqueta="Carrera">
            <select required value={form.carrera_id} onChange={cambiar('carrera_id')}>
              <option value="">Elegir carrera…</option>
              {carreras.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
          </Campo>
          <Campo paso="3" etiqueta="Asignatura"
            ayuda={form.carrera_id ? 'Solo aparecen las asignaturas de la carrera elegida.' : 'Primero elige una carrera.'}>
            <select required value={form.asignatura_id} onChange={cambiar('asignatura_id')}
              disabled={!form.carrera_id || cargandoAsig}>
              <option value="">{cargandoAsig ? 'Cargando…' : 'Elegir asignatura…'}</option>
              {asignaturas.map((a) => (
                <option key={a.id} value={a.id} disabled={yaInscrita(a.id)}>
                  {a.codigo} · {a.nombre}{yaInscrita(a.id) ? ' (ya inscrita)' : ''}
                </option>
              ))}
            </select>
          </Campo>
          <div className="fila">
            <Campo etiqueta="Nota meta (opcional)" ayuda={elegida ? `Escala de 0 a ${elegida.escala}` : null}>
              <input type="number" step="0.01" value={form.nota_meta} onChange={cambiar('nota_meta')} placeholder="9,00" />
            </Campo>
            <Campo etiqueta="Color">
              <select value={form.color} onChange={cambiar('color')} style={{ borderLeft: `6px solid ${form.color}` }}>
                {COLORES.map(([v, n]) => <option key={v} value={v}>{n}</option>)}
              </select>
            </Campo>
          </div>
          <div className="acciones"><button className="btn btn--primario" disabled={!form.asignatura_id}>Inscribir</button></div>
        </form>

        <div className="tarjeta">
          <h2>Inscritas</h2>
          {inscripciones.length === 0 && <p className="vacio">Todavía no inscribes materias.</p>}
          <ul className="lista-materias">
            {inscripciones.map((i) => (
              <li key={i.id} style={{ borderLeftColor: i.color }}>
                <div>
                  <b>{i.asignatura.nombre}</b>
                  <span>{i.asignatura.codigo} · {i.periodo.nombre} · {i.asignatura.creditos} créditos
                    {i.nota_meta != null && ` · meta ${i.nota_meta}`}</span>
                </div>
                <div className="celda-acciones">
                  <Link className="btn btn--suave btn--mini" to={`/entregas?materia=${i.id}`}>Entregas</Link>
                  <button className="btn btn--peligro btn--mini" onClick={() => quitar(i)}>Quitar</button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </>
  )
}
