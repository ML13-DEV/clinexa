import logging

import resend

from app.core.config import settings

logger = logging.getLogger(__name__)


def enviar_mail_reset(destinatario: str, nombre: str, link: str) -> None:
    """No propaga errores de Resend: /olvide-password siempre responde
    igual exista o no la cuenta (evitar user enumeration), así que un
    fallo de envío no debe convertirse en un 500 que delate lo contrario."""
    resend.api_key = settings.resend_api_key

    try:
        resend.Emails.send({
            "from": settings.resend_from_email,
            "to": destinatario,
            "subject": "Restablecer tu contraseña - Clinexa",
            "html": f"""
                <p>Hola{f' {nombre}' if nombre else ''},</p>
                <p>Pediste restablecer tu contraseña en Clinexa. Entrá al
                siguiente link para elegir una nueva (válido por
                {settings.reset_password_token_expire_minutes} minutos):</p>
                <p><a href="{link}">{link}</a></p>
                <p>Si no fuiste vos, ignorá este mail.</p>
            """,
        })
    except Exception:
        logger.exception("Fallo el envio de mail de reset a %s", destinatario)
