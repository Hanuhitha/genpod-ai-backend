from pydantic import BaseModel, field_validator


class QueryList(BaseModel):
    req_queries: list[str]

    @field_validator('req_queries')
    @classmethod
    def check_req_queries_items(cls, v):
        if not isinstance(v, list):
            raise ValueError('QueryList must be a list')
        for item in v:
            if not isinstance(item, str):
                raise ValueError('Each req_queries item must be a string')
        return v
