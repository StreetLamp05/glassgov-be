import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "sqlite:///dev.db"  # fallback if someone runs without Compose
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    OPENSTATES_API_KEY = os.getenv("OPENSTATES_API_KEY", "")
    FBI_API_KEY = os.getenv("FBI_API_KEY", "")
    CENSUS_API_KEY = os.getenv("CENSUS_API_KEY", "")

    LLM_MOCK = os.getenv("LLM_MOCK", "1") == "1"


    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
