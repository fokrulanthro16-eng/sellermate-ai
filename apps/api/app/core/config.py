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

    # Trusted reverse-proxy CIDRs for IP header forwarding.
    # Set to a comma-separated list of CIDRs (e.g. "10.0.0.0/8,172.16.0.0/12")
    # when the app runs behind nginx/Cloudflare so the real client IP is used
    # for rate limiting instead of the proxy's IP. Leave empty to use the
    # direct TCP connection address (safe default for direct-internet deployments).
    trusted_proxy_cidrs: str = ""

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
    def trusted_proxy_cidr_list(self) -> list[str]:
        return [c.strip() for c in self.trusted_proxy_cidrs.split(",") if c.strip()]

    @property
    def refresh_token_expire_seconds(self) -> int:
        return self.refresh_token_expire_days * 24 * 60 * 60

    @property
    def otp_expire_seconds(self) -> int:
        return self.otp_expire_minutes * 60

    def validate_production_config(self) -> list[str]:
        """
        Return a list of human-readable errors that must be fixed before the app
        can boot in production. An empty list means the config is safe.
        Only runs when APP_ENV=production; always returns [] in other envs.
        """
        if not self.is_production:
            return []

        errors: list[str] = []

        if self.app_secret_key == "dev-secret-change-in-production":
            errors.append(
                "APP_SECRET_KEY must be set to a cryptographically secure random value"
            )

        _local_db = "postgresql+asyncpg://sellermate:password@localhost"
        if self.database_url.startswith(_local_db):
            errors.append("DATABASE_URL must point to the production database, not localhost")

        if self.redis_url == "redis://localhost:6379/0":
            errors.append("REDIS_URL must point to the production Redis instance, not localhost")

        # Payment: live mode requires full credentials
        if not self.bkash_sandbox:
            missing = [
                k for k, v in {
                    "BKASH_APP_KEY": self.bkash_app_key,
                    "BKASH_APP_SECRET": self.bkash_app_secret,
                    "BKASH_USERNAME": self.bkash_username,
                    "BKASH_PASSWORD": self.bkash_password,
                }.items() if not v
            ]
            if missing:
                errors.append(
                    f"BKASH_SANDBOX=false but these credentials are missing: {', '.join(missing)}"
                )

        if not self.sslcommerz_sandbox:
            missing = [
                k for k, v in {
                    "SSLCOMMERZ_STORE_ID": self.sslcommerz_store_id,
                    "SSLCOMMERZ_STORE_PASSWORD": self.sslcommerz_store_password,
                }.items() if not v
            ]
            if missing:
                errors.append(
                    f"SSLCOMMERZ_SANDBOX=false but these credentials are missing: {', '.join(missing)}"
                )

        if not self.nagad_sandbox:
            missing = [
                k for k, v in {
                    "NAGAD_MERCHANT_ID": self.nagad_merchant_id,
                    "NAGAD_MERCHANT_NUMBER": self.nagad_merchant_number,
                    "NAGAD_PUBLIC_KEY": self.nagad_public_key,
                    "NAGAD_PRIVATE_KEY": self.nagad_private_key,
                }.items() if not v
            ]
            if missing:
                errors.append(
                    f"NAGAD_SANDBOX=false but these credentials are missing: {', '.join(missing)}"
                )

        # Courier: partial credentials are a misconfiguration
        if self.pathao_client_id:
            missing = [
                k for k, v in {
                    "PATHAO_CLIENT_SECRET": self.pathao_client_secret,
                    "PATHAO_USERNAME": self.pathao_username,
                    "PATHAO_PASSWORD": self.pathao_password,
                }.items() if not v
            ]
            if missing:
                errors.append(
                    f"PATHAO_CLIENT_ID is set but these are missing: {', '.join(missing)}"
                )

        if self.steadfast_api_key and not self.steadfast_secret_key:
            errors.append(
                "STEADFAST_API_KEY is set but STEADFAST_SECRET_KEY is missing"
            )

        return errors

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
