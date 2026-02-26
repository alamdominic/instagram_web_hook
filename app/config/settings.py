from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # BaseSettings es para leer configuración del entorno
    # Instagram Webhook
    INSTAGRAM_APP_SECRET: str
    VERIFY_SIGNATURE: bool
    INSTAGRAM_VERIFY_TOKEN: str
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str
    INSTAGRAM_ACCESS_TOKEN: str
    # App
    SECRET_KEY: str
    DEBUG: bool
    HOST: str
    PORT: int

    # Base de datos
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    DB_ECHO: bool = False  # Controla logs SQL independientemente de DEBUG

    model_config = SettingsConfigDict(env_file=".env")  # ← reemplaza class Config


settings = Settings()
