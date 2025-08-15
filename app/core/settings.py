import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Define o ambiente atual (default para 'development')
ENV = os.getenv("ENV", "development")

# Carrega variáveis do arquivo correspondente
load_dotenv(f".env.{ENV}", override=True)


class Settings(BaseSettings):
    user: str = ""
    password: str = ""
    host: str = "localhost"
    port: int = 5432
    dbname: str = "postgres"
    debug: bool = ENV == "development"
    secret_key: str = "your_secret_key"
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"

    model_config = SettingsConfigDict(env_file=f".env.{ENV}", extra="ignore")

    @property
    def database_url_async(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"

    @property
    def database_url_sync(self) -> str:
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"


settings = Settings()

DATABASE_URL_ASYNC = settings.database_url_async
DATABASE_URL_SYNC = settings.database_url_sync
