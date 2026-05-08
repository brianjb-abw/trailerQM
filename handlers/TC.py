import csv
import os
import re

import PyPDF2

from handlers.Freight3P import f_CB as freight


def proc_TC(pdf_path, csv_path):
    fname = os.path.basename(pdf_path)

    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        pages_text = [page.extract_text() for page in reader.pages]

    vin_re = re.compile(r'\b1XN[A-Z0-9]{13,15}\b')
    price_re = re.compile(r'\b(\d{1,3},\d{3}\.\d{2})\b')
    dim_re = re.compile(r'\b(\d+)X(\d+)\b')

    items = []
    invoice_total = None

    for page_text in pages_text:
        lines = page_text.split('\n')

        if invoice_total is None:
            m = re.search(r'\$(\d{1,3},\d{3}\.\d{2})', page_text)
            if m:
                invoice_total = float(m.group(1).replace(',', ''))

        for i, line in enumerate(lines):
            vin_matches = list(vin_re.finditer(line))

            if not vin_matches:
                if 'VIN#' in line:
                    next_line = lines[i + 1] if i + 1 < len(lines) else ''
                    if not vin_re.search(next_line):
                        print(f"  WARNING ({fname}): VIN# label found but no valid 1XN VIN nearby")
                continue

            if len(vin_matches) != 1:
                print(f"  WARNING ({fname}): Expected 1 VIN on line, found {len(vin_matches)}")
                vin = ''
                after_vin = ''
            else:
                vin = vin_matches[0].group()
                after_vin = line[vin_matches[0].end():]

            # Cost: after VIN on same line, else on previous line
            price_hits = price_re.findall(after_vin)
            if price_hits:
                cost = float(price_hits[0].replace(',', ''))
            else:
                prev = lines[i - 1] if i > 0 else ''
                price_hits = price_re.findall(prev)
                if price_hits:
                    cost = float(price_hits[0].replace(',', ''))
                else:
                    print(f"  WARNING ({fname}): No price found for VIN {vin or '(unknown)'}")
                    cost = 0.0

            # Description: nearest prior line containing a WxL dimension
            desc = ''
            for j in range(i - 1, -1, -1):
                if dim_re.search(lines[j]):
                    desc = lines[j].strip()
                    break
            if not desc:
                print(f"  WARNING ({fname}): No description found for VIN {vin or '(unknown)'}")

            # Strip any leading non-alpha characters (e.g. invoice total bleeding onto same line)
            desc = re.sub(r'^[^A-Z]+', '', desc)

            dim_match = dim_re.search(desc)
            width = dim_match.group(1) if dim_match else ''
            length = dim_match.group(2) if dim_match else ''

            items.append((vin, width, length, desc, '', cost))

    item_total = sum(item[5] for item in items)

    if invoice_total is not None and abs(item_total - invoice_total) > 0.01:
        print(f"  WARNING ({fname}): Cost check failed — items ${item_total:,.2f}, invoice total ${invoice_total:,.2f}")

    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f)
        for item in items:
            writer.writerow([item[0], item[1], item[2], item[3], item[4], f"{item[5]:.2f}"])
        writer.writerow([])
        writer.writerow(['Invoice Total', f"{item_total:,.2f}"])
        writer.writerow(['3P Freight', f"{freight:,.2f}"])
        writer.writerow(['Load Total', f"{item_total + freight:,.2f}"])

    return len(items), item_total
