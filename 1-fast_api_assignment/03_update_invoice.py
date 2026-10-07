from fastapi import APIRouter, HTTPException
from data_store import invoice_list, save_invoices
from models import Invoice

router = APIRouter()
@router.put('/invoices/{invoice_id}')
def update_invoice(invoice_id: int, invoice: Invoice):
    for i, existing in enumerate(invoice_list):
        if existing['id'] == invoice_id:
            invoice_list[i] = invoice.model_dump()
            invoice_list[i]['id'] = invoice_id
            save_invoices()
            return invoice_list[i]
    raise HTTPException(status_code=404, detail="Invoice not found")