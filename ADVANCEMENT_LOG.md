2024-07-27: Introduced configurable default values for `max_retries` and `initial_delay` into `config.py` and utilized them in `main.py` to centralize retry mechanism settings.

2026-07-15: Implemented a Pydantic model validation with automatic retry using a separate thread for validation and retry logic, improving the overall performance and responsiveness of the system.
