from flask import Flask, request, jsonify
from datetime import datetime
import logging
import asyncio
from app.models import RouteRequest, RouteResponse, LocationRequest
from app.services import GeocodingService, RoutingService
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

geocoding_service = GeocodingService()
routing_service = RoutingService()

def compose_address(location_data: dict) -> str:
    """Compose a full address from individual fields"""
    address_parts = []
    
    # Add house number and street
    if location_data.get('HSNMR') and location_data.get('STRAS'):
        address_parts.append(f"{location_data['HSNMR']} {location_data['STRAS']}")
    elif location_data.get('STRAS'):
        address_parts.append(location_data['STRAS'])
    elif location_data.get('HSNMR'):
        address_parts.append(location_data['HSNMR'])
    
    # Add location complement if exists
    if location_data.get('LOCAT'):
        address_parts.append(location_data['LOCAT'])
    
    # Add postal code and city
    if location_data.get('PSTLZ') and location_data.get('ORT01'):
        address_parts.append(f"{location_data['PSTLZ']} {location_data['ORT01']}")
    elif location_data.get('ORT01'):
        address_parts.append(location_data['ORT01'])
    
    # Add country
    if location_data.get('LAND1'):
        address_parts.append(location_data['LAND1'])
    
    # Join all parts with comma
    return ", ".join(address_parts)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": settings.app_name})

@app.route('/calculate-route', methods=['POST'])
def calculate_route():
    """Calculate the shortest distance between two addresses"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "error": "No JSON data provided",
                "data": None,
                "metadata": {"timestamp": datetime.utcnow().isoformat()}
            }), 400
        
        # Validate request data
        try:
            route_request = RouteRequest(**data)
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": f"Invalid request data: {str(e)}",
                "data": None,
                "metadata": {"timestamp": datetime.utcnow().isoformat()}
            }), 400
        
        # Compose full addresses
        home_address = compose_address(route_request.home.dict())
        office_address = compose_address(route_request.office.dict())
        
        logger.info(f"Composed home address: {home_address}")
        logger.info(f"Composed office address: {office_address}")
        
        # Run async operations in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Geocode home address
            home_lat, home_lon = loop.run_until_complete(
                geocoding_service.geocode(home_address)
            )
            if home_lat is None or home_lon is None:
                raise ValueError(f"Could not geocode home address: {home_address}")
            
            # Geocode office address
            office_lat, office_lon = loop.run_until_complete(
                geocoding_service.geocode(office_address)
            )
            if office_lat is None or office_lon is None:
                raise ValueError(f"Could not geocode office address: {office_address}")
            
            # Calculate distance
            distance = loop.run_until_complete(
                routing_service.calculate_distance(
                    (home_lat, home_lon),
                    (office_lat, office_lon)
                )
            )
            
            if distance is None:
                raise ValueError("Could not calculate route between addresses")
                
        finally:
            loop.close()
        
        # Prepare response
        response_data = {
            "status": "success",
            "error": None,
            "data": {
                "home": {
                    "HSNMR": route_request.home.HSNMR,
                    "STRAS": route_request.home.STRAS,
                    "LOCAT": route_request.home.LOCAT,
                    "PSTLZ": route_request.home.PSTLZ,
                    "ORT01": route_request.home.ORT01,
                    "LAND1": route_request.home.LAND1,
                    "home_address": home_address,
                    "coordinates": {
                        "latitude": home_lat,
                        "longitude": home_lon
                    }
                },
                "office": {
                    "HSNMR": route_request.office.HSNMR,
                    "STRAS": route_request.office.STRAS,
                    "LOCAT": route_request.office.LOCAT,
                    "PSTLZ": route_request.office.PSTLZ,
                    "ORT01": route_request.office.ORT01,
                    "LAND1": route_request.office.LAND1,
                    "office_address": office_address,
                    "coordinates": {
                        "latitude": office_lat,
                        "longitude": office_lon
                    }
                },
                "distance": distance
            },
            "metadata": {
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        return jsonify(response_data)
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "data": None,
            "metadata": {"timestamp": datetime.utcnow().isoformat()}
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "An unexpected error occurred",
            "data": None,
            "metadata": {"timestamp": datetime.utcnow().isoformat()}
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=settings.debug)