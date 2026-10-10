from pydantic import BaseModel, Field

class Invoice(BaseModel):
    invoice_id: str
    vendor: str
    amount: float | None = None
    status: str
    date: str

class Payments(BaseModel):
    invoice_id: str = Field(min_length=1)
    paid: float = Field(gt=0)
