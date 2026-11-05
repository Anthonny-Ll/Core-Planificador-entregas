// Etiqueta + control + texto de ayuda, para que todos los formularios se vean iguales.
export default function Campo({ etiqueta, paso, ayuda, children }) {
  return (
    <label className="campo">
      <span className="campo__etiqueta">
        {paso && <span className="campo__paso">{paso}</span>}{etiqueta}
      </span>
      {children}
      {ayuda && <span className="campo__ayuda">{ayuda}</span>}
    </label>
  )
}
