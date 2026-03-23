from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Single Origin API"
    app_version: str = "0.1.0"
    cors_origin: str = "*"
    turnstile_secret_key: str = ""
    turnstile_expected_hostname: str = ""
    enforce_turnstile: bool = False

    # JWT signing — HS256 symmetric key (default / dev mode)
    jwt_secret_key: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"

    # Lab mode: when LAB_JWT_PRIVATE_KEY is set, the app switches to RS256 signing.
    # The private key is a PEM string with literal \n escape sequences (as stored
    # in environment variables / Terraform variables). The app normalises \n → newlines
    # at startup. Setting this also activates the JWKS endpoint with the matching
    # public key so Cloudflare API Shield JWT Validation can verify lab tokens.
    lab_jwt_private_key: str = ""

    database_path: str = "single_origin.db"
    seed_demo_email: str = "demo@singleorigin.example"
    seed_demo_password: str = ""
    seed_wholesale_email: str = "wholesale@cafepartner.example"
    seed_wholesale_password: str = ""
    seed_admin_email: str = "admin@singleorigin.example"
    seed_admin_password: str = ""
    seed_test_users_password: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
