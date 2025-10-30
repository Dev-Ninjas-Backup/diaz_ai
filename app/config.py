from pydantic_settings import BaseSettings
import yaml


class Settings(BaseSettings):
    OPENAI_API_KEY : str
    # MONGODB_URI : str
    # DB_NAME : str
    # POSTGRES_URI : str
    # NEONDB_NAME : str


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()



class Config:

    def __init__(self):
        pass

    def load_yaml(self, file_path):
        with open(file_path, "r") as f:
            config = yaml.safe_load(f)
        return config


configs = Config().load_yaml("config/config.yaml")
