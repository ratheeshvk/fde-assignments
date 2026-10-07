from fastapi import APIRouter
from data_store import invoice_list

router = APIRouter()


@router.get("/invoices")
def get_invoices():
    return invoice_list

from fastapi import APIRouter, HTTPException
from data_store import invoice_list
@router.get('/invoices/{invoice_id}')
def get_invoice(invoice_id: int):
    invoice = next((i for i in invoice_list if i['id'] == invoice_id), None)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice
