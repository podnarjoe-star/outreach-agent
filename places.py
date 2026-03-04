import os
import requests

def search_places(city, business_type):
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    query = f"{business_type} in {city}"
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.websiteUri,places.formattedAddress,places.id"
    }
    data = {"textQuery": query}
    response = requests.post(url, headers=headers, json=data)
    results = response.json().get("places", [])
    businesses = []
    for place in results[:10]:
        name = place.get("displayName", {}).get("text", "")
        website = place.get("websiteUri", "")
        address = place.get("formattedAddress", "")
        businesses.append({
            "name": name,
            "address": address,
            "website": website,
            "type": business_type
        })
    return businesses