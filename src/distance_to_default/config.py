"""Application configuration loaded from environment variables."""

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime settings."""

    model_config = SettingsConfigDict(env_prefix="DISTANCE_TO_DEFAULT_", extra="ignore")

    log_level: str = "INFO"
    # No prefix on purpose: this is the same variable every project in the
    # portfolio uses — one DSN configures all of them.
    # TODO: rename to PUBLIC_MARKET_DATA_POSTGRES_DSN once dados-mercado-publico
    # is renamed to public-market-data.
    market_data_dsn: str = Field(
        default="postgresql://dados:dados@localhost:5433/dados_mercado_publico",
        validation_alias=AliasChoices("DADOS_MERCADO_PUBLICO_POSTGRES_DSN"),
    )
