# controllers/webhook_checker.py
from fastapi import HTTPException, Request, Response
import hmac
import hashlib

# importamos la instancia, no la clase: settings = Settings()
# Es el patrón Singleton una sola instancia para toda la app.
from app.config.settings import settings


class WebhookChecker:
    """
    Clase responsable de:
    - Validar el webhook inicial de Meta (hub challenge)
    - Verificar la firma de seguridad (X-Hub-Signature-256)

    Principio aplicado:
    - Separación de responsabilidades
    - Métodos pequeños y testeables
    """

    def __init__(self):
        self.INSTAGRAM_VERIFY_TOKEN = settings.INSTAGRAM_VERIFY_TOKEN
        self.INSTAGRAM_APP_SECRET = settings.INSTAGRAM_APP_SECRET

    # VERIFICACIÓN INICIAL DEL WEBHOOK (GET)

    def verify(
        self, hub_mode: str, hub_verify_token: str, hub_challenge: str
    ) -> Response:
        """
        Verifica el challenge inicial enviado por Meta cuando se configura el webhook.

        Meta envía:
            hub.mode
            hub.verify_token
            hub.challenge

        Si el verify_token coincide con el configurado en nuestra app,
        debemos devolver el challenge con status 200.
        """

        if hub_mode == "subscribe" and hub_verify_token == self.INSTAGRAM_VERIFY_TOKEN:
            return Response(content=hub_challenge, status_code=200)

        raise HTTPException(status_code=403, detail="Token inválido")

    # VERIFICACIÓN DE FIRMA (POST)

    """
    X-Hub-Signature-256: sha256=a1b2c3d4e5f6...
    Esa firma es un HMAC SHA256 generado con:
        - Tu App Secret
        - El body crudo de la petición
    """

    async def verify_signature(self, request: Request) -> bool:
        """
        Orquesta el proceso completo de verificación de firma:

        1. Obtener header de firma
        2. Obtener body crudo
        3. Extraer algoritmo y firma recibida
        4. Generar firma local
        5. Comparación segura

        Retorna True si la firma es válida.
        Lanza HTTPException si la firma es inválida.
        """
        if not settings.VERIFY_SIGNATURE:
            return True
        header_signature = self._get_signature_header(request)
        raw_body = await self._get_raw_body(request)

        algorithm, signature_received = self.extract_signature(header_signature)

        self._validate_algorithm(algorithm, signature_received)

        expected_signature = self._generate_signature(raw_body)

        self._secure_compare(expected_signature, signature_received)

        return True

    def _get_signature_header(self, request: Request) -> str:
        """
        Obtiene el header X-Hub-Signature-256.

        Lanza excepción si no existe.
        """
        header_signature = request.headers.get("X-Hub-Signature-256")

        if not header_signature:
            raise HTTPException(status_code=403, detail="Signature header missing")

        return header_signature

    async def _get_raw_body(self, request: Request) -> bytes:
        """
        Obtiene el body crudo en formato bytes.

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
