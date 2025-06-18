import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    nominatim_url: str = os.getenv("NOMINATIM_URL", "http://nominatim:8080")
    ors_url: str = os.getenv("ORS_URL", "http://openrouteservice:8080")
    ors_api_key: str = os.getenv("ORS_API_KEY", "")
    app_name: str = "Route Calculator API"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    class Config:
        env_file = ".env"

settings = Settings()