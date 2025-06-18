from fastapi import FastAPI, HTTPException
from datetime import datetime
import logging
from app.models import RouteRequest, RouteResponse, LocationRequest
from app.services import GeocodingService, RoutingService
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, debug=settings.debug)

geocoding_service = GeocodingService()
routing_service = RoutingService()

def compose_address(location: LocationRequest) -> str:
    """Compose a full address from individual fields"""
    address_parts = []
    
    # Add house number and street
    if location.HSNMR and location.STRAS:
        address_parts.append(f"{location.HSNMR} {location.STRAS}")
    elif location.STRAS:
        address_parts.append(location.STRAS)
    
    # Add location complement if exists
    if location.LOCAT:
        address_parts.append(location.LOCAT)
    
    # Add postal code and city
    if location.PSTLZ and location.ORT01:
        address_parts.append(f"{location.PSTLZ} {location.ORT01}")
    elif location.ORT01:
        address_parts.append(location.ORT01)
    
    # Add country
    if location.LAND1:
        address_parts.append(location.LAND1)
    
    # Join all parts with comma
    return ", ".join(address_parts)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.app_name}

@app.post("/calculate-route", response_model=RouteResponse)
async def calculate_route(request: RouteRequest):
    """Calculate the shortest distance between two addresses"""
    try:
        # Compose full addresses
        home_address = compose_address(request.home)
        office_address = compose_address(request.office)
        
        logger.info(f"Composed home address: {home_address}")
        logger.info(f"Composed office address: {office_address}")
        
        # Geocode home address
        home_lat, home_lon = await geocoding_service.geocode(home_address)
        if home_lat is None or home_lon is None:
            raise ValueError(f"Could not geocode home address: {home_address}")
        
        # Geocode office address
        office_lat, office_lon = await geocoding_service.geocode(office_address)
        if office_lat is None or office_lon is None:
            raise ValueError(f"Could not geocode office address: {office_address}")
        
        # Calculate distance
        distance = await routing_service.calculate_distance(
            (home_lat, home_lon),
            (office_lat, office_lon)
        )
        
        if distance is None:
            raise ValueError("Could not calculate route between addresses")
        
        # Prepare response with all individual fields
        return RouteResponse(
            status="success",
            error=None,
            data={
                "home": {
                    "HSNMR": request.home.HSNMR,
                    "STRAS": request.home.STRAS,
                    "LOCAT": request.home.LOCAT,
                    "PSTLZ": request.home.PSTLZ,
                    "ORT01": request.home.ORT01,
                    "LAND1": request.home.LAND1,
                    "home_address": home_address,
                    "coordinates": {
                        "latitude": home_lat,
                        "longitude": home_lon
                    }
                },
                "office": {
                    "HSNMR": request.office.HSNMR,
                    "STRAS": request.office.STRAS,
                    "LOCAT": request.office.LOCAT,
                    "PSTLZ": request.office.PSTLZ,
                    "ORT01": request.office.ORT01,
                    "LAND1": request.office.LAND1,
                    "office_address": office_address,
                    "coordinates": {
                        "latitude": office_lat,
                        "longitude": office_lon
                    }
                },
                "distance": distance
            },
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return RouteResponse(
            status="error",
            error=str(e),
            data=None,
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return RouteResponse(
            status="error",
            error="An unexpected error occurred",
            data=None,
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)