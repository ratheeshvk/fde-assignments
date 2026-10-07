from fastapi import APIRouter
from data_store import invoice_list, save_invoices
from models import Invoice

router = APIRouter()

@router.post('/invoices')
def create_invoice(invoice: Invoice):
    invoice_data = invoice.model_dump()
    invoice_data['id'] = len(invoice_list) + 1
    invoice_list.append(invoice_data)
    save_invoices()
    return invoice_data