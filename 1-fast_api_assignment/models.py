from pydantic import BaseModel,Field

class Invoice(BaseModel):
    id: int
    amount: float = Field(gt=0)
    status: str