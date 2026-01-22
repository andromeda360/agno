from __future__ import annotations

from importlib import metadata

from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

from agno_v2.utils.log import logger


class AgnoAPISettings(BaseSettings):
    app_name: str = "agno_v2"
    app_version: str = metadata.version("agno_v2")

    api_runtime: str = "prd"
    alpha_features: bool = False

    api_url: str = "https://os-api.agno.com"

    model_config = SettingsConfigDict(env_prefix="AGNO_V2_V2_")

    @field_validator("api_runtime", mode="before")
    def validate_runtime_env(cls, v):
        """Validate api_runtime."""

        valid_api_runtimes = ["dev", "stg", "prd"]
        if v.lower() not in valid_api_runtimes:
            raise ValueError(f"Invalid api_runtime: {v}")

        return v.lower()

    @field_validator("api_url", mode="before")
    def update_api_url(cls, v, info: ValidationInfo):
        api_runtime = info.data["api_runtime"]
        if api_runtime == "dev":
            from os import getenv

            if getenv("AGNO_V2_V2_RUNTIME") == "docker":
                return "http://host.docker.internal:7070"
            return "http://localhost:7070"
        elif api_runtime == "stg":
            return "https://api-stg.agno.com"
        else:
            return "https://os-api.agno.com"

    def gate_alpha_feature(self):
        if not self.alpha_features:
            logger.error("This is an Alpha feature not for general use.\nPlease message the Agno team for access.")
            exit(1)


agno_api_settings = AgnoAPISettings()
