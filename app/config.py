# Модель лоя получения настроек из .env

import ipaddress
from typing import Optional, Union

from pydantic import Field, SecretStr, EmailStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigBase(BaseSettings):

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
        json_encoders = {
            ipaddress.IPv4Address: lambda v: str(v)
        }
    )


class Project(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="project_")

    name: Optional[str] = ""
    version: Optional[str] = ""
    info: Optional[str] = ""
    root: str


class Author(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="author_")

    tg_id: Optional[int] = None
    tg_username: Optional[str] = ""
    email: Optional[Union[EmailStr, str]] = ""


class ApiConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="api_")

    ip: Optional[str] = ""              # ip на API
    host: Optional[str] = ""            # ip на API
    port: Optional[int] = None          # Порт для API
    root: Optional[str] = ""            # Путь к директории API
    secret: Optional[SecretStr] = ""    # "секрет" для безопасности API
    version: Optional[str] = ""         # Версия API

    full_path: Optional[str] = ""       # Полный путь к API
    path: Optional[str] = ""            # Путь после ip и порта
    docs: Optional[str] = ""            # Полный путь к swagger






# class DatabaseConfig(ConfigBase):
#     model_config = SettingsConfigDict(env_prefix="db_")
#
#     ip: str
#     port: int
#     name: SecretStr
#     user: SecretStr
#     password: SecretStr
#
#     dialect: str
#     async_dialect: str
#     driver: Optional[str] = ""
#
#     def pre_conn(self):  # Подготавливаем строку для создания conn
#         return (
#             f"{self.user.get_secret_value()}:{self.password.get_secret_value()}@"
#             f"{self.ip}:{self.port}/{self.name.get_secret_value()}{self.driver}"
#         )
#
#     @computed_field
#     def async_conn(self) -> SecretStr:
#         return SecretStr(f"{self.async_dialect}://{self.pre_conn()}")
#
#     @computed_field
#     def conn(self) -> SecretStr:
#         return SecretStr(f"{self.dialect}://{self.pre_conn()}")





class Config(BaseSettings):
    model_config = SettingsConfigDict()

    project: Project = Field(default_factory=Project)
    author: Author = Field(default_factory=Author)
    api: ApiConfig = Field(default_factory=ApiConfig)


    @classmethod
    def load(cls) -> "Config":
        return cls()

    def set_api_path(self):
        port = f":{self.api.port}" if self.api.port else ""
        self.api.full_path = self.api.ip + port + self.project.root + self.api.root + self.api.version
        self.api.path = self.project.root + self.api.root + self.api.version


    def set_api_docs(self):
        port = f":{self.api.port}" if self.api.port else ""
        self.api.docs = self.api.ip + port + self.project.root + self.api.root + self.api.version + "/docs#"


    def __init__(self, **data):
        super().__init__(**data)
        self.set_api_path()
        self.set_api_docs()



CONFIG = Config()
