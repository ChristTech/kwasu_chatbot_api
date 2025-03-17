import requests
import time

def get_osm_places_from_bbox(south, north, west, east):
    """
    Fetches points of interest from OpenStreetMap within a bounding box.

    Returns:
        List of (lat, lon) tuples.
    """
    query = f"""
    [out:json][timeout:25];
    (
      node({south},{west},{north},{east});
    );
    out center;
    """
    
    url = "http://overpass-api.de/api/interpreter"
    response = requests.post(url, data={'data': query})

    coordinates = []
    if response.status_code == 200:
        data = response.json()
        for element in data.get("elements", []):
            lat = element.get("lat")
            lon = element.get("lon")
            if lat and lon:
                coordinates.append((lat, lon))
    else:
        print("Error:", response.status_code, response.text)

    return coordinates

def reverse_geocode(lat, lon):
    """
    Uses OpenStreetMap's Nominatim API to get a place name from coordinates.

    Returns:
        tuple: (place_name, lat, lon)
    """
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
    headers = {"User-Agent": "Kivy-App/1.0"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        place_name = data.get("display_name")

        # Try to extract more useful information if display_name is missing
        if not place_name and "address" in data:
            address = data["address"]
            place_name = address.get("name") or address.get("road") or address.get("building")

        if place_name:
            return place_name, lat, lon

    print(f"Reverse geocoding failed for ({lat}, {lon}):", response.status_code)
    return None  # Skip if no name is found

def get_places_with_names(south, north, west, east):
    """
    Retrieves all coordinates in the bounding box and reverse geocodes them.

    Returns:
        dict: {place_name: (lat, lon)}
    """
    coordinates = get_osm_places_from_bbox(south, north, west, east)
    places = {}

    for lat, lon in coordinates:
        result = reverse_geocode(lat, lon)
        if result:
            place_name, lat, lon = result
            places[place_name] = (lat, lon)
        time.sleep(1)  # Avoid exceeding API rate limits

    return places

# Example usage
if __name__ == "__main__":
    south, north, west, east = 8.71433, 8.72833, 4.47161, 4.49341
    places_data = get_places_with_names(south, north, west, east)

    for name, coords in places_data.items():
        print(f"{name}: {coords}")
