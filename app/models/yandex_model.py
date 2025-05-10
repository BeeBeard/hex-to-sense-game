from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic import Field
from pydantic import computed_field

load_dotenv()


class Synonym(BaseModel):
    text: str
    pos: str
    fr: int


class Translation(BaseModel):
    text: str
    pos: str
    fr: int
    # syn: Optional[List[Synonym]]


class Definition(BaseModel):
    text: str
    # pos: str
    # tr: List[Translation]


class YaAnswer(BaseModel):
    head: Optional[dict] = None
    nmt_code: Optional[int] = None
    code: Optional[int] = None
    def_: List[Definition] = Field(alias='def')

    @computed_field
    def is_exist(self) -> bool:
        if self.def_:
            return True
        return False

    class Config:
        validate_by_name = True  # Разрешаем обращаться по псевдониму 'def'
