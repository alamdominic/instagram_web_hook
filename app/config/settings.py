"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application configuration.

    Attributes:
        INSTAGRAM_APP_SECRET (str): App secret used to validate signatures.
        VERIFY_SIGNATURE (bool): Enable or disable signature verification.
        INSTAGRAM_VERIFY_TOKEN (str): Verification token for GET handshake.
        INSTAGRAM_BUSINESS_ACCOUNT_ID (str): Instagram business account id.
        INSTAGRAM_ACCESS_TOKEN (str): Token for Graph API requests.
        SECRET_KEY (str): Application secret key.
        DEBUG (bool): Enable debug mode.
        HOST (str): Host binding for the API.
        PORT (int): Port for the API.
        POSTGRES_USER (str): Database user.
        POSTGRES_PASSWORD (str): Database password.
        POSTGRES_HOST (str): Database host.
        POSTGRES_PORT (int): Database port.
        POSTGRES_DB (str): Database name.
        DB_ECHO (bool): Enable SQL echo logging.
        EMAIL_SENDER (str): Sender email address.
        EMAIL_PASSWORD (str): Sender email password or app password.
        RECIPIENT_EMAIL (str): Comma-separated list of recipients.
    """

    INSTAGRAM_APP_SECRET: str
    VERIFY_SIGNATURE: bool
    INSTAGRAM_VERIFY_TOKEN: str
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str
    INSTAGRAM_ACCESS_TOKEN: str

    SECRET_KEY: str
    DEBUG: bool
    HOST: str
    PORT: int

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    DB_ECHO: bool = False

    EMAIL_SENDER: str
    EMAIL_PASSWORD: str
    RECIPIENT_EMAIL: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
