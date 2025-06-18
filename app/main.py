from fastapi import FastAPI, HTTPException
from datetime import datetime
import logging
from app.models import RouteRequest, RouteResponse
from app.services import GeocodingService, RoutingService
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, debug=settings.debug)

geocoding_service = GeocodingService()
routing_service = RoutingService()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.app_name}

@app.post("/distance_ik", response_model=RouteResponse)
async def calculate_route(request: RouteRequest):
    """Calculate the shortest distance between two addresses"""
    try:
        # Geocode home address
        home_lat, home_lon = await geocoding_service.geocode(request.home_address)
        if home_lat is None or home_lon is None:
            raise ValueError(f"Could not geocode home address: {request.home_address}")
        
        # Geocode office address
        office_lat, office_lon = await geocoding_service.geocode(request.office_address)
        if office_lat is None or office_lon is None:
            raise ValueError(f"Could not geocode office address: {request.office_address}")
        
        # Calculate distance
        distance = await routing_service.calculate_distance(
            (home_lat, home_lon),
            (office_lat, office_lon)
        )
        
        if distance is None:
            raise ValueError("Could not calculate route between addresses")
        
        # Prepare response
        return RouteResponse(
            status="success",
            error=None,
            data={
                "home": {
                    "home_address": request.home_address,
                    "coordinates": {
                        "latitude": home_lat,
                        "longitude": home_lon
                    }
                },
                "office": {
                    "office_address": request.office_address,
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