from fastapi import APIRouter, HTTPException
from data_store import invoice_list, save_invoices

router = APIRouter()

@router.delete('/invoices/{invoice_id}')
def delete_invoice(invoice_id: int):
    for i, invoice in enumerate(invoice_list):
        if invoice['id'] == invoice_id:
            removed_invoice = invoice_list.pop(i)
            save_invoices()
            return removed_invoice
    raise HTTPException(status_code=404, detail="Invoice not found")