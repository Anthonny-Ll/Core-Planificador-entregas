// Funciones que llaman a la API de FastAPI. React nunca toca la base de datos directamente.

const CLAVE = 'planificador_sesion'

export function leerSesion() {
  try { return JSON.parse(localStorage.getItem(CLAVE)) } catch { return null }
}
export function guardarSesion(sesion) {
  if (sesion) localStorage.setItem(CLAVE, JSON.stringify(sesion))
  else localStorage.removeItem(CLAVE)
}

// Error con el formato del backend: { mensaje, errores: [...] , status }
export class ErrorApi extends Error {
  constructor(status, mensaje, errores = []) {
    super(mensaje)
    this.status = status
    this.errores = errores
  }
}

function leerError(status, cuerpo) {
  const d = cuerpo?.detail
  if (d && typeof d === 'object' && !Array.isArray(d)) return new ErrorApi(status, d.mensaje, d.errores)
  // 422 de Pydantic (tipo de dato incorrecto, ej. texto donde va un número)
  if (Array.isArray(d)) return new ErrorApi(status, 'Datos con formato incorrecto.',
    d.map((e) => `${e.loc?.slice(1).join('.')}: ${e.msg}`))
  return new ErrorApi(status, d || 'Error al comunicarse con el servidor')
}

async function pedir(metodo, ruta, cuerpo) {
  const sesion = leerSesion()
  const headers = { 'Content-Type': 'application/json' }
  if (sesion?.token) headers.Authorization = `Bearer ${sesion.token}`
  const res = await fetch(ruta, { method: metodo, headers, body: cuerpo ? JSON.stringify(cuerpo) : undefined })
  if (res.status === 401 && sesion) {   // token vencido: volver al login
    guardarSesion(null)
    window.location.href = '/login'
  }
  const datos = res.status === 204 ? null : await res.json().catch(() => null)
  if (!res.ok) throw leerError(res.status, datos)
  return datos
}

export const api = {
  get: (r) => pedir('GET', r),
  post: (r, b) => pedir('POST', r, b),
  put: (r, b) => pedir('PUT', r, b),
  patch: (r, b) => pedir('PATCH', r, b),
  del: (r) => pedir('DELETE', r),
}
