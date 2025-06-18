from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class Coordinates(BaseModel):
    latitude: float
    longitude: float

class LocationData(BaseModel):
    address: str
    coordinates: Coordinates

class LocationRequest(BaseModel):
    HSNMR: str #Numero de rue
    STRAS: str #Rue
    LOCAT: str #Complement d'adresse
    PSTLZ: str #Code postal
    ORT01: str #Ville
    LAND1: str #Pays

class RouteRequest(BaseModel):
    home: LocationRequest
    office: LocationRequest

class RouteResponse(BaseModel):
    status: Literal["success", "error"]
    error: Optional[str] = None
    data: Optional[dict] = None
    metadata: dict

class RouteData(BaseModel):
    home: dict
    office: dict
    distance: float