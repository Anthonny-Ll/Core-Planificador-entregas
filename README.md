# Planificador de entregas académicas

Proyecto de **Ingeniería Web (UDLA)** hecho con **FastAPI + React + SQLite**.

El estudiante inscribe sus materias del período y carga las entregas del sílabo de cada una (tareas, proyectos y exámenes), con el peso que tienen dentro de cada progreso. El administrador mantiene el catálogo académico: carreras, asignaturas con los pesos de sus 3 progresos, períodos y usuarios.

> Esta versión cubre el **Administrador con validación en el backend** y los **formularios con dropdowns en cascada**. El plan de estudio, las notas y la sincronización con Brightspace son las siguientes etapas del proyecto.

**Demo en línea:** `https://<tu-servicio>.onrender.com` *(reemplazar después del despliegue)*

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@udla.edu.ec` | la que se define en `ADMIN_PASSWORD` (en local: `Admin123*`) |
| Estudiante de prueba | `estudiante@udla.edu.ec` | `Estudiante123` |

También se puede crear una cuenta nueva de estudiante desde **Regístrate**.

---

## Requisitos de la materia y dónde se cumplen

### 1. Validación en el backend de un dato sensible del core

**Dato sensible: los pesos de los 3 progresos de cada asignatura.** Con ellos se calcula cuánto vale cada entrega en la nota final, la nota que le falta al estudiante para llegar a su meta y la prioridad de cada tarea en el plan. Si se grabaran pesos que no suman 100, los cálculos de **todos** los estudiantes inscritos en esa asignatura saldrían mal.

Por eso la regla no se confía al JavaScript: el formulario solo muestra la suma como ayuda (no bloquea el envío) y quien decide es el backend, **antes de grabar**:

| Regla (al crear **y** al editar una asignatura) | Respuesta si falla |
|---|---|
| Hay exactamente 3 progresos; cada peso es > 0 y ≤ 100 | `422` |
| **Los 3 pesos suman exactamente 100** | `422` con la suma recibida |
| Código con formato `AAAA9999` (ej. `ISWZ3101`) | `422` |
| Código no repetido | `409` |
| Créditos entre 1 y 10; escala > 0 | `422` |
| La carrera elegida existe | `422` |
| Quien guarda tiene rol **admin** | `403` (sin sesión: `401`) |

- Reglas: [`backend/app/services/validaciones.py`](backend/app/services/validaciones.py) → `validar_pesos_progresos()` y `validar_asignatura()` (funciones puras).
- Dónde se aplican antes del `commit`: [`backend/app/controllers/admin_controller.py`](backend/app/controllers/admin_controller.py) → `_guardar_asignatura()`.
- Control de rol: [`backend/app/core/security.py`](backend/app/core/security.py) → `solo_admin()`.

Lo mismo pasa con las entregas del estudiante: la suma de los pesos de las entregas de un progreso no puede pasar de 100, y el progreso tiene que ser de la misma asignatura que la materia elegida (`422`).

**Cómo comprobarlo sin el formulario** (saltándose el JavaScript):

1. Abrir `/docs` (Swagger), ejecutar `POST /api/auth/login` con el admin y copiar el `token`.
2. Botón **Authorize** → pegar el token.
3. `POST /api/admin/asignaturas` con:
   ```json
   { "carrera_id": 1, "codigo": "ISWZ4100", "nombre": "Proyecto Integrador",
     "creditos": 3, "escala": 10, "pesos": [30, 40, 40] }
   ```
4. Respuesta `422` y no se grabó nada:
   ```json
   { "detail": { "mensaje": "No se guardó la asignatura.",
                 "errores": ["Los pesos de los progresos deben sumar 100. Suma actual: 110."] } }
   ```

Con `curl`:

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login -H "Content-Type: application/json" \
  -d '{"correo":"admin@udla.edu.ec","password":"Admin123*"}' | python -c "import sys,json;print(json.load(sys.stdin)['token'])")

curl -i -X POST http://127.0.0.1:8000/api/admin/asignaturas \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"carrera_id":1,"codigo":"ISWZ4100","nombre":"Proyecto Integrador","creditos":3,"escala":10,"pesos":[30,40,40]}'
```

### 2. Referencias a otras tablas con dropdowns (en cascada)

Ningún formulario pide escribir una clave foránea:

| Formulario | Cascada | Endpoint que llena la lista dependiente |
|---|---|---|
| **Inscribir materia** (estudiante) | Período → **Carrera → Asignatura** (solo las de esa carrera) | `GET /api/catalogo/carreras/{carrera_id}/asignaturas` |
| **Nueva entrega** (estudiante) | **Materia inscrita → Progreso** (solo los 3 de esa asignatura, con cuánto peso ya está cargado) | `GET /api/inscripciones/{id}/progresos` |
| **Nueva asignatura** (admin) | Carrera en dropdown | `GET /api/admin/carreras` |

La lista dependiente está deshabilitada hasta elegir la anterior, se vacía cuando la anterior cambia y se vuelve a pedir al backend. Además el backend comprueba que lo recibido sea coherente (que la asignatura y el período existan, que el progreso sea de esa materia), así que tampoco se puede engañar enviando ids a mano.

- [`frontend/src/pages/estudiante/Materias.jsx`](frontend/src/pages/estudiante/Materias.jsx)
- [`frontend/src/pages/estudiante/Entregas.jsx`](frontend/src/pages/estudiante/Entregas.jsx)

### 3. Versionado en Git y despliegue

Repositorio con `.gitignore` (sin base de datos, `node_modules`, `dist` ni secretos) y despliegue en Render con [`render.yaml`](render.yaml). Pasos más abajo.

---

## Modelo de datos (SQLite)

```
carreras (id, codigo U, nombre)
   └─< asignaturas (id, carrera_id FK, codigo U, nombre, creditos, escala)
          └─< progresos (id, asignatura_id FK, numero 1..3, peso)      ← suman 100
periodos (id, nombre U, fecha_inicio, fecha_fin, activo)
usuarios (id, nombre, correo U, password_hash, rol, activo, creado_en)

inscripciones (id, usuario_id FK, asignatura_id FK, periodo_id FK, color, nota_meta)
   │   (usuario, asignatura, periodo) es único
   └─< entregas (id, inscripcion_id FK, progreso_id FK, titulo, tipo, peso,
                 horas_estimadas, fecha_estimada, estado)
```

`peso_final` de una entrega (lo que vale en la nota final) = `peso × peso del progreso / 100`. Ejemplo: 60 % del Progreso 2, que vale 30 % → **18 %** de la nota final.

## Tecnologías

- **Backend:** FastAPI, SQLAlchemy 2, SQLite, PyJWT. Contraseñas con PBKDF2-SHA256 (con sal, de la librería estándar). Organizado en MVC: `models`, `controllers`, `schemas` y `services`.
- **Frontend:** React 18 + Vite + React Router. CSS con nombres BEM y media queries (funciona en celular).
- **Pruebas:** pytest (validaciones y API completa con una BD temporal).

## Estructura

```
backend/
  app/
    main.py                     arranque, CORS, rutas y servir el build de React
    core/config.py              variables de entorno
    core/database.py            conexión SQLite (claves foráneas activadas)
    core/security.py            hash de contraseñas, JWT, solo_admin / solo_estudiante
    models/                     catalogo.py, usuario.py, estudiante.py
    schemas.py                  forma del JSON (tipos)
    services/validaciones.py    reglas de negocio (funciones puras)
    controllers/                auth, admin y estudiante
    seed.py                     admin, catálogo de ejemplo y estudiante de prueba
  tests/                        test_validaciones.py, test_api.py
  requirements.txt
frontend/
  src/
    api.js                      fetch con token y lectura de errores del backend
    sesion.jsx                  quién inició sesión
    App.jsx                     rutas protegidas por rol
    pages/                      Login, Registro, admin/*, estudiante/*
    components/                 Layout, Campo, ErrorServidor
render.yaml                     despliegue en Render
```

## API

| Método y ruta | Rol | Qué hace |
|---|---|---|
| `POST /api/auth/login` · `POST /api/auth/registro` · `GET /api/auth/yo` | — | Sesión (el registro siempre crea estudiantes) |
| `GET/POST /api/admin/carreras`, `PUT/DELETE /api/admin/carreras/{id}` | admin | CRUD; `409` al borrar con asignaturas |
| `GET/POST /api/admin/asignaturas`, `PUT/DELETE /api/admin/asignaturas/{id}` | admin | CRUD con validación de pesos; `409` al borrar con inscritos |
| `GET/POST /api/admin/periodos`, `PUT/DELETE /api/admin/periodos/{id}` | admin | CRUD; un solo período activo |
| `GET /api/admin/usuarios`, `PATCH /api/admin/usuarios/{id}` | admin | Activar o desactivar cuentas |
| `GET /api/catalogo/periodos`, `/carreras`, `/carreras/{id}/asignaturas` | con sesión | Fuentes de los dropdowns |
| `GET/POST /api/inscripciones`, `DELETE /api/inscripciones/{id}` | estudiante | Inscribir materias |
| `GET /api/inscripciones/{id}/progresos` | estudiante | Progresos de la materia con peso cargado |
| `GET/POST /api/entregas`, `DELETE /api/entregas/{id}` | estudiante | Entregas del sílabo |

Documentación interactiva en `/docs`.

## Ejecutar en local

Necesitas Python 3.11 o superior y Node 18 o superior.

**Terminal 1 — backend**

```bash
cd backend
python -m venv venv
venv\Scripts\activate            # Windows  (en Mac/Linux: source venv/bin/activate)
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

La primera vez crea `backend/planificador.db` con el administrador, 3 carreras, 8 asignaturas, 2 períodos y el estudiante de prueba. Para empezar de cero, borra ese archivo.

**Terminal 2 — frontend**

```bash
cd frontend
npm install
npm run dev
```

Abrir http://localhost:5173 (las llamadas a `/api` se reenvían al puerto 8000).

**Pruebas**

```bash
cd backend
pytest -v
```

## Despliegue en Render

1. Subir el repositorio a GitHub.
2. En Render: **New → Blueprint** y elegir el repositorio. Render lee `render.yaml`.
3. Cuando lo pida, escribir el valor de `ADMIN_PASSWORD` (la contraseña del administrador). `SECRET_KEY` la genera Render.
4. Esperar el build (compila React y luego instala el backend). Un solo servicio sirve la página y la API.
5. Copiar la URL del servicio en la parte de arriba de este README.

> En el plan gratuito de Render el disco no es permanente: al reiniciarse el servicio, la base SQLite vuelve a crearse con los datos iniciales. Para la demo no es un problema; para datos reales habría que usar PostgreSQL (basta con cambiar `DATABASE_URL`).

## Seguridad

- Las contraseñas se guardan con hash PBKDF2-SHA256 y sal aleatoria, nunca en texto plano.
- El rol se comprueba en **cada** ruta del backend; ocultar menús en React es solo comodidad visual.
- El registro público no permite elegir el rol: siempre crea estudiantes.
- Un estudiante solo ve y modifica sus propias materias y entregas (las de otros responden `404`).
- `SECRET_KEY` y `ADMIN_PASSWORD` vienen de variables de entorno, no del código.

## Autor

Anthonny Llanos · Ingeniería de Software, UDLA · [github.com/Anthonny-Ll](https://github.com/Anthonny-Ll)
