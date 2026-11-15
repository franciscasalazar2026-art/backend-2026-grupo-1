MIN_PASSWORD_LENGTH = 12


def validar_politica_contrasena(password: str) -> None:
     # Valida que la contraseña cumpla con el mínimo de 12 caracteres exigido
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres."
        )
