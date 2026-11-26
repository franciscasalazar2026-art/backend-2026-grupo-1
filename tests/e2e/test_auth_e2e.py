"""Exercise auth and protected business operations over HTTP and real PostgreSQL."""

import json
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx2
import jwt


def _estado(respuesta: httpx2.Response, esperado: int) -> None:
    assert respuesta.status_code == esperado, (
        f"{respuesta.request.method} {respuesta.request.url.path}: "
        f"esperado {esperado}, recibido {respuesta.status_code}"
    )


def _bearer(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _password_segura() -> str:
    return f"Aa1!{secrets.token_urlsafe(24)}"


def _registrar_cliente(http: httpx2.Client) -> dict[str, str]:
    credenciales = {
        "email": f"cliente-{uuid4().hex}@example.com",
        "password": _password_segura(),
    }
    respuesta = http.post(
        "/auth/registro", json={"nombre": "Cliente E2E", **credenciales}
    )
    _estado(respuesta, 201)
    usuario = respuesta.json()
    assert usuario["email"] == credenciales["email"]
    assert usuario["activo"] is True and usuario["rol"] == "cliente"
    assert {"password", "password_hash"}.isdisjoint(usuario)
    return credenciales


def _login(http: httpx2.Client, credenciales: dict[str, str], rol: str) -> dict:
    respuesta = http.post("/auth/login", json=credenciales)
    _estado(respuesta, 200)
    datos = respuesta.json()
    assert datos["usuario"]["email"] == credenciales["email"]
    assert datos["usuario"]["rol"] == rol
    assert datos["token_type"] == "bearer"
    assert datos["access_token"] and datos["refresh_token"]
    assert {"password", "password_hash"}.isdisjoint(datos["usuario"])
    return datos


def _solicitar_token(servidor, email: str) -> tuple[dict, str]:
    archivos_anteriores = set(servidor.buzon.glob("*.json"))
    respuesta = servidor.http.post("/auth/forgot-password", json={"email": email})
    _estado(respuesta, 200)
    datos = respuesta.json()
    assert set(datos) == {"mensaje"}
    assert isinstance(datos["mensaje"], str) and datos["mensaje"].strip()

    archivos_nuevos = set(servidor.buzon.glob("*.json")) - archivos_anteriores
    assert len(archivos_nuevos) == 1
    correo = json.loads(archivos_nuevos.pop().read_text(encoding="utf-8"))
    assert correo["email"] == email
    assert isinstance(correo["token"], str) and correo["token"].count(".") == 2
    return datos, correo["token"]


def test_login_creacion_y_consulta_protegidas_logout_y_refresh_rechazado(
    servidor_e2e,
    preparar_personal,
):
    http = servidor_e2e.http
    personal = preparar_personal("recepcionista")
    sesion = _login(http, personal, "recepcionista")
    headers = _bearer(sesion["access_token"])

    cliente = {
        "nombre": "Cliente creado vía HTTP",
        "email": f"agenda-{uuid4().hex}@example.test",
        "telefono": "+56912345678",
    }
    creado = http.post("/clientes", json=cliente, headers=headers)
    _estado(creado, 201)
    cliente_id = creado.json()["id"]
    consultado = http.get(f"/clientes/{cliente_id}", headers=headers)
    _estado(consultado, 200)
    assert consultado.json() == {"id": cliente_id, **cliente, "activo": True}
    _estado(http.get(f"/clientes/{cliente_id}"), 401)

    renovada = http.post(
        "/auth/refresh", json={"refresh_token": sesion["refresh_token"]}
    )
    _estado(renovada, 200)
    refresh = renovada.json()["refresh_token"]
    assert refresh != sesion["refresh_token"]

    _estado(http.post("/auth/logout", json={"refresh_token": refresh}), 200)
    _estado(http.post("/auth/refresh", json={"refresh_token": refresh}), 401)


def test_registro_con_rol_admin_solicitado_conserva_cliente_y_cierra_sesion(
    servidor_e2e, preparar_personal
):
    http = servidor_e2e.http
    personal = _login(http, preparar_personal("recepcionista"), "recepcionista")
    recurso = {
        "nombre": "Cliente consultado por cuenta registrada",
        "email": f"recurso-{uuid4().hex}@example.test",
        "telefono": "+56912345678",
    }
    creado = http.post(
        "/clientes", json=recurso, headers=_bearer(personal["access_token"])
    )
    _estado(creado, 201)
    recurso_id = creado.json()["id"]

    credenciales = {
        "email": f"registro-{uuid4().hex}@example.com",
        "password": _password_segura(),
    }
    registro = http.post(
        "/auth/registro",
        json={"nombre": "Registro con rol solicitado", "rol": "admin", **credenciales},
    )
    _estado(registro, 201)
    usuario = registro.json()
    assert usuario["email"] == credenciales["email"]
    assert usuario["rol"] == "cliente" and usuario["activo"] is True
    assert {"password", "password_hash"}.isdisjoint(usuario)

    sesion = _login(http, credenciales, "cliente")
    assert sesion["usuario"]["id"] == usuario["id"]
    headers = _bearer(sesion["access_token"])
    consultado = http.get(f"/clientes/{recurso_id}", headers=headers)
    _estado(consultado, 200)
    assert consultado.json() == {"id": recurso_id, **recurso, "activo": True}

    intento_escritura = {
        **recurso,
        "email": f"rechazado-{uuid4().hex}@example.test",
    }
    _estado(http.post("/clientes", json=intento_escritura, headers=headers), 403)
    _estado(
        http.post("/auth/logout", json={"refresh_token": sesion["refresh_token"]}),
        200,
    )
    _estado(
        http.post("/auth/refresh", json={"refresh_token": sesion["refresh_token"]}),
        401,
    )


def test_recuperacion_generica_de_un_uso_y_revocacion_de_sesiones(servidor_e2e):
    http = servidor_e2e.http
    cliente = _registrar_cliente(http)
    sesion_anterior = _login(http, cliente, "cliente")
    segunda_sesion = _login(http, cliente, "cliente")
    assert segunda_sesion["refresh_token"] != sesion_anterior["refresh_token"]
    acceso_anterior = _bearer(sesion_anterior["access_token"])
    _estado(http.get("/auth/me", headers=acceso_anterior), 200)
    _estado(http.get("/auth/me", headers=_bearer(segunda_sesion["access_token"])), 200)
    otra_cuenta = _registrar_cliente(http)
    sesion_otra_cuenta = _login(http, otra_cuenta, "cliente")
    otro_usuario_id = sesion_otra_cuenta["usuario"]["id"]
    assert otro_usuario_id != sesion_anterior["usuario"]["id"]

    respuesta_conocida, token = _solicitar_token(servidor_e2e, cliente["email"])
    archivos_anteriores = set(servidor_e2e.buzon.iterdir())
    desconocido = http.post(
        "/auth/forgot-password",
        json={
            "email": f"desconocido-{uuid4().hex}@example.com",
        },
    )
    _estado(desconocido, 200)
    assert desconocido.json() == respuesta_conocida
    assert set(servidor_e2e.buzon.iterdir()) == archivos_anteriores
    _, token_pendiente = _solicitar_token(servidor_e2e, cliente["email"])
    assert token_pendiente != token

    password_nueva = _password_segura()

    def restablecer(token_recuperacion: str, password: str) -> httpx2.Response:
        return http.post(
            "/auth/reset-password",
            json={
                "token": token_recuperacion,
                "nueva_password": password,
            },
        )

    cabecera, payload, firma = token.split(".")
    inicio_alterado = "A" if payload[0] != "A" else "B"
    token_manipulado = f"{cabecera}.{inicio_alterado}{payload[1:]}.{firma}"
    _estado(restablecer(token_manipulado, password_nueva), 401)
    _estado(restablecer(sesion_anterior["access_token"], password_nueva), 401)

    claims = jwt.decode(token, servidor_e2e.jwt_secret, algorithms=["HS256"])
    claims["exp"] = datetime.now(timezone.utc) - timedelta(minutes=1)
    token_vencido = jwt.encode(claims, servidor_e2e.jwt_secret, algorithm="HS256")
    _estado(restablecer(token_vencido, password_nueva), 401)
    _estado(http.get("/auth/me", headers=acceso_anterior), 200)

    _estado(
        http.post(
            "/auth/reset-password",
            json={
                "token": token,
                "nueva_password": password_nueva,
                "usuario_id": otro_usuario_id,
            },
        ),
        200,
    )
    otro_password = _password_segura()
    _estado(restablecer(token, otro_password), 400)
    _estado(restablecer(token_pendiente, otro_password), 401)
    for sesion in (sesion_anterior, segunda_sesion):
        _estado(http.get("/auth/me", headers=_bearer(sesion["access_token"])), 401)
        _estado(
            http.post("/auth/refresh", json={"refresh_token": sesion["refresh_token"]}),
            401,
        )
    _estado(http.post("/auth/login", json=cliente), 401)
    _estado(http.post("/auth/login", json={**cliente, "password": otro_password}), 401)

    sesion_nueva = _login(http, {**cliente, "password": password_nueva}, "cliente")
    assert sesion_nueva["usuario"]["id"] == sesion_anterior["usuario"]["id"]
    _estado(http.get("/auth/me", headers=_bearer(sesion_nueva["access_token"])), 200)
    _estado(
        http.get("/auth/me", headers=_bearer(sesion_otra_cuenta["access_token"])),
        200,
    )
    sesion_otra_cuenta_vigente = _login(http, otra_cuenta, "cliente")
    assert sesion_otra_cuenta_vigente["usuario"]["id"] == otro_usuario_id


def test_mismo_servicio_sin_autenticacion_cliente_y_admin(
    servidor_e2e, preparar_personal
):
    http = servidor_e2e.http
    cliente = _login(http, _registrar_cliente(http), "cliente")
    admin = _login(http, preparar_personal("admin"), "admin")
    datos = {
        "nombre": f"Servicio E2E {uuid4().hex}",
        "descripcion": "Creado por un administrador",
        "duracion_minutos": 35,
        "precio": "12000.00",
        "activo": True,
    }

    anonimo = http.post("/servicios", json=datos)
    _estado(anonimo, 401)
    assert anonimo.headers["WWW-Authenticate"] == "Bearer"
    assert anonimo.json()["error"] == "HTTP_401"

    cliente_sin_permiso = http.post(
        "/servicios",
        json=datos,
        headers=_bearer(cliente["access_token"]),
    )
    _estado(cliente_sin_permiso, 403)
    assert cliente_sin_permiso.json()["error"] == "HTTP_403"
    listado = http.get("/servicios", params={"buscar": datos["nombre"]})
    _estado(listado, 200)
    assert listado.json()["total"] == 0 and listado.json()["items"] == []

    permitido = http.post(
        "/servicios", json=datos, headers=_bearer(admin["access_token"])
    )
    _estado(permitido, 201)
    servicio_id = permitido.json()["id"]
    consultado = http.get(f"/servicios/{servicio_id}")
    _estado(consultado, 200)
    assert consultado.json() == {"id": servicio_id, **datos}
