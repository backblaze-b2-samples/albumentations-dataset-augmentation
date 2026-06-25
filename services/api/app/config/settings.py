from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Backblaze B2 region (e.g. "us-west-004"). The S3 endpoint is derived
    # from it via the `b2_endpoint` property — never hardcode a full endpoint
    # URL anywhere in source.
    b2_region: str = "us-west-004"
    b2_application_key_id: str = ""
    b2_application_key: str = ""
    b2_bucket_name: str = ""
    b2_public_url_base: str = ""

    # Max source images augmented in a single synchronous run. Bounds the
    # demo so a 500-seed run doesn't block the request for minutes. Documented,
    # not silently capped — the UI surfaces when a run is truncated.
    max_run_source_images: int = 50

    api_port: int = 8000
    # Explicit allowlist by default — covers Next on :3000 and the
    # fallback :3001 it picks if 3000 is busy. Production deploys should
    # override with the exact frontend origin.
    api_cors_origins: str = "http://localhost:3000,http://localhost:3001"
    # Optional dev-only escape hatch: a regex that matches additional
    # allowed origins. Empty by default — set this to e.g.
    # `^http://localhost:\d+$` to accept any localhost port without
    # listing each one. NEVER ship this to production.
    api_cors_origin_regex: str = ""

    # Upload limits
    max_file_size: int = 100 * 1024 * 1024  # 100MB

    # Small durable counters (downloads, etc). Point at a persistent
    # volume in production if you care about surviving restarts.
    download_count_file: str = "data/download_count.json"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def b2_endpoint(self) -> str:
        """S3-compatible endpoint derived from the configured region.

        Keeping the region as the source of truth (rather than a hardcoded
        endpoint string) is parent-standard #4 — no region literals in source.
        """
        return f"https://s3.{self.b2_region}.backblazeb2.com"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",")]


settings = Settings()
