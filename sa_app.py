import os
import requests
from dotenv import load_dotenv

# 1. Load variables from the .env file
load_dotenv()
CLIENT_ID = os.getenv("KR_CLIENT_ID")
CLIENT_SECRET = os.getenv("KR_CLIENT_SECRET")

# Base URL for Kroger API
KROGER_API_BASE = "https://api.kroger.com/v1"

def get_access_token():
    """
    Sends a POST request to the token endpoint
    and manages the token retrieval.
    """
    print("Attempting to retrieve access token...")

    # The required headers for the token endpoint
    # Uses the standard Base64 encoding method for Client Credentials flow
    auth_headers = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)

    # The required body/data for the request
    token_data = {
        'grant_type': 'client_credentials',
        'scope': 'product.compact' # Scope for public product searching
    }

    # Send the request
    token_url = f"{KROGER_API_BASE}/connect/oauth2/token"

    try:
        response = requests.post(token_url, auth=auth_headers, data=token_data)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        token_info = response.json()

        # Error checking and management (A6 concept)
        if 'access_token' not in token_info:
             print("Error: Token response missing 'access_token'.")
             return None

        access_token = token_info.get('access_token')
        expires_in = token_info.get('expires_in', 0)

        print(f"Token Retrieved Successfully! Expires in {expires_in} seconds.")
        return access_token

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error during token retrieval: {e}")
        print(f"Response: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Network Error during token retrieval: {e}")
        return None


def find_nearest_store(token, zip_code):
    """
    Finds the nearest store and extracts its locationId.
    """
    if not token:
        print("Cannot find location without a valid access token.")
        return None

    print(f"\nSearching for nearest store to zip code: {zip_code}...")

    # The required headers including the Bearer Token
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }

    # Query parameters for the Locations API
    location_params = {
        'filter.zipCode.near': zip_code,
        'filter.limit': 1  # We only need the nearest one
    }

    location_url = f"{KROGER_API_BASE}/locations"

    try:
        response = requests.get(location_url, headers=headers, params=location_params)
        response.raise_for_status()  # Raise exception for bad status codes

        location_data = response.json()

        #Location Parsing - Extracting the locationId
        stores = location_data.get('data')

        if stores and len(stores) > 0:
            store = stores[0]
            location_id = store.get('locationId')
            store_name = store.get('name')

            print(f"✅ Store Found: {store_name}")
            print(f"   Location ID: {location_id}")
            return location_id
        else:
            print(f"❌ No Kroger store found near {zip_code}.")
            return None

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error during location search: {e}")
        print(f"Response: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Network Error during location search: {e}")
        return None

def search_products(token, location_id, search_term):
    """
    Searches for products at a specific location and extracts key data.
    """
    if not token or not location_id:
        print("🛑 Cannot search products without valid token and location ID.")
        return None

    print(f"\nSearching for '{search_term}' at location ID {location_id}...")

    # Headers remain the same, using the Bearer Token
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }

    # Query parameters for the Products API
    product_params = {
        'filter.term': search_term,
        'filter.locationId': location_id,
        'filter.limit': 5
    }

    product_url = f"{KROGER_API_BASE}/products"

    try:
        response = requests.get(product_url, headers=headers, params=product_params)
        response.raise_for_status()

        product_data = response.json()
        products = product_data.get('data', [])

        if not products:
            print(f"❌ No products found matching '{search_term}' at this location.")
            return []

        results_list = []
        #Data Extraction - Looping through results to pull relevant fields
        for product in products:
            item_data = {
                'UPC': product.get('upc'),
                'Name': product.get('description'),
                'Price': 'N/A' # Default price until we find it
            }

            # Prices are nested under the 'items' array
            price_data = product.get('items', [])
            if price_data and price_data[0].get('price'):
                # Get the 'price' dictionary
                price_dict = price_data[0]['price']

                # Check if regular price exists
                if price_dict.get('regular') is not None:
                    # Access the float value and apply the formatting (A10)
                    price_value = price_dict['regular']
                    item_data['Price'] = f"${price_value:,.2f}"
                else:
                    item_data['Price'] = 'Price Data Missing'

            results_list.append(item_data)

        print(f"✅ Found {len(results_list)} results for '{search_term}'.")
        return results_list

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error during product search: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Network Error during product search: {e}")
        return None


def display_results(results):
    """
    Formats and displays the final output to the user.
    """
    if not results:
        return

    print("\n--- 🛒 **Compare and Select** Assistant Results ---")
    # Simple table formatting for clear output
    for i, item in enumerate(results):
        print(f"**{i + 1}. {item['Name']}**")
        print(f"   Price: {item['Price']:<10} | UPC: {item['UPC']}")
    print("----------------------------------------------------------")


if __name__ == "__main__":
    # Define parameters for testing
    TEST_ZIP_CODE = "45040"  # Use a valid US zip code near a Kroger store
    SEARCH_ITEM = "coffee"  # The item the user wants to compare

    # 1. Get the Access Token (Security Key)
    token = get_access_token()

    if token:
        # 2. Find the Nearest Store (Location Resource Key)
        location_id = find_nearest_store(token, TEST_ZIP_CODE)

        if location_id:
            # 3. Search Products (Information Processing)
            product_results = search_products(token, location_id, SEARCH_ITEM)

            # 4. Display Results (Integrated Output)
            display_results(product_results)
        else:
            print("\n❌ cannot proceed. Failed to secure location resource.")
    else:
        print("\n❌ startup failed. Cannot obtain access token.")