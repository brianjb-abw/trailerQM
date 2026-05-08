import csv
import os
import re

import PyPDF2


def proc_LT(pdf_path, csv_path):
    fname = os.path.basename(pdf_path)

    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        pages_text = [page.extract_text() for page in reader.pages]

    vin_re = re.compile(r'^[A-Z0-9]{15,20}$')
    dim_re = re.compile(r'(\d+)"\s*x\s*(\d+)\'')
    price_re = re.compile(r'EACH\s+\d+\s+([\d,]+\.\d{2})')
    freight_re = re.compile(r'Freight:\s*([\d,]+\.\d{2})')
    total_re = re.compile(r'Total:\s*([\d,]+\.\d{2})')

    items = []
    freight = 0.0
    invoice_total = None

    for page_text in pages_text:
        lines = [line.strip() for line in page_text.split('\n')]

        # Capture freight and invoice total (present on final page)
        for line in lines:
            m = freight_re.search(line)
            if m:
                freight = float(m.group(1).replace(',', ''))
            m = total_re.search(line)
            if m:
                invoice_total = float(m.group(1).replace(',', ''))

        # VIN: PyPDF2 puts "SERIAL NO :" and "Special Instructions :" on one line;
        # the VIN appears on its own line immediately after
        vin = ''
        for i, line in enumerate(lines):
            if 'SERIAL NO' in line:
                for j in range(i + 1, min(i + 4, len(lines))):
                    if vin_re.match(lines[j]):
                        vin = lines[j]
                        break
                if not vin:
                    print(f"  WARNING ({fname}): SERIAL NO found but no valid VIN nearby")
                break
        if not vin:
            continue

        # Description and dimensions: first line matching the WxL format (e.g. 83" x 16')
        desc = ''
        dim_match = None
        for line in lines:
            dm = dim_re.search(line)
            if dm:
                desc = line
                dim_match = dm
                break
        if not desc:
            print(f"  WARNING ({fname}): No description found for VIN {vin}")

        # Strip the part number that PyPDF2 concatenates onto the end of the description line
        desc = re.sub(r'DL\d\S+', '', desc).strip()

        width = dim_match.group(1) if dim_match else ''
        length = dim_match.group(2) if dim_match else ''

        # Color: line immediately above "Road Service Program"
        color = ''
        for i, line in enumerate(lines):
            if 'Road Service Program' in line and i > 0:
                color = lines[i - 1]
                break
        if not color:
            print(f"  WARNING ({fname}): No color found for VIN {vin}")

        # Cost: Extension value from the "EACH" line
        cost = 0.0
        for line in lines:
            m = price_re.search(line)
            if m:
                cost = float(m.group(1).replace(',', ''))
                break
        if cost == 0.0:
            print(f"  WARNING ({fname}): No price found for VIN {vin}")

        items.append((vin, width, length, desc, color, cost))

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
