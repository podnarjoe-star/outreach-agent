import os
import requests

def search_places(city, business_type):
    try:
        api_key = os.environ.get("GOOGLE_PLACES_API_KEY")

        if not api_key:
            raise Exception("Google Places API key is missing. Please add GOOGLE_PLACES_API_KEY in Railway variables.")

        query = f"{business_type} in {city}"
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.websiteUri,places.formattedAddress,places.id"
        }
        data = {"textQuery": query}
        response = requests.post(url, headers=headers, json=data)

        if response.status_code != 200:
            raise Exception(f"Google Places API error {response.status_code}: {response.text}")

        results = response.json().get("places", [])

        if not results:
            return []

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

    except Exception as e:
        raise Exception(f"Failed to search for businesses: {str(e)}")