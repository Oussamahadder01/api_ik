from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class Coordinates(BaseModel):
    latitude: float
    longitude: float

class LocationData(BaseModel):
    address: str
    coordinates: Coordinates

class RouteRequest(BaseModel):
    home_address: str
    office_address: str

class RouteResponse(BaseModel):
    status: Literal["success", "error"]
    error: Optional[str] = None
    data: Optional[dict] = None
    metadata: dict

class RouteData(BaseModel):
    home: dict
    office: dict
    distance: float