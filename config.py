from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Configuration settings for the application, loaded from environment variables
    or a .env file.
    """
    model_name: str = "gemini-2.5-flash"
    temperature: float = 0.7
    max_tokens: int = 1024
    gemini_api_key: str = Field(validation_alias="GEMINI_API_KEY")
    # New: Add a default number of retries for the validation function
    default_max_retries: int = 3
    # New: Add a default initial delay for the retry mechanism
    default_initial_delay: float = 1.0

    model_config = SettingsConfigDict(
        env_file='.env',         # Load variables from .env file
        extra='ignore'           # Ignore extra environment variables
    )
