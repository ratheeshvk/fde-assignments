import json
from pathlib import Path

_DATA_FILE = Path(__file__).with_name("data_store.json")

with _DATA_FILE.open() as f:
    invoice_list = json.load(f)

def save_invoices():
    with _DATA_FILE.open("w") as f:
        json.dump(invoice_list, f, indent=4)