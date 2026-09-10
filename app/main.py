from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from app.schemas import Cliente, ClienteCreate, ClienteUpdate, Cita, CitaCreate, CitaUpdate
from app.models import EstadoCita
from app.database import db_clientes, db_citas

app = FastAPI(
    title="API REST - Sistema de Gestión de Citas",
    description="API para la gestión de clientes y agendamiento de citas.",
    version="1.0.0"
)

# --- ENDPOINTS CLIENTES ---

@app.get("/clientes", response_model=List[Cliente], status_code=status.HTTP_200_OK, tags=["Clientes"])
def listar_clientes(
    limit: int = Query(10, ge=1, le=100, description="Límite de registros a retornar"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir")
):
    return db_clientes[offset : offset + limit]

@app.post("/clientes", response_model=Cliente, status_code=status.HTTP_201_CREATED, tags=["Clientes"])
def crear_cliente(cliente: ClienteCreate):
    for c in db_clientes:
        if c.email == cliente.email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo ya está registrado")
    
    nuevo_id = max([c.id for c in db_clientes], default=0) + 1
    nuevo_cliente = Cliente(id=nuevo_id, **cliente.model_dump())
    db_clientes.append(nuevo_cliente)
    return nuevo_cliente

@app.get("/clientes/{cliente_id}", response_model=Cliente, status_code=status.HTTP_200_OK, tags=["Clientes"])
def obtener_cliente(cliente_id: int):
    for c in db_clientes:
        if c.id == cliente_id:
            return c
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")

@app.put("/clientes/{cliente_id}", response_model=Cliente, status_code=status.HTTP_200_OK, tags=["Clientes"])
def actualizar_cliente(cliente_id: int, cliente_data: ClienteUpdate):
    for idx, c in enumerate(db_clientes):
        if c.id == cliente_id:
            datos_actualizados = c.model_dump()
            actualizacion = cliente_data.model_dump(exclude_unset=True)
            datos_actualizados.update(actualizacion)
            
            cliente_modificado = Cliente(**datos_actualizados)
            db_clientes[idx] = cliente_modificado
            return cliente_modificado
            
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")

@app.delete("/clientes/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Clientes"])
def eliminar_cliente(cliente_id: int):
    for idx, c in enumerate(db_clientes):
        if c.id == cliente_id:
            db_clientes.pop(idx)
            return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")

# --- ENDPOINTS CITAS ---

@app.get("/citas", response_model=List[Cita], status_code=status.HTTP_200_OK, tags=["Citas"])
def listar_citas(
    estado: Optional[EstadoCita] = Query(None, description="Filtrar citas por estado"),
    ordenar_fecha: Optional[str] = Query("asc", pattern="^(asc|desc)$", description="Orden por fecha: asc o desc"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    resultado = db_citas
    if estado:
        resultado = [c for c in resultado if c.estado == estado]
    
    reverse = (ordenar_fecha == "desc")
    resultado = sorted(resultado, key=lambda x: x.fecha_hora, reverse=reverse)
    
    return resultado[offset : offset + limit]

@app.post("/citas", response_model=Cita, status_code=status.HTTP_201_CREATED, tags=["Citas"])
def crear_cita(cita: CitaCreate):
    if not any(c.id == cita.cliente_id for c in db_clientes):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El ID del cliente no existe")
    
    nuevo_id = max([c.id for c in db_citas], default=0) + 1
    nueva_cita = Cita(id=nuevo_id, **cita.model_dump())
    db_citas.append(nueva_cita)
    return nueva_cita

@app.get("/citas/{cita_id}", response_model=Cita, status_code=status.HTTP_200_OK, tags=["Citas"])
def obtener_cita(cita_id: int):
    for c in db_citas:
        if c.id == cita_id:
            return c
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada")

@app.put("/citas/{cita_id}", response_model=Cita, status_code=status.HTTP_200_OK, tags=["Citas"])
def actualizar_cita(cita_id: int, cita_data: CitaUpdate):
    for idx, c in enumerate(db_citas):
        if c.id == cita_id:
            datos_actualizados = c.model_dump()
            actualizacion = cita_data.model_dump(exclude_unset=True)
            datos_actualizados.update(actualizacion)
            
            cita_modificada = Cita(**datos_actualizados)
            db_citas[idx] = cita_modificada
            return cita_modificada
            
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada")

@app.delete("/citas/{cita_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Citas"])
def eliminar_cita(cita_id: int):
    for idx, c in enumerate(db_citas):
        if c.id == cita_id:
            db_citas.pop(idx)
            return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada")