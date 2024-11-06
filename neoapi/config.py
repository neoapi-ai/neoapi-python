import os


class Config:
    API_KEY = os.getenv("NEOAPI_API_KEY", "")
    API_URL = os.getenv("NEOAPI_API_URL", "https://api.neoapi.ai")
