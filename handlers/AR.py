import csv
import os
import re

import PyPDF2

from handlers.Freight3P import f_CL as freight


def proc_AR(pdf_path, csv_path):
    fname = os.path.basename(pdf_path)

    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = '\n'.join(page.extract_text() for page in reader.pages)

    vin_re = re.compile(r'#:\s*([A-Z0-9]{17})')
    color_re = re.compile(r'COLOR:\s*([A-Z]+)')
    dim_re = re.compile(r'(\d+(?:\.\d+)?)X(\d+)')
    balance_re = re.compile(r'BALANCE DUE\s*\$?([\d,]+\.\d{2})')

    # Each item ends with "Subtotal: X.XX"; split to pair block text with its cost
    parts = re.split(r'Subtotal:\s*([\d,]+\.\d{2})', text)

    items = []
    i = 0
    while i + 1 < len(parts):
        block_text = parts[i]
        cost_str = parts[i + 1]
        i += 2

        vin_matches = vin_re.findall(block_text)
        if not vin_matches:
            continue  # header or footer block

        if len(vin_matches) != 1:
            print(f"  WARNING ({fname}): Expected 1 VIN in item block, found {len(vin_matches)}")
            vin = ''
        else:
            vin = vin_matches[0]

        cost = float(cost_str.replace(',', ''))

        # Description: line where "ARISING" is followed by a dimension (avoids "ARISING CARGO, LLC")
        # The wrap continuation is concatenated onto the next line — extract only the alpha part
        desc = ''
        lines = [line.strip() for line in block_text.split('\n')]
        for j, line in enumerate(lines):
            if re.search(r'ARISING\s+[\d.]', line):
                desc_start = line[line.index('ARISING'):].strip()
                if j + 1 < len(lines):
                    alpha_match = re.match(r'^([A-Z ]+)', lines[j + 1])
                    continuation = alpha_match.group(1).strip() if alpha_match else ''
                    desc = (desc_start + ' ' + continuation).strip() if continuation else desc_start
                else:
                    desc = desc_start
                break
        if not desc:
            print(f"  WARNING ({fname}): No description found for VIN {vin or '(unknown)'}")

        dim_match = dim_re.search(desc)
        width = dim_match.group(1) if dim_match else ''
        length = dim_match.group(2) if dim_match else ''

        color_match = color_re.search(block_text)
        color = color_match.group(1) if color_match else ''

        items.append((vin, width, length, desc, color, cost))

    item_total = sum(item[5] for item in items)

    balance_match = balance_re.search(text)
    if balance_match:
        balance = float(balance_match.group(1).replace(',', ''))
        if abs(item_total - balance) > 0.01:
            print(f"  WARNING ({fname}): Cost check failed — items ${item_total:,.2f}, balance due ${balance:,.2f}")

    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f)
        for item in items:
            writer.writerow([item[0], item[1], item[2], item[3], item[4], f"{item[5]:.2f}"])
        writer.writerow([])
        writer.writerow(['Invoice Total', f"{item_total:,.2f}"])
        writer.writerow(['3P Freight', f"{freight:,.2f}"])
        writer.writerow(['Load Total', f"{item_total + freight:,.2f}"])

    return len(items), item_total
