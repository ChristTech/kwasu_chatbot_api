import overpy

def fetch_locations():
    # Initialize the Overpass API
    api = overpy.Overpass()

    # Define the bounding box for KWASU (min_lat, min_lon, max_lat, max_lon)
    bbox = (8.7800, 4.4000, 8.9800, 4.6000)

    # Define the Overpass query to fetch all named features
    query = f"""
        [out:json];
        (
            node["name"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
            way["name"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
            relation["name"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        );
        out body;
        >;
        out skel qt;
    """

    # Execute the query
    result = api.query(query)

    # Dictionary to store location names and their coordinates
    location_coordinates = {}

    # Extract and save location data
    for node in result.nodes:
        name = node.tags.get("name", "Unnamed Location")
        latitude = node.lat
        longitude = node.lon
        location_coordinates[name] = (latitude, longitude)
        print(f"Fetched {name}: ({latitude}, {longitude})")

    return location_coordinates

fetch_locations()