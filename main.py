import os
import time
import json
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from config import Settings

# Generic type for Pydantic models
T = TypeVar('T', bound=BaseModel)

# Load settings from config.py
settings = Settings()

# Configure the Google Generative AI client
genai.configure(api_key=settings.gemini_api_key)

# Define a Pydantic model for the expected output structure
class ProductInfo(BaseModel):
    name: str
    price: float
    currency: str
    description: str
    category: str

# Function to interact with the LLM, validate output, and retry
def validate_and_retry_llm_output(
    prompt: str,
    schema_model: Type[T],
    max_retries: int = settings.default_max_retries,  # Use setting for default
    initial_delay: float = settings.default_initial_delay # Use setting for default
) -> T:
    """
    Calls the LLM, attempts to parse and validate its output against a Pydantic schema,
    and retries on failure with exponential backoff.
    """
    model = genai.GenerativeModel(settings.model_name)
    current_delay = initial_delay

    print(f"Attempting to generate and validate structured output for prompt:\n'{prompt}'")
    print(f"Expected schema: {schema_model.__name__}")

    for attempt in range(1, max_retries + 1):
        print(f"\n--- Attempt {attempt}/{max_retries} ---")
        try:
            # Add schema instructions to the prompt
            schema_instruction = f"Output ONLY a JSON object conforming to the following Pydantic schema:\n{schema_model.schema_json(indent=2)}\n"
            full_prompt = f"{prompt}\n{schema_instruction}"

            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.temperature,
                    max_output_tokens=settings.max_tokens,
                    response_mime_type="application/json" # Request JSON directly
                ),
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )

            # Extract text from the response
            # Note: Gemini often returns content directly as json for 'application/json' mime type.
            # If it's a string, we parse it.
            raw_output = response.text.strip()
            print(f"Raw LLM output:\n{raw_output[:200]}...") # Show beginning of output

            # Attempt to parse JSON
            json_data = json.loads(raw_output)

            # Attempt to validate with Pydantic
            validated_data = schema_model.model_validate(json_data)
            print("Validation successful!")
            return validated_data

        except json.JSONDecodeError as e:
            print(f"Attempt {attempt} failed: JSON decoding error: {e}")
        except ValidationError as e:
            print(f"Attempt {attempt} failed: Pydantic validation error: {e.errors()}")
        except Exception as e:
            print(f"Attempt {attempt} failed: An unexpected error occurred: {e}")

        if attempt < max_retries:
            print(f"Retrying in {current_delay:.1f} seconds...")
            time.sleep(current_delay)
            current_delay *= 2  # Exponential backoff
        else:
            print("Max retries reached. Could not get valid structured output.")
            raise RuntimeError("Failed to get valid structured output after multiple retries.")

# --- Demo Usage ---
if __name__ == "__main__":
    # Example prompt for product information
    product_prompt = "Generate information for a high-end coffee maker, including its price in USD."

    try:
        validated_product = validate_and_retry_llm_output(
            prompt=product_prompt,
            schema_model=ProductInfo,
            # max_retries and initial_delay now default to values from settings
            # but can still be overridden here if needed.
            max_retries=5 # Example: override default for this specific call
        )
        print("\n--- Final Validated Product Info ---")
        print(validated_product.model_dump_json(indent=2))

    except RuntimeError as e:
        print(f"Application error: {e}")
    except Exception as e:
        print(f"An unhandled error occurred: {e}")
