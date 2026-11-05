import { createContext, useContext, useState } from 'react'
import { api, guardarSesion, leerSesion } from './api'

// Guarda quién inició sesión para que cualquier pantalla lo pueda consultar.
const Contexto = createContext(null)

export function ProveedorSesion({ children }) {
  const [sesion, setSesion] = useState(leerSesion)

  const entrar = async (ruta, datos) => {
    const r = await api.post(ruta, datos)
    guardarSesion(r)
    setSesion(r)
    return r.usuario
  }
  const salir = () => { guardarSesion(null); setSesion(null) }

  return (
    <Contexto.Provider value={{ usuario: sesion?.usuario, entrar, salir }}>
      {children}
    </Contexto.Provider>
  )
}

export const useSesion = () => useContext(Contexto)
