import os
import fitz  # PyMuPDF

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "sample_data")
os.makedirs(SAMPLE_DIR, exist_ok=True)

# 1. Purchase Order CSV
po_csv_content = """SKU,Item Description,Qty Ordered,Unit,Unit Price,Total Price
SKU-HUB-07,USB-C Hub 7-in-1 Aluminum Dock,100,each,12.00,1200.00
SKU-CAB-02,Braided USB-C to Lightning Cable 2M Black,200,each,3.50,700.00
SKU-CHG-65,65W GaN Fast Wall Charger Dual Port,100,each,14.50,1450.00
SKU-MNT-MAG,Magnetic Car Phone Mount with Qi Wireless,50,each,8.00,400.00
SKU-EAR-PRO,True Wireless Earbuds with ANC Case,80,each,22.00,1760.00
"""

with open(os.path.join(SAMPLE_DIR, "sample_po_shenzhen_apex.csv"), "w", encoding="utf-8") as f:
    f.write(po_csv_content)

# 2. Historical Prices CSV
hist_csv_content = """Date,Supplier,SKU,Description,Unit,Historical Unit Price
2026-01-15,Shenzhen Apex Electronics Co.,SKU-HUB-07,USB-C Hub 7-in-1,each,12.00
2026-02-15,Shenzhen Apex Electronics Co.,SKU-HUB-07,USB-C Hub 7-in-1,each,12.00
2026-03-15,Shenzhen Apex Electronics Co.,SKU-HUB-07,USB-C Hub 7-in-1,each,12.00
2026-01-15,Shenzhen Apex Electronics Co.,SKU-MNT-MAG,Magnetic Car Phone Mount,each,8.00
2026-02-15,Shenzhen Apex Electronics Co.,SKU-MNT-MAG,Magnetic Car Phone Mount,each,8.00
2026-03-15,Shenzhen Apex Electronics Co.,SKU-MNT-MAG,Magnetic Car Phone Mount,each,8.00
"""

with open(os.path.join(SAMPLE_DIR, "sample_historical_purchases.csv"), "w", encoding="utf-8") as f:
    f.write(hist_csv_content)

# 3. Create PDF Invoice using PyMuPDF
doc = fitz.open()
page = doc.new_page(width=612, height=792)  # US Letter

# Draw text
p1 = fitz.Point(50, 60)
page.insert_text(p1, "Shenzhen Apex Electronics Co., Ltd.", fontsize=18, fontname="helv", color=(0.1, 0.2, 0.5))

page.insert_text(fitz.Point(50, 85), "High-Tech Industrial Park, Nanshan District, Shenzhen, China", fontsize=9, fontname="helv")
page.insert_text(fitz.Point(50, 98), "billing@apexelectronics.sz | Tel: +86-755-88992211", fontsize=9, fontname="helv")

page.insert_text(fitz.Point(400, 60), "COMMERCIAL INVOICE", fontsize=14, fontname="helv")
page.insert_text(fitz.Point(400, 80), "Invoice #: INV-8891", fontsize=10, fontname="helv")
page.insert_text(fitz.Point(400, 95), "Date: 2026-10-12", fontsize=10, fontname="helv")
page.insert_text(fitz.Point(400, 110), "Ref PO #: PO-1042", fontsize=10, fontname="helv")
page.insert_text(fitz.Point(400, 125), "Currency: USD", fontsize=10, fontname="helv")

page.insert_text(fitz.Point(50, 140), "Billed To: TechVault E-Commerce LLC", fontsize=10, fontname="helv")
page.insert_text(fitz.Point(50, 155), "Warehouse Bay 4, Seattle, WA 98101, USA", fontsize=9, fontname="helv")

# Table Header
y = 190
page.insert_text(fitz.Point(50, y), "SKU / Description", fontsize=9, fontname="helv")
page.insert_text(fitz.Point(320, y), "Qty", fontsize=9, fontname="helv")
page.insert_text(fitz.Point(370, y), "Unit", fontsize=9, fontname="helv")
page.insert_text(fitz.Point(430, y), "Unit Price", fontsize=9, fontname="helv")
page.insert_text(fitz.Point(510, y), "Total (USD)", fontsize=9, fontname="helv")

# Table items (with intentional discrepancies)
items = [
    ("SKU-HUB-07", "Type C Dock 7P Aluminum (USB-C 7-in-1)", "100", "each", "$13.20", "$1,320.00"),
    ("SKU-CAB-02", "Braided Type-C to Lightning 2M Black", "240", "each", "$3.50", "$840.00"),
    ("SKU-CHG-65", "65W GaN Wall Charger Dual USB", "100", "each", "$14.50", "$1,450.00"),
    ("SKU-MNT-MAG", "Mag Car Phone Qi Wireless Mount", "50", "each", "$9.60", "$480.00"),
    ("SKU-CHG-65", "65W GaN Wall Charger Dual USB", "100", "each", "$14.50", "$1,450.00")
]

y = 215
for sku, desc, qty, unit, price, total in items:
    page.insert_text(fitz.Point(50, y), f"{sku}  {desc}", fontsize=9, fontname="helv")
    page.insert_text(fitz.Point(320, y), qty, fontsize=9, fontname="helv")
    page.insert_text(fitz.Point(370, y), unit, fontsize=9, fontname="helv")
    page.insert_text(fitz.Point(430, y), price, fontsize=9, fontname="helv")
    page.insert_text(fitz.Point(510, y), total, fontsize=9, fontname="helv")
    y += 24

y += 20
page.insert_text(fitz.Point(400, y), "Subtotal: $5,540.00", fontsize=10, fontname="helv")
y += 18
page.insert_text(fitz.Point(400, y), "Discount: -$680.00", fontsize=10, fontname="helv")
y += 18
page.insert_text(fitz.Point(400, y), "Total Amount: $4,860.00", fontsize=12, fontname="helv")

pdf_path = os.path.join(SAMPLE_DIR, "sample_invoice_apex.pdf")
doc.save(pdf_path)
print(f"Generated sample files in {SAMPLE_DIR}")
