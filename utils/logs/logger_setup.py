from pydantic import BaseSettings
from logfire import Logfire

# Load settings from the default.toml file
class LogfireSettings(BaseSettings):
    token: str

    class Config:
        env_file = "default.toml"  # Path to the TOML file
        env_file_encoding = "utf-8"  # File encoding

# Initialize settings
settings = LogfireSettings()

# Initialize Logfire with the loaded token
logger = Logfire(api_key=settings.token)

# Example log message
logger.info("Logfire logging initialized successfully!")
