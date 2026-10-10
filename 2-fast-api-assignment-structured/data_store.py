import json
from pathlib import Path

_DATA_FILE = Path(__file__).with_name("data_store.json")

with _DATA_FILE.open() as f:
    _data = json.load(f)

invoice_list = _data["invoices"]
payment_list = _data["payments"]

def save_invoices():
    with _DATA_FILE.open("w") as f:
        json.dump(
            {"invoices": invoice_list, "payments": payment_list},
            f,
            indent=4,
        )
