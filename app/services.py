import httpx
from typing import Tuple, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class GeocodingService:
    def __init__(self):
        self.nominatim_url = settings.nominatim_url
        
    async def geocode(self, address: str) -> Tuple[Optional[float], Optional[float]]:
        """Geocode an address using Nominatim"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.nominatim_url}/search",
                    params={
                        "q": address,
                        "format": "json",
                        "limit": 3
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                
                data = response.json()
                if data:
                    lat = float(data[0]["lat"])
                    lon = float(data[0]["lon"])
                    return lat, lon
                else:
                    logger.warning(f"No results found for address: {address}")
                    return None, None
                    
        except Exception as e:
            logger.error(f"Geocoding error for address '{address}': {str(e)}")
            return None, None

class RoutingService:
    def __init__(self):
        self.ors_url = settings.ors_url
        
    async def calculate_distance(self, start_coords: Tuple[float, float], 
                                end_coords: Tuple[float, float]) -> Optional[float]:
        """Calculate distance between two points using OpenRouteService"""
        try:
            headers = {}
                
            async with httpx.AsyncClient() as client:
                # ORS expects coordinates as [lon, lat]
                response = await client.post(
                    f"{self.ors_url}/ors/v2/directions/driving-car",
                    json={
                        "coordinates": [
                            [start_coords[1], start_coords[0]],  # lon, lat
                            [end_coords[1], end_coords[0]]       # lon, lat
                        ]
                    },
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                
                data = response.json()
                if "routes" in data and data["routes"]:
                    # Distance is in meters, convert to kilometers
                    distance_meters = data["routes"][0]["summary"]["distance"]
                    return round(distance_meters / 1000, 2)
                else:
                    logger.warning("No routes found")
                    return None
                    
        except Exception as e:
            logger.error(f"Routing error: {str(e)}")
            return None