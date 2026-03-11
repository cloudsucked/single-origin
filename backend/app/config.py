from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Single Origin API"
    app_version: str = "0.1.0"
    cors_origin: str = "*"
    turnstile_secret_key: str = ""
    turnstile_expected_hostname: str = ""
    enforce_turnstile: bool = False
    jwt_secret_key: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    database_path: str = "single_origin.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
