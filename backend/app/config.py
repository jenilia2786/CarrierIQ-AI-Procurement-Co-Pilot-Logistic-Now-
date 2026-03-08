from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str = ""
    groq_api_key: str = ""
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "carrieriq"
    secret_key: str = "CarrierIQ_SuperSecret_Key_2024"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
