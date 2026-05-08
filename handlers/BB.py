import csv
import os
import re

import PyPDF2


def proc_BB(pdf_path, csv_path):
    fname = os.path.basename(pdf_path)

    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = '\n'.join(page.extract_text() for page in reader.pages)

    lines = [line.strip() for line in text.split('\n')]
    serial_re = re.compile(r'^[A-Z0-9]{17,19}$')
    dollar_re = re.compile(r'\$([\d,]+\.\d{2})')
    total_re = re.compile(r'Total:\s*\$?([\d,]+\.\d{2})')

    items = []
    freight = 0.0
    invoice_total = None

    total_match = total_re.search(text)
    if total_match:
        invoice_total = float(total_match.group(1).replace(',', ''))

    for i, line in enumerate(lines):
        # S&H line: extract as freight (3rd dollar amount = extension)
        if 'S&H' in line and 'SHIPPING' in line:
            sh_dollars = dollar_re.findall('\n'.join(lines[i + 1:i + 10]))
            if len(sh_dollars) >= 3:
                freight = float(sh_dollars[2].replace(',', ''))
            else:
                print(f"  WARNING ({fname}): Could not determine S&H freight amount")
            continue

        if line != 'LOT DETAIL:':
            continue

        # Serial: line immediately after LOT DETAIL:
        serial_line = lines[i + 1] if i + 1 < len(lines) else ''
        if not serial_re.match(serial_line):
            print(f"  WARNING ({fname}): Unexpected value at LOT DETAIL: {serial_line!r}")
            serial = ''
        else:
            serial = serial_line

        # Description: two lines immediately above LOT DETAIL:
        desc_line1 = lines[i - 2] if i >= 2 else ''
        desc_line2 = lines[i - 1] if i >= 1 else ''
        desc = (desc_line1 + ' ' + desc_line2).strip()

        # Price: 2nd dollar amount after serial (index 0 = list, index 1 = price)
        after_serial = '\n'.join(lines[i + 2:i + 10])
        dollar_hits = dollar_re.findall(after_serial)
        if len(dollar_hits) >= 2:
            cost = float(dollar_hits[1].replace(',', ''))
        else:
            print(f"  WARNING ({fname}): No price found for serial {serial or '(unknown)'}")
            cost = 0.0

        items.append((serial, '', '', desc, '', cost))

    item_total = sum(item[5] for item in items)

    if invoice_total is not None and abs(item_total + freight - invoice_total) > 0.01:
        print(f"  WARNING ({fname}): Cost check failed — items ${item_total:,.2f} + freight ${freight:,.2f} = ${item_total + freight:,.2f}, invoice total ${invoice_total:,.2f}")

    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f)
        for item in items:
            writer.writerow([item[0], item[1], item[2], item[3], item[4], f"{item[5]:.2f}"])
        writer.writerow([])
        writer.writerow(['Subtotal', f"{item_total:,.2f}"])
        writer.writerow(['Freight', f"{freight:,.2f}"])
        writer.writerow(['Invoice Total', f"{item_total + freight:,.2f}"])

    return len(items), item_total
