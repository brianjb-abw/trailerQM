import csv
from pathlib import Path

from handlers.AR import proc_AR
from handlers.BB import proc_BB
from handlers.LT import proc_LT
from handlers.TC import proc_TC

HANDLERS = {
    'AR': proc_AR,
    'BB': proc_BB,
    'LT': proc_LT,
    'TC': proc_TC,
}


def main():
    t_in = Path('T_IN')
    csv_path = str(Path('T_OUT') / 'trailer_data.csv')

    with open(csv_path, 'w', newline='') as f:
        csv.writer(f).writerow(['VIN', 'W', 'L', 'Description', 'Color', 'Cost'])

    for pdf_file in sorted(t_in.glob('*.pdf')):
        prefix = pdf_file.stem[:2].upper()
        handler = HANDLERS.get(prefix)
        if handler is None:
            print(f"No handler for manufacturer prefix '{prefix}' ({pdf_file.name})")
            continue

        count, total = handler(str(pdf_file), csv_path)
        print(f"{pdf_file.name} complete:\n  trailers/mowers processed: {count}\n  total cost: ${total:,.2f}\n")


if __name__ == "__main__":
    main()
