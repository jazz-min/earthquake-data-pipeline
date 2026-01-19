from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database configuration (reuses existing env vars)
    db_name: str = "earthquake_db"
    db_user: str = "earthquake_user"
    db_pass: str = "earthquake_pass"
    db_host: str = "postgres"
    db_port: int = 5432
    db_schema: str = "transformed_data"

    # USGS API configuration
    usgs_base_url: str = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    usgs_timeout_secs: int = 3
    usgs_retry_max: int = 2

    # Circuit breaker configuration
    cb_failure_threshold: int = 5
    cb_recovery_secs: int = 60

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
