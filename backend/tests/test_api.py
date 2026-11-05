"""Pruebas de la API completa con una BD temporal."""

NUEVA = {"carrera_id": 1, "codigo": "ISWZ4100", "nombre": "Proyecto Integrador", "creditos": 3, "escala": 10}


def test_sin_token_401_y_estudiante_no_es_admin_403(cliente, estudiante):
    assert cliente.get("/api/admin/carreras").status_code == 401
    assert cliente.get("/api/admin/carreras", headers=estudiante).status_code == 403


def test_admin_crea_asignatura_con_pesos_validos(cliente, admin):
    r = cliente.post("/api/admin/asignaturas", headers=admin, json={**NUEVA, "pesos": [30, 30, 40]})
    assert r.status_code == 201, r.text
    assert [p["peso"] for p in r.json()["progresos"]] == [30, 30, 40]


def test_backend_rechaza_pesos_que_no_suman_100_y_no_graba(cliente, admin):
    """Aunque alguien se salte el formulario de React, el backend no graba."""
    antes = len(cliente.get("/api/admin/asignaturas", headers=admin).json())
    r = cliente.post("/api/admin/asignaturas", headers=admin, json={**NUEVA, "pesos": [30, 40, 40]})
    assert r.status_code == 422
    assert "Suma actual: 110" in r.json()["detail"]["errores"][0]
    assert len(cliente.get("/api/admin/asignaturas", headers=admin).json()) == antes


def test_backend_rechaza_carrera_inexistente(cliente, admin):
    r = cliente.post("/api/admin/asignaturas", headers=admin, json={**NUEVA, "carrera_id": 999, "pesos": [30, 30, 40]})
    assert r.status_code == 422
    assert "La carrera elegida no existe." in r.json()["detail"]["errores"]


def test_codigo_repetido_409(cliente, admin):
    r = cliente.post("/api/admin/asignaturas", headers=admin, json={**NUEVA, "codigo": "iswz3101", "pesos": [30, 30, 40]})
    assert r.status_code == 409


def test_editar_pesos_tambien_se_valida(cliente, admin):
    asig = cliente.get("/api/admin/asignaturas", headers=admin).json()[0]
    cuerpo = {k: asig[k] for k in ("carrera_id", "codigo", "nombre", "creditos", "escala")}
    r = cliente.put(f"/api/admin/asignaturas/{asig['id']}", headers=admin, json={**cuerpo, "pesos": [10, 10, 10]})
    assert r.status_code == 422


def test_cascada_carrera_a_asignaturas(cliente, estudiante):
    carreras = cliente.get("/api/catalogo/carreras", headers=estudiante).json()
    isw = next(c for c in carreras if c["codigo"] == "ISW")
    asignaturas = cliente.get(f"/api/catalogo/carreras/{isw['id']}/asignaturas", headers=estudiante).json()
    assert asignaturas and all(a["carrera_id"] == isw["id"] for a in asignaturas)


def _inscribir(cliente, estudiante, codigo="ISWZ3101"):
    periodo = cliente.get("/api/catalogo/periodos", headers=estudiante).json()[0]
    carreras = cliente.get("/api/catalogo/carreras", headers=estudiante).json()
    for c in carreras:
        for a in cliente.get(f"/api/catalogo/carreras/{c['id']}/asignaturas", headers=estudiante).json():
            if a["codigo"] == codigo:
                r = cliente.post("/api/inscripciones", headers=estudiante,
                                 json={"periodo_id": periodo["id"], "asignatura_id": a["id"], "nota_meta": 9})
                assert r.status_code == 201, r.text
                return r.json()


def test_inscripcion_duplicada_409(cliente, estudiante):
    insc = _inscribir(cliente, estudiante)
    r = cliente.post("/api/inscripciones", headers=estudiante, json={
        "periodo_id": insc["periodo"]["id"], "asignatura_id": insc["asignatura"]["id"]})
    assert r.status_code == 409


def test_cascada_materia_a_progresos_y_peso_cargado(cliente, estudiante):
    insc = _inscribir(cliente, estudiante)
    progresos = cliente.get(f"/api/inscripciones/{insc['id']}/progresos", headers=estudiante).json()
    assert [p["numero"] for p in progresos] == [1, 2, 3]
    p2 = progresos[1]
    base = {"inscripcion_id": insc["id"], "progreso_id": p2["id"], "tipo": "proyecto", "horas_estimadas": 6}
    r = cliente.post("/api/entregas", headers=estudiante, json={**base, "titulo": "Documento de Análisis", "peso": 60})
    assert r.status_code == 201
    assert r.json()["peso_final"] == 18  # 60 % del P2, que vale 30 %
    r = cliente.post("/api/entregas", headers=estudiante, json={**base, "titulo": "Otro", "peso": 50})
    assert r.status_code == 422  # 60 + 50 > 100
    progresos = cliente.get(f"/api/inscripciones/{insc['id']}/progresos", headers=estudiante).json()
    assert progresos[1]["cargado"] == 60


def test_progreso_de_otra_materia_se_rechaza(cliente, estudiante):
    web = _inscribir(cliente, estudiante, "ISWZ3101")
    otra = _inscribir(cliente, estudiante, "ISWZ2105")
    prog_otra = cliente.get(f"/api/inscripciones/{otra['id']}/progresos", headers=estudiante).json()[0]
    r = cliente.post("/api/entregas", headers=estudiante, json={
        "inscripcion_id": web["id"], "progreso_id": prog_otra["id"], "titulo": "Trampa",
        "tipo": "tarea", "peso": 10, "horas_estimadas": 1})
    assert r.status_code == 422


def test_registro_no_puede_crear_admin(cliente):
    r = cliente.post("/api/auth/registro", json={
        "nombre": "Nuevo", "correo": "nuevo@udla.edu.ec", "password": "Clave1234", "rol": "admin"})
    assert r.status_code == 201
    assert r.json()["usuario"]["rol"] == "estudiante"


def test_admin_desactiva_usuario_y_ya_no_entra(cliente, admin):
    usuarios = cliente.get("/api/admin/usuarios", headers=admin).json()
    est = next(u for u in usuarios if u["rol"] == "estudiante")
    assert cliente.patch(f"/api/admin/usuarios/{est['id']}", headers=admin, json={"activo": False}).status_code == 200
    r = cliente.post("/api/auth/login", json={"correo": est["correo"], "password": "Estudiante123"})
    assert r.status_code == 403
