from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_mode: str = "beta"  # beta | production
    app_secret_key: str = "dev-secret-change-in-production"
    app_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://sellermate:password@localhost:5432/sellermate"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Cloudflare R2 / AWS S3
    s3_bucket_name: str = "sellermate-uploads"
    s3_region: str = "auto"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_endpoint_url: str = ""
    s3_public_url: str = ""  # CDN base URL for serving uploaded files

    # AI Providers
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""

    # WhatsApp Cloud API
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_webhook_verify_token: str = ""
    whatsapp_app_secret: str = ""

    # ── Courier: Pathao ───────────────────────────────────────────────────────
    pathao_client_id: str = ""
    pathao_client_secret: str = ""
    pathao_username: str = ""
    pathao_password: str = ""
    pathao_base_url: str = "https://hermes.pathao.com"

    # ── Courier: Steadfast ────────────────────────────────────────────────────
    steadfast_api_key: str = ""
    steadfast_secret_key: str = ""
    steadfast_base_url: str = "https://portal.steadfast.com.bd/public-api"

    # ── Courier: REDX ─────────────────────────────────────────────────────────
    redx_api_key: str = ""
    redx_base_url: str = "https://openapi.redx.com.bd"

    # ── Payment: SSLCommerz ───────────────────────────────────────────────────
    sslcommerz_store_id: str = ""
    sslcommerz_store_password: str = ""
    sslcommerz_sandbox: bool = True

    # ── Payment: bKash Tokenized Checkout ─────────────────────────────────────
    bkash_app_key: str = ""
    bkash_app_secret: str = ""
    bkash_username: str = ""
    bkash_password: str = ""
    bkash_sandbox: bool = True

    # ── Payment: Nagad ────────────────────────────────────────────────────────
    nagad_merchant_id: str = ""
    nagad_merchant_number: str = ""
    nagad_public_key: str = ""   # PEM public key provided by Nagad
    nagad_private_key: str = ""  # merchant's RSA private key
    nagad_sandbox: bool = True

    # ── SMTP (transactional email) ────────────────────────────────────────────
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@sellermate.ai"
    smtp_from_name: str = "SellerMate"
    smtp_tls: bool = True

    # ── Public storefront ─────────────────────────────────────────────────────
    storefront_base_url: str = "http://localhost:3000"  # for payment callback URLs

    # CORS
    allowed_origins: str = "http://localhost:3000"

    # OTP
    otp_expire_minutes: int = 10
    otp_length: int = 6

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_beta(self) -> bool:
        return self.app_mode == "beta"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def refresh_token_expire_seconds(self) -> int:
        return self.refresh_token_expire_days * 24 * 60 * 60

    @property
    def otp_expire_seconds(self) -> int:
        return self.otp_expire_minutes * 60

    @property
    def sslcommerz_base_url(self) -> str:
        return (
            "https://sandbox.sslcommerz.com"
            if self.sslcommerz_sandbox
            else "https://securepay.sslcommerz.com"
        )

    @property
    def bkash_base_url(self) -> str:
        return (
            "https://tokenized.sandbox.bka.sh/v1.2.0-beta"
            if self.bkash_sandbox
            else "https://tokenized.pay.bka.sh/v1.2.0-beta"
        )

    @property
    def nagad_base_url(self) -> str:
        return (
            "http://sandbox.mynagad.com:10080/merchant-api"
            if self.nagad_sandbox
            else "https://api.mynagad.com"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
