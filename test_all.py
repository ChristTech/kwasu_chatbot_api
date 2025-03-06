from geopy.geocoders import Nominatim

# Initialize the geocoder
geolocator = Nominatim(user_agent="geoapiExercises")

# List of location names
locations = [
    "Eiffel Tower, Paris",
    "Statue of Liberty, New York",
    "Taj Mahal, Agra",
    "Great Wall of China",
    "Sydney Opera House, Sydney"
]

# Dictionary to store location names and their coordinates
location_coordinates = {}

# Fetch coordinates for each location
for location in locations:
    try:
        # Get location data
        location_data = geolocator.geocode(location)
        
        if location_data:
            # Extract latitude and longitude
            latitude = location_data.latitude
            longitude = location_data.longitude
            
            # Save to dictionary
            location_coordinates[location] = (latitude, longitude)
            print(f"Fetched coordinates for {location}: ({latitude}, {longitude})")
        else:
            print(f"Could not find coordinates for {location}")
    except Exception as e:
        print(f"Error fetching coordinates for {location}: {e}")

# Output the dictionary
print("\nLocation Coordinates:")
for location, coordinates in location_coordinates.items():
    print(f"{location}: {coordinates}")