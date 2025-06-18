import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    nominatim_url: str = os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org")
    ors_url: str = os.getenv("ORS_URL", "http://51.44.41.148:8082")
    app_name: str = "Route Calculator API"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    class Config:
        env_file = ".env"

settings = Settings()