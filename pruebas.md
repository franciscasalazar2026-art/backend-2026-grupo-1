# Plan de Pruebas Manuales de Endpoints

Este documento contiene las pruebas manuales realizadas para verificar el correcto funcionamiento de los endpoints de la API REST (Clientes, Citas y Servicios), incluyendo los casos de éxito y el manejo centralizado de errores.

---

## 1. Pruebas de Éxito

### Endpoints de Clientes
* **GET /clientes:** Retorna código `200 OK` y la lista de clientes paginada.
* **POST /clientes:** Registra un nuevo cliente y retorna código `201 Created`.
* **GET /clientes/{id}:** Obtiene el detalle de un cliente por su ID (`200 OK`).

### Endpoints de Citas
* **GET /citas:** Retorna código `200 OK` con las citas agendadas.
* **POST /citas:** Crea una nueva cita asociada a un cliente (`201 Created`).

### Endpoints de Servicios
* **GET /servicios:** Retorna código `200 OK` con la lista de servicios disponibles.
  * **Respuesta Esperada:**
  ```json
  [
    {
      "id": 1,
      "nombre": "Corte de cabello",
      "descripcion": "Corte y peinado básico",
      "precio": 15000.0
    }
  ]
