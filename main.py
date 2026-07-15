import threading
from config import Settings
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import json
import time

class ProductInfo(BaseModel):
    product_id: str
    product_name: str
    price: float

def validate_and_retry(schema: BaseModel, max_retries: int, initial_delay: float, model_name: str, gemini_api_key: str):
    for i in range(max_retries):
        try:
            # Make API call to Gemini to get the product information
            response = get_product_info(model_name, gemini_api_key)
            # Validate the response against the schema
            schema.parse_raw(json.dumps(response))
            return response
        except Exception as e:
            print(f"Validation failed: {e}")
            # Exponential backoff for retry
            delay = initial_delay * (2 ** i)
            time.sleep(delay)
    return None

def get_product_info(model_name: str, gemini_api_key: str):
    # Simulate API call to Gemini
    return {
        "product_id": "12345",
        "product_name": "Test Product",
        "price": 19.99
    }

def main():
    settings = Settings()
    schema = ProductInfo
    max_retries = settings.default_max_retries
    initial_delay = settings.default_initial_delay
    model_name = settings.model_name
    gemini_api_key = settings.gemini_api_key

    if settings.enable_multithreading:
        # Create a separate thread for validation and retry logic
        thread = threading.Thread(target=validate_and_retry, args=(schema, max_retries, initial_delay, model_name, gemini_api_key))
        thread.start()
        thread.join()
    else:
        # Run validation and retry logic in the main thread
        validate_and_retry(schema, max_retries, initial_delay, model_name, gemini_api_key)

if __name__ == "__main__":
    main()
