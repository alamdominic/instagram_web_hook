"""Security validation for Instagram webhook requests."""

import hashlib
import hmac
from fastapi import HTTPException, Request, Response
from app.config.settings import settings


class WebhookChecker:
    """Validate handshake parameters and request signatures for Meta webhooks."""

    def __init__(self):
        """Initialize with configuration secrets required for validation."""
        self.INSTAGRAM_VERIFY_TOKEN = settings.INSTAGRAM_VERIFY_TOKEN
        self.INSTAGRAM_APP_SECRET = settings.INSTAGRAM_APP_SECRET

    def verify(
        self, hub_mode: str, hub_verify_token: str, hub_challenge: str
    ) -> Response:
        """Validate the Meta verification handshake.

        Args:
            hub_mode (str): Subscription mode, expected to be "subscribe".
            hub_verify_token (str): Verification token from Meta.
            hub_challenge (str): Challenge string to echo back.

        Returns:
            Response: Plain text response with the challenge.

        Raises:
            HTTPException: If mode or token is invalid.
        """
        if hub_mode == "subscribe" and hub_verify_token == self.INSTAGRAM_VERIFY_TOKEN:
            return Response(content=hub_challenge, status_code=200)

        raise HTTPException(status_code=403, detail="Token inválido")

    async def verify_signature(self, request: Request) -> bool:
        """Validate the X-Hub-Signature-256 header for a POST request.

        Args:
            request (Request): Incoming HTTP request.

        Returns:
            bool: True when the signature is valid or verification is disabled.

        Raises:
            HTTPException: If the header is missing or the signature is invalid.
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
        """Extract the X-Hub-Signature-256 header.

        Args:
            request (Request): Incoming HTTP request.

        Returns:
            str: Signature header value.

        Raises:
            HTTPException: If the header is missing.
        """
        header_signature = request.headers.get("X-Hub-Signature-256")

        if not header_signature:
            raise HTTPException(status_code=403, detail="Signature header missing")

        return header_signature

    async def _get_raw_body(self, request: Request) -> bytes:
        """Return the raw request body bytes.

        Args:
            request (Request): Incoming HTTP request.

        Returns:
            bytes: Raw request body.
        """
        return await request.body()

    def _validate_algorithm(self, algorithm: str, signature_received: str) -> None:
        """Validate the signature format and algorithm.

        Args:
            algorithm (str): Signature algorithm prefix.
            signature_received (str): Signature payload.

        Raises:
            HTTPException: If algorithm or signature is invalid.
        """
        if algorithm != "sha256" or not signature_received:
            raise HTTPException(
                status_code=403, detail="Token inválido or invalid signature format"
            )

    def _generate_signature(self, raw_body: bytes) -> str:
        """Generate the expected HMAC SHA256 signature.

        Args:
            raw_body (bytes): Raw request body.

        Returns:
            str: Hex encoded signature.
        """

        digest = hmac.new(
            self.INSTAGRAM_APP_SECRET.encode(), raw_body, hashlib.sha256
        ).hexdigest()

        return digest

    def _secure_compare(self, expected_signature: str, received_signature: str) -> None:
        """Compare signatures in constant time.

        Args:
            expected_signature (str): Locally generated signature.
            received_signature (str): Signature from the header.

        Raises:
            HTTPException: If signatures do not match.
        """

        if not hmac.compare_digest(expected_signature, received_signature):
            raise HTTPException(status_code=403, detail="Token inválido")

    # UTILIDADES

    def extract_signature(self, header_signature: str):
        """Split header value into algorithm and signature.

        Args:
            header_signature (str): Raw header value.

        Returns:
            tuple[str | None, str | None]: Algorithm and signature pair.
        """

        if "=" in header_signature:
            algorithm, signature = header_signature.split("=", 1)
            return algorithm, signature

        return None, None
