import os
import csv
from pathlib import Path
from dotenv import load_dotenv

from handlers.AR import proc_AR
from handlers.BB import proc_BB
from handlers.LT import proc_LT
from handlers.TC import proc_TC

load_dotenv()


HANDLERS = {
    'AR': proc_AR,
    'BB': proc_BB,
    'LT': proc_LT,
    'TC': proc_TC,
}


def main():
    BASE_PATH = os.getenv("BASE_PATH")
    in_dir = "tm_IN"
    out_dir = "tm_OUT"
    out_file = "tm_data.csv"

    t_in = Path(os.path.join(BASE_PATH, in_dir))
    csv_path = Path(os.path.join(BASE_PATH, out_dir, out_file))

    with open(csv_path, 'w', newline='') as f:
        csv.writer(f).writerow(['VIN', 'W', 'L', 'Description', 'Color', 'Cost'])

    for pdf_file in sorted(t_in.glob('*.pdf')):
        print(f"filename: {pdf_file.name}")
        prefix = pdf_file.stem[:2].upper()
        handler = HANDLERS.get(prefix)
        if handler is None:
            print(f"No handler for manufacturer prefix '{prefix}' ({pdf_file.name})")
            continue

        count, total = handler(str(pdf_file), csv_path)
        print(f"{pdf_file.name} complete:\n  trailers/mowers processed: {count}\n  total cost: ${total:,.2f}\n")


if __name__ == "__main__":
    main()
