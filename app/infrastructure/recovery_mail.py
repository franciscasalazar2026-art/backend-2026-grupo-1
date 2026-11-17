"""Buzón local opcional para desarrollo y pruebas."""

import json
import logging
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

logger = logging.getLogger(__name__)


def deliver_recovery_token(email: str, token: str, message_id: str) -> None:
    configured_directory = os.getenv("RECOVERY_MAIL_DIR")
    if not configured_directory:
        return

    directory = Path(configured_directory)
    temporary_path = None
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=directory, delete=False
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(
                {"email": email, "token": token}, temporary_file, ensure_ascii=False
            )
        temporary_path.replace(directory / f"{message_id}.json")
    except OSError:
        logger.error("No se pudo escribir en el buzón local de recuperación.")
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                logger.warning(
                    "No se pudo limpiar un archivo temporal del buzón local."
                )
