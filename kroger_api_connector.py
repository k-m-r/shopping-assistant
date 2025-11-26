import os
import requests
import time  # Added for tracking token expiration
from dotenv import load_dotenv

# Load environment variables once here
load_dotenv()


class KrogerResourceClient:
    """
    Manages all state and interaction with the Kroger Public API.
    Handles token retrieval, caching, and refresh automatically.
    """

    def __init__(self):
        # Configuration and State
        self._client_id = os.getenv("KR_CLIENT_ID")
        self._client_secret = os.getenv("KR_CLIENT_SECRET")
        self._api_base = "https://api.kroger.com/v1"
        self._access_token = None
        self._token_expires_at = 0

        # Initial check/refresh to ensure we start with a valid token
        self._refresh_token()

    def _refresh_token(self):
        """Internal method to fetch a new token if needed."""

        if not self._client_id or not self._client_secret:
            print("Error: Kroger API credentials not set.")
            return

        if self._access_token and self._token_expires_at > time.time() + 60:
            # Token is still valid for at least 60 seconds, no refresh needed
            return

        print("🔑 Refreshing access token...")
        auth_headers = requests.auth.HTTPBasicAuth(self._client_id, self._client_secret)
        token_data = {'grant_type': 'client_credentials', 'scope': 'product.compact'}
        token_url = f"{self._api_base}/connect/oauth2/token"

        try:
            response = requests.post(token_url, auth=auth_headers, data=token_data)
            response.raise_for_status()
            token_info = response.json()

            # Update instance state
            self._access_token = token_info.get('access_token')
            self._token_expires_at = time.time() + token_info.get('expires_in', 0)
            print("✅ Token refreshed successfully.")

        except requests.exceptions.RequestException as e:
            print(f"Error during token retrieval: {e}")
            self._access_token = None
            self._token_expires_at = 0

    def find_nearest_store(self, zip_code):
        """Finds the nearest store to a given zip code and extracts its locationId."""
        self._refresh_token()
        if not self._access_token:
            return None

        headers = {'Authorization': f'Bearer {self._access_token}', 'Accept': 'application/json'}
        location_params = {'filter.zipCode.near': zip_code, 'filter.limit': 1}
        location_url = f"{self._api_base}/locations"

        try:
            response = requests.get(location_url, headers=headers, params=location_params)
            response.raise_for_status()
            stores = response.json().get('data')

            if stores and len(stores) > 0:
                location_id = stores[0].get('locationId')
                print(f"Store found. Name : {stores[0].get('name')} , Location Id:  {location_id}")
                return location_id
            else:
                return None

        except requests.exceptions.RequestException as e:
            print(f"🚨 Error during location search: {e}")
            return None

    def search_products(self, location_id, search_term):
        """Searches for products at a specific location."""
        self._refresh_token()
        if not self._access_token or not location_id:
            return []

        headers = {'Authorization': f'Bearer {self._access_token}', 'Accept': 'application/json'}
        product_params = {
            'filter.term': search_term,
            'filter.locationId': location_id,
            'filter.limit': 5
        }
        product_url = f"{self._api_base}/products"

        try:
            response = requests.get(product_url, headers=headers, params=product_params)
            response.raise_for_status()
            products = response.json().get('data', [])

            results_list = []
            for product in products:
                # [Price extraction logic as previously fixed]
                item_data = {
                    'UPC': product.get('upc'),
                    'Name': product.get('description'),
                    'Price': 'N/A',
                    'PromoPrice': 'N/A'
                }
                price_data = product.get('items', [])
                if price_data and price_data[0].get('price'):
                    price_dict = price_data[0]['price']
                    if price_dict.get('regular') is not None:
                        price_value = price_dict['regular']
                        item_data['Price'] = f"${price_value:,.2f}"
                    if price_dict.get('promo') is not None:
                        promo_price = price_dict['promo']
                        item_data['PromoPrice'] = f"${promo_price:,.2f}"
                results_list.append(item_data)

            return results_list

        except requests.exceptions.RequestException as e:
            print(f"🚨 Error during product search: {e}")
            return []
