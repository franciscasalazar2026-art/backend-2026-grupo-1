# API REST - Sistema de Gestión de Citas

## Integrantes
* Francisca Alvarado
* Camila Fuentes
* Emily Jara 
* Francisca Salazar
* Isidora Valverde
## Requisitos e Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/franciscasalazar2026-art/backend-2026-grupo-1.git](https://github.com/franciscasalazar2026-art/backend-2026-grupo-1.git)
   cd backend-2026-grupo-1
## Contrato de Endpoints REST

### Clientes
| Método | Endpoint | Descripción | Código Éxito |
| :--- | :--- | :--- | :--- |
| `GET` | `/clientes` | Lista clientes con paginación | `200 OK` |
| `POST` | `/clientes` | Registra un nuevo cliente | `201 Created` |
| `GET` | `/clientes/{id}` | Obtiene detalle de un cliente | `200 OK` |
| `PUT` | `/clientes/{id}` | Actualiza datos de un cliente | `200 OK` |
| `DELETE` | `/clientes/{id}` | Elimina un cliente | `204 No Content` |

### Citas
| Método | Endpoint | Descripción | Código Éxito |
| :--- | :--- | :--- | :--- |
| `GET` | `/citas` | Lista citas con filtros | `200 OK` |
| `POST` | `/citas` | Agenda una nueva cita | `201 Created` |
| `GET` | `/citas/{id}` | Obtiene detalle de una cita | `200 OK` |
| `PUT` | `/citas/{id}` | Actualiza estado/fecha de cita | `200 OK` |
| `DELETE` | `/citas/{id}` | Cancela/Elimina una cita | `204 No Content` |