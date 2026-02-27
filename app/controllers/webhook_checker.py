# controllers/webhook_checker.py
from fastapi import HTTPException, Request, Response
import hmac
import hashlib

# importamos la instancia, no la clase: settings = Settings()
# Es el patrón Singleton una sola instancia para toda la app.
from app.config.settings import settings


class WebhookChecker:
    """
    Clase responsable de la verificación de seguridad de los webhooks de Meta.

    Responsabilidades:
    - Validar el 'hub challenge' durante la configuración del webhook.
    - Verificar la firma criptográfica (X-Hub-Signature-256) de cada petición entrante.
    """

    def __init__(self):
        """Inicializa con los secretos de configuración necesarios para la validación."""
        self.INSTAGRAM_VERIFY_TOKEN = settings.INSTAGRAM_VERIFY_TOKEN
        self.INSTAGRAM_APP_SECRET = settings.INSTAGRAM_APP_SECRET

    def verify(
        self, hub_mode: str, hub_verify_token: str, hub_challenge: str
    ) -> Response:
        """
        Verifica el challenge inicial enviado por Meta (GET request).

        Cuando se configura un webhook, Meta envía una petición con:
        - hub.mode: Debe ser "subscribe".
        - hub.verify_token: Debe coincidir con nuestro token secreto.
        - hub.challenge: Un string aleatorio que debemos devolver.

        Args:
            hub_mode (str): El modo de la suscripción.
            hub_verify_token (str): El token de verificación enviado por Meta.
            hub_challenge (str): El reto que se espera de vuelta.

        Returns:
            Response: Respuesta HTTP 200 con el challenge si la verificación pasa.

        Raises:
            HTTPException (403): Si el token es inválido o el modo no es correcto.
        """
        if hub_mode == "subscribe" and hub_verify_token == self.INSTAGRAM_VERIFY_TOKEN:
            return Response(content=hub_challenge, status_code=200)

        raise HTTPException(status_code=403, detail="Token inválido")

    async def verify_signature(self, request: Request) -> bool:
        """
        Orquesta el proceso completo de verificación de firma X-Hub-Signature-256 (POST request).

        Pasos:
        1. Obtiene el header de firma y el body crudo.
        2. Extrae el algoritmo y el hash recibido.
        3. Genera un hash HMAC SHA256 local usando el APP_SECRET y el body.
        4. Compara ambas firmas de manera segura contra ataques de tiempo (hmac.compare_digest).

        Args:
            request (Request): La petición entrante.

        Returns:
            bool: True si la firma es válida.

        Raises:
            HTTPException: Si falta el header o la firma no coincide.
        """
        if not settings.VERIFY_SIGNATURE:
            return True
        # ... resto del código ... (aquí se llamaría a las funciones privadas)
        # Nota: La implementación original llamaba a métodos privados self._get_signature_header etc.
        # Asumo que esas llamadas existen y solo modifico el docstring y la estructura visible

        # Para mantener el código funcional, reinserto el cuerpo original de la función
        header_signature = self._get_signature_header(request)
        raw_body = await self._get_raw_body(request)

        algorithm, signature_received = self.extract_signature(header_signature)

        self._validate_algorithm(algorithm, signature_received)

        expected_signature = self._generate_signature(raw_body)

        self._secure_compare(expected_signature, signature_received)

        return True

    def _get_signature_header(self, request: Request) -> str:
        """
        Obtiene el header X-Hub-Signature-256 de la petición.

        Raises:
            HTTPException (403): Si el header no está presente.
        """
        header_signature = request.headers.get("X-Hub-Signature-256")

        if not header_signature:
            raise HTTPException(status_code=403, detail="Signature header missing")

        return header_signature

    async def _get_raw_body(self, request: Request) -> bytes:
        """Obtiene el cuerpo crudo de la petición como bytes para el cálculo del hash.
        IMPORTANTE:
        Meta firma el body EXACTAMENTE como llega.
        No debe modificarse ni convertirse antes de firmar.
        """
        return await request.body()

    def _validate_algorithm(self, algorithm: str, signature_received: str) -> None:
        """
        Valida que:
        - El algoritmo sea sha256
        - La firma recibida no esté vacía
        """
        if algorithm != "sha256" or not signature_received:
            raise HTTPException(
                status_code=403, detail="Token inválido or invalid signature format"
            )

    def _generate_signature(self, raw_body: bytes) -> str:
        """
        Genera la firma HMAC SHA256 usando:
            - INSTAGRAM_APP_SECRET
            - body crudo (bytes)

        Retorna la firma en formato hexadecimal.
        """

        digest = hmac.new(
            self.INSTAGRAM_APP_SECRET.encode(), raw_body, hashlib.sha256
        ).hexdigest()

        return digest

    def _secure_compare(self, expected_signature: str, received_signature: str) -> None:
        """
        Compara ambas firmas usando comparación segura
        para evitar ataques de timing.
        """

        if not hmac.compare_digest(expected_signature, received_signature):
            raise HTTPException(status_code=403, detail="Token inválido")

    # UTILIDADES

    def extract_signature(self, header_signature: str):
        """
        El header_signature viene en formato:

            "sha256=abc123..."

        Necesitamos extraer el algoritmo y la firma por separado.
        """

        if "=" in header_signature:
            algorithm, signature = header_signature.split("=", 1)
            return algorithm, signature

        return None, None
