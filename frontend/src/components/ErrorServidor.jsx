// Muestra la respuesta de error del backend tal como llegó (código HTTP + motivos).
export default function ErrorServidor({ error }) {
  if (!error) return null
  return (
    <div className="aviso aviso--error" role="alert">
      <b>{error.message}</b>
      {error.status && <span className="aviso__codigo">Respuesta del servidor ({error.status})</span>}
      {error.errores?.length > 0 && <ul>{error.errores.map((e) => <li key={e}>{e}</li>)}</ul>}
    </div>
  )
}
