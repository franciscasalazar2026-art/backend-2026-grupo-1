
class ClienteNoEncontrado(Exception):
    pass


class ClienteServicio:

    def __init__(self, repositorio):
        self.repositorio = repositorio

    def listar(self, limite=10, desplazamiento=0):
        clientes, total = self.repositorio.listar(
            limite=limite,
            desplazamiento=desplazamiento,
        )

        return {
            "items": clientes,
            "total": total,
            "pagina": desplazamiento // limite + 1,
            "limite": limite,
            "total_paginas": (
                (total + limite - 1) // limite if total else 1
            ),
        }

    def obtener(self, cliente_id: int):
        cliente = self.repositorio.obtener(cliente_id)

        if cliente is None:
            raise ClienteNoEncontrado()

        return cliente

    def crear(self, datos: dict):
        return self.repositorio.crear(datos)

    def actualizar(self, cliente_id: int, cambios: dict):
        cliente = self.obtener(cliente_id)

        if any(valor is None for valor in cambios.values()):
            raise ValueError("Los campos no pueden ser nulos.")

        return self.repositorio.actualizar(cliente, cambios)

    def eliminar(self, cliente_id: int):
        cliente = self.obtener(cliente_id)
        self.repositorio.eliminar(cliente)
