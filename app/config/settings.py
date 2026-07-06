from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/voice_agent"

    admin_username: str = "admin"
    admin_password: str = "admin123"
    jwt_secret: str = "change-this-secret"
    jwt_expire_minutes: int = 720

    vapi_api_key: str = ""
    vapi_phone_number_id: str = ""
    vapi_webhook_secret: str = ""
    vapi_server_url: str = ""

    crm_webhook_url: str = ""

    calling_start_hour: int = 10
    calling_end_hour: int = 19
    max_concurrent_calls: int = 5
    max_retries: int = 3
    retry_gap_hours: int = 3
    timezone: str = "Asia/Karachi"

    class Config:
        env_file = ".env"


settings = Settings()
