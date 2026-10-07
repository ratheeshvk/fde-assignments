from fastapi import FastAPI
from importlib import import_module

get_invoices_router = import_module("01_get_invoices").router
create_invoice_router = import_module("02_create_invoice").router
update_invoice_router = import_module("03_update_invoice").router
delete_invoice_router = import_module("04_delete_invoice").router

app = FastAPI()
app.include_router(get_invoices_router)
app.include_router(create_invoice_router)
app.include_router(update_invoice_router)
app.include_router(delete_invoice_router)
