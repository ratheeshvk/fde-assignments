from fastapi import FastAPI

from model import Payments
from service import (
    add_payment,
    delete_payments_by_invoice_id,
    get_all_payments,
    get_payments_by_invoice_id,
    run_pipeline,
    update_payment_amount,
)

app = FastAPI()

@app.get("/payments")
def get_payments():
    return get_all_payments()

@app.get("/payments/{invoice_id}")
def get_payment(invoice_id: str):
    return get_payments_by_invoice_id(invoice_id)

@app.post("/payments")
def create_payment(payment: Payments):
    return add_payment(payment)

@app.put("/payments/{invoice_id}")
def update_payment(invoice_id: str, payment: Payments):
    return update_payment_amount(invoice_id, payment)

@app.delete("/payments/{invoice_id}")
def delete_payment(invoice_id: str):
    return delete_payments_by_invoice_id(invoice_id)

@app.post("/clean-pipeline")
def clean_invoices():
    return run_pipeline()
