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
    
    # Database Backend
    DB_ENGINE: str = "postgresql"
    DB_DRIVER: str = "asyncpg"
    DB_HOST: str = "localhost"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_NAME: str = "postgres"
    DB_PORT: int = 5432
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"{self.DB_ENGINE}+{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # InfluxDB Backend (for Sensor Data)
    INFLUXDB_URL: str
    INFLUXDB_TOKEN: str
    INFLUXDB_ORG: str
    INFLUXDB_BUCKET: str

    # MQTT Broker (for Real-Time Sensor Ingestion)
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_TOPIC_FILTER: str = "factory/A/machine/+/telemetry"
    MQTT_CLIENT_ID: str = "gonster-subscriber"

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

settings = Settings()
