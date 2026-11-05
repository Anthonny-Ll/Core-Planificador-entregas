import { useEffect, useState } from 'react'
import { api } from '../../api'
import Campo from '../../components/Campo'
import ErrorServidor from '../../components/ErrorServidor'

const VACIA = { carrera_id: '', codigo: '', nombre: '', creditos: 3, escala: 10, pesos: [30, 30, 40] }

export default function Asignaturas() {
  const [carreras, setCarreras] = useState([])
  const [asignaturas, setAsignaturas] = useState([])
  const [filtro, setFiltro] = useState('')
  const [form, setForm] = useState(VACIA)
  const [editando, setEditando] = useState(null) // id de la asignatura que se edita
  const [error, setError] = useState(null)
  const [ok, setOk] = useState('')

  const cargar = () =>
    api.get('/api/admin/asignaturas' + (filtro ? `?carrera_id=${filtro}` : '')).then(setAsignaturas)

  useEffect(() => { api.get('/api/admin/carreras').then(setCarreras) }, [])
  useEffect(() => { cargar() }, [filtro])

  const cambiar = (c) => (e) => setForm({ ...form, [c]: e.target.value })
  const cambiarPeso = (i) => (e) => {
    const pesos = [...form.pesos]; pesos[i] = e.target.value
    setForm({ ...form, pesos })
  }

  // Solo es una AYUDA visual: no bloquea el envío. Quien decide es el backend.
  const suma = form.pesos.reduce((t, p) => t + (Number(p) || 0), 0)
  const sumaOk = Math.abs(suma - 100) < 0.01

  const limpiar = () => { setForm(VACIA); setEditando(null); setError(null) }

  const guardar = async (e) => {
    e.preventDefault()
    setError(null); setOk('')
    const cuerpo = {
      ...form,
      carrera_id: Number(form.carrera_id),
      creditos: Number(form.creditos),
      escala: Number(form.escala),
      pesos: form.pesos.map(Number),
    }
    try {
      const r = editando
        ? await api.put(`/api/admin/asignaturas/${editando}`, cuerpo)
        : await api.post('/api/admin/asignaturas', cuerpo)
      setOk(`Asignatura ${r.codigo} · ${r.nombre} guardada.`)
      limpiar(); cargar()
    } catch (err) { setError(err) }
  }

  const editar = (a) => {
    setEditando(a.id); setOk(''); setError(null)
    setForm({
      carrera_id: a.carrera_id, codigo: a.codigo, nombre: a.nombre, creditos: a.creditos,
      escala: a.escala, pesos: a.progresos.map((p) => p.peso),
    })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const borrar = async (a) => {
    if (!window.confirm(`¿Borrar ${a.codigo} · ${a.nombre}?`)) return
    setError(null); setOk('')
    try { await api.del(`/api/admin/asignaturas/${a.id}`); cargar() } catch (err) { setError(err) }
  }

  return (
    <>
      <h1>{editando ? 'Editar asignatura' : 'Nueva asignatura'}</h1>
      <p className="sub">Catálogo académico · los estudiantes inscriben sus materias desde aquí</p>

      <div className="dos-columnas">
        <form className="tarjeta" onSubmit={guardar}>
          <Campo etiqueta="Carrera" ayuda="Se elige de la lista; no se escribe el identificador de la carrera.">
            <select required value={form.carrera_id} onChange={cambiar('carrera_id')}>
              <option value="">Elegir carrera…</option>
              {carreras.map((c) => <option key={c.id} value={c.id}>{c.nombre} ({c.codigo})</option>)}
            </select>
          </Campo>
          <div className="fila">
            <Campo etiqueta="Código" ayuda="Formato: 4 letras y 4 dígitos">
              <input value={form.codigo} onChange={cambiar('codigo')} placeholder="ISWZ3101" />
            </Campo>
            <Campo etiqueta="Nombre"><input value={form.nombre} onChange={cambiar('nombre')} /></Campo>
          </div>
          <div className="fila">
            <Campo etiqueta="Créditos"><input type="number" value={form.creditos} onChange={cambiar('creditos')} /></Campo>
            <Campo etiqueta="Escala de calificación"><input type="number" step="any" value={form.escala} onChange={cambiar('escala')} /></Campo>
          </div>

          <h3 className="subtitulo">Pesos de los progresos (% de la nota final)</h3>
          <div className="fila fila--3">
            {form.pesos.map((p, i) => (
              <Campo key={i} etiqueta={`Progreso ${i + 1}`}>
                <input type="number" step="any" value={p} onChange={cambiarPeso(i)}
                  className={sumaOk ? '' : 'input--alerta'} />
              </Campo>
            ))}
          </div>
          <p className={'suma ' + (sumaOk ? 'suma--ok' : 'suma--mal')}>
            Suma: {Math.round(suma * 100) / 100} / 100
            {!sumaOk && ' · el servidor no lo va a aceptar'}
          </p>

          <div className="acciones">
            {editando && <button type="button" className="btn btn--suave" onClick={limpiar}>Cancelar</button>}
            <button className="btn btn--primario">Guardar asignatura</button>
          </div>
        </form>

        <div>
          <ErrorServidor error={error && { ...error, message: error.message || 'No se guardó la asignatura.' }} />
          {ok && <div className="aviso aviso--ok">{ok}</div>}
          <div className="tarjeta nota">
            <b>Validaciones en el backend antes de guardar</b>
            <ul>
              <li>Cada peso mayor que 0 y como máximo 100, y los 3 suman exactamente 100 → 422</li>
              <li>Código con formato AAAA9999 y no repetido → 422 / 409</li>
              <li>Créditos entero entre 1 y 10; escala mayor que 0 → 422</li>
              <li>La carrera elegida existe → 422</li>
              <li>Solo un usuario con rol admin puede guardar → 403</li>
            </ul>
            <p>Se pueden comprobar sin el formulario desde <a href="/docs" target="_blank" rel="noreferrer">/docs</a>.</p>
          </div>
        </div>
      </div>

      <div className="tarjeta">
        <div className="cabecera-tabla">
          <h2>Asignaturas registradas</h2>
          <select value={filtro} onChange={(e) => setFiltro(e.target.value)}>
            <option value="">Todas las carreras</option>
            {carreras.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
        </div>
        <div className="tabla-scroll">
          <table>
            <thead><tr><th>Código</th><th>Nombre</th><th>Carrera</th><th>Créditos</th><th>P1 · P2 · P3</th><th></th></tr></thead>
            <tbody>
              {asignaturas.map((a) => (
                <tr key={a.id} className={editando === a.id ? 'fila--activa' : ''}>
                  <td><b>{a.codigo}</b></td>
                  <td>{a.nombre}</td>
                  <td>{a.carrera.nombre}</td>
                  <td>{a.creditos}</td>
                  <td>{a.progresos.map((p) => `${p.peso} %`).join(' · ')}</td>
                  <td className="celda-acciones">
                    <button className="btn btn--suave btn--mini" onClick={() => editar(a)}>Editar</button>
                    <button className="btn btn--peligro btn--mini" onClick={() => borrar(a)}>Borrar</button>
                  </td>
                </tr>
              ))}
              {asignaturas.length === 0 && <tr><td colSpan="6" className="vacio">No hay asignaturas.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
