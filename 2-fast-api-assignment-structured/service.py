from fastapi import HTTPException

import repository
from model import Payments

def get_all_payments():
    return repository.get_all_payments()

def get_payments_by_invoice_id(invoice_id: str):
    payments = repository.get_payments_by_invoice_id(invoice_id)
    if not payments:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payments

def add_payment(payment: Payments):
    if repository.get_invoice_by_id(payment.invoice_id) is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return repository.add_payment(payment)

def update_payment_amount(invoice_id: str, payment: Payments):
    if payment.invoice_id != invoice_id:
        raise HTTPException(status_code=400, detail="Invoice id does not match")
    matches = repository.get_payments_by_invoice_id(invoice_id)
    if not matches:
        raise HTTPException(status_code=404, detail="Payment not found")
    if len(matches) > 1:
        raise HTTPException(status_code=409, detail="Multiple payments for this invoice")
    return repository.update_payment_amount(invoice_id, payment.paid)

def delete_payments_by_invoice_id(invoice_id: str):
    removed = repository.delete_payments_by_invoice_id(invoice_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Payment not found")
    return removed

def invoice_key(invoice):
    return (
        invoice["invoice_id"],
        invoice["vendor"],
        invoice["amount"],
        invoice["status"],
        invoice["date"],
    )

def normalize_invoices(invoices):
    missing_amount_indexes = []
    for index in range(len(invoices)):
        invoices[index]["vendor"] = invoices[index]["vendor"].strip().title()
        invoices[index]["status"] = invoices[index]["status"].strip().upper()
        if invoices[index]["amount"] is None:
            missing_amount_indexes.append(index)
            print(
                f"Amount is None at index {index}: {invoices[index]['invoice_id']}"
            )
    return missing_amount_indexes

def remove_exact_duplicates(invoices):
    exact_dupes = {}
    first_index = {}
    for index in range(len(invoices)):
        key = invoice_key(invoices[index])
        if key in first_index:
            exact_dupes.setdefault(key, [first_index[key]]).append(index)
        else:
            first_index[key] = index

    indexes_to_remove = []
    for indexes in exact_dupes.values():
        indexes_to_remove.extend(indexes[1:])
    for index in sorted(indexes_to_remove, reverse=True):
        del invoices[index]
    return exact_dupes

def find_suspected_duplicates(invoices):
    groups = {} # Creating a group with same vendor, amount, and date
    for invoice in invoices:
        key = (invoice["vendor"], invoice["amount"], invoice["date"])
        groups.setdefault(key, []).append(invoice)

    pairs = []
    for group in groups.values():
        first = group[0]
        for other in group[1:]:
            if other["invoice_id"] == first["invoice_id"]:
                continue
            pair = f"({other['invoice_id']} ~ {first['invoice_id']})"
            pairs.append(pair)
            print(pair)
    return pairs

def apply_credit_notes(invoices):
    pairs = []
    for negative_index, negative_invoice in enumerate(invoices):
        negative_amount = negative_invoice["amount"]
        if negative_amount is None or negative_amount >= 0 or negative_invoice["status"] == "CANCELLED":
            continue

        matched_positive_index = None
        for positive_index, positive_invoice in enumerate(invoices):
            positive_amount = positive_invoice["amount"]
            if positive_amount is None or positive_amount <= 0 or positive_invoice["status"] == "CANCELLED":
                continue
            same_vendor = positive_invoice["vendor"] == negative_invoice["vendor"]
            same_amount = positive_amount == abs(negative_amount)
            if same_vendor and same_amount:
                matched_positive_index = positive_index
                break

        if matched_positive_index is None:
            print(f"Credit note {negative_invoice['invoice_id']} at index {negative_index} has no partner")
            continue

        negative_invoice["status"] = "CANCELLED"
        invoices[matched_positive_index]["status"] = "CANCELLED"
        pair = f"{negative_index} <-> {matched_positive_index}"
        pairs.append(pair)
        print(pair)
    return pairs

def reconcile_payments(invoices, payments):
    paid_by_invoice = {}
    for payment in payments:
        invoice_id = payment["invoice_id"]
        paid_by_invoice[invoice_id] = paid_by_invoice.get(invoice_id, 0) + payment["paid"]

    invoice_ids = {invoice["invoice_id"] for invoice in invoices}
    rows = []
    for index in range(len(invoices)):
        invoice = invoices[index]
        if invoice["amount"] is None or invoice["status"] == "CANCELLED":
            print(
                "Excluded from totals:"
                f" index {index} {invoice['invoice_id']}"
                f" amount {invoice['amount']} status {invoice['status']}"
            )
            continue
        paid = paid_by_invoice.get(invoice["invoice_id"], 0)
        balance = invoice["amount"] - paid
        row = {
            "invoice_id": invoice["invoice_id"],
            "vendor": invoice["vendor"],
            "amount": invoice["amount"],
            "paid": paid,
            "balance": balance,
        }
        rows.append(row)
        print(
            f"{row['invoice_id']} | {row['vendor']} | amount {row['amount']}"
            f" | paid {row['paid']} | balance {row['balance']}"
        )

    for invoice_id, paid in paid_by_invoice.items():
        if invoice_id not in invoice_ids:
            print(f"Unmatched payment {invoice_id} paid {paid}")
    return rows

def run_pipeline():
    print("0) ======== Get all invoices and payments")
    invoices = repository.get_all_invoices()
    payments = repository.get_all_payments()

    print("1) Normalize")
    missing_amount_indexes = normalize_invoices(invoices)

    print("2) ========Exact duplicates")
    exact_dupes = remove_exact_duplicates(invoices)
    for key, indexes in exact_dupes.items():
        print(f"{key[0]} indexes {indexes}")

    print("3) ======== Suspected duplicates")
    suspected_duplicates = find_suspected_duplicates(invoices)

    print("4) ======== Credit notes")
    credit_notes = apply_credit_notes(invoices)

    print("5) Reconcile payments")
    reconciliation = reconcile_payments(invoices, payments)
    invoice_ids = {invoice["invoice_id"] for invoice in invoices}
    paid_by_invoice = {}
    for payment in payments:
        invoice_id = payment["invoice_id"]
        paid_by_invoice[invoice_id] = paid_by_invoice.get(invoice_id, 0) + payment["paid"]
    unmatched_payments = [
        {"invoice_id": invoice_id, "paid": paid}
        for invoice_id, paid in paid_by_invoice.items()
        if invoice_id not in invoice_ids
    ]
    repository.save_invoices()
    return {
        "missing_amount_indexes": missing_amount_indexes,
        "exact_duplicates": [
            {"invoice_id": key[0], "indexes": indexes}
            for key, indexes in exact_dupes.items()
        ],
        "suspected_duplicates": suspected_duplicates,
        "credit_notes": credit_notes,
        "reconciliation": reconciliation,
        "unmatched_payments": unmatched_payments,
        "invoices": invoices,
    }

if __name__ == "__main__":
    run_pipeline()
