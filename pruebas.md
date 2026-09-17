# Plan de Pruebas Manuales de Endpoints

## Pruebas de Éxito
1. **GET /clientes:** Retorna código `200 OK` y la lista inicial de clientes en formato JSON.
2. **POST /clientes:** Registra un nuevo cliente y retorna código `201 Created`.
3. **GET /citas:** Retorna código `200 OK` con las citas agendadas.

## Casos de Prueba de Error
1. **Error 404 - Recursos no encontrados:**
   * **Petición:** `GET /clientes/999`
   * **Resultado:** `404 Not Found`
   * **Cuerpo de Respuesta:**
     ```json
     {
       "error": {
         "code": "RESOURCE_NOT_FOUND",
         "message": "No existe un cliente con el ID 999",
         "details": []
       }
     }
     ```

2. **Error 409 - Duplicidad de datos:**
   * **Petición:** `POST /clientes` con un email previamente existente.
   * **Resultado:** `409 Conflict`
   * **Cuerpo de Respuesta:**
     ```json
     {
       "error": {
         "code": "EMAIL_ALREADY_EXISTS",
         "message": "El correo ya esta registrado",
         "details": []
       }
     }
     ```