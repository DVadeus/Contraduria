"""Configuration centralisée de Contraduría via pydantic-settings.

Todas las variables de entorno usan el prefijo CONTRADURIA_.
Ejemplo: CONTRADURIA_PARQUET_DIR, CONTRADURIA_DEBUG, etc.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings globales de la API Contraduría.

    Cargadas desde variables de entorno con prefijo CONTRADURIA_,
    y desde archivo .env si existe.
    """

    model_config = SettingsConfigDict(
        env_prefix="CONTRADURIA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -- App --
    app_name: str = "Contraduría API"
    app_version: str = "0.1.0"
    debug: bool = False

    # -- Project root --
    project_root: Path = Path(__file__).resolve().parent.parent.parent.parent.parent

    # -- DuckDB --
    parquet_dir: str = "data/parquet"
    duckdb_threads: int = 4
    duckdb_memory_limit: str = "4GB"
    duckdb_read_only: bool = True

    # -- API --
    cors_origins: list[str] = ["*"]
    api_prefix: str = ""

    # -- Pagination defaults --
    default_page_size: int = 50
    max_page_size: int = 200

    # -- ETL metadata --
    etl_state_file: str = "data/metadata/etl_state.json"

    @property
    def parquet_dir_absolute(self) -> Path:
        """Devuelve la ruta absoluta al directorio Parquet."""
        p = Path(self.parquet_dir)
        if p.is_absolute():
            return p
        return self.project_root / p

    @property
    def etl_state_path(self) -> Path:
        """Devuelve la ruta absoluta al archivo de estado ETL."""
        p = Path(self.etl_state_file)
        if p.is_absolute():
            return p
        return self.project_root / p


# Singleton de configuración
settings = Settings()
