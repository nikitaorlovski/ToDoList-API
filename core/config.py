from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class AuthJWT(BaseModel):
    private_key_path: Path = ROOT / "private.pem"
    public_key_path: Path = ROOT / "public.pem"
    access_token_expire: int = 15
    refresh_token_expire_days: int = 7


class Settings(BaseSettings):
    ALGORITHM: str
    auth_jwt: AuthJWT = AuthJWT()

    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )


settings = Settings()
