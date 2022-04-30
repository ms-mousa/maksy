from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "maksy-beta"
    pinecone_key: str

    class Config:
        env_file = ".env"
