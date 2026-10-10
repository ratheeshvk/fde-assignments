from data_store import invoice_list, payment_list, save_invoices
from model import Payments

__all__ = [
    "get_all_invoices",
    "get_invoice_by_id",
    "get_all_payments",
    "get_payments_by_invoice_id",
    "add_payment",
    "update_payment_amount",
    "delete_payments_by_invoice_id",
    "save_invoices",
]

def get_all_invoices():
    return invoice_list

def get_invoice_by_id(invoice_id: str):
    return next(
        (invoice for invoice in invoice_list if invoice["invoice_id"] == invoice_id),
        None,
    )

def get_all_payments():
    return payment_list

def get_payments_by_invoice_id(invoice_id: str):
    return [
        payment for payment in payment_list if payment["invoice_id"] == invoice_id
    ]

def add_payment(payment: Payments):
    payment_data = payment.model_dump()
    payment_list.append(payment_data)
    save_invoices()
    return payment_data

def update_payment_amount(invoice_id: str, paid: float):
    for payment in payment_list:
        if payment["invoice_id"] == invoice_id:
            payment["paid"] = paid
            save_invoices()
            return payment
    return None

def delete_payments_by_invoice_id(invoice_id: str):
    removed = []
    for index in range(len(payment_list) - 1, -1, -1):
        if payment_list[index]["invoice_id"] == invoice_id:
            removed.append(payment_list.pop(index))
    if removed:
        save_invoices()
    removed.reverse()
    return removed
