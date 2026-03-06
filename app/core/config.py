from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "Real-Time Machine Data Ingestion Service"
    PROJECT_DESCRIPTION: str = "Microservice for receiving, storing, and serving real-time sensor data from industrial machines"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Server Config
    SERVER_HOST: str = "localhost"
    SERVER_PORT: int = 8000
    
    # PostgreSQL Backend
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # InfluxDB Backend (for Sensor Data)
    INFLUXDB_URL: str
    INFLUXDB_TOKEN: str
    INFLUXDB_ORG: str
    INFLUXDB_BUCKET: str
    
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

settings = Settings()
