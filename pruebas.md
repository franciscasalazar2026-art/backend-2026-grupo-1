# Plan de Pruebas Manuales de Endpoints

## Pruebas de Éxito

1. **GET /clientes:** Retorna código `200 OK` y la lista inicial de clientes en formato JSON.
2. **POST /clientes:** Registra un nuevo cliente y retorna código `201 Created`.
3. **GET /citas:** Retorna código `200 OK` con las citas agendadas.

### Endpoints de Servicios
4. **GET /servicios:** Retorna código `200 OK` con la lista de servicios.
   - **Respuesta:**
   ```json
   [
     {
       "id": 1,
       "nombre": "Corte de cabello",
       "descripcion": "Corte y peinado básico",
       "precio": 15000.0
     }
   ]
