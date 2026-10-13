import os
import json
import random

PRODUCTS = [
    {
        "canonical": "Blue nitrile gloves, large, 100 per box",
        "pack_qty": 100,
        "pack_unit": "box",
        "size": "large",
        "attributes": ["blue", "nitrile"],
        "variations": [
            "NITR GLOVE BLU LRG 100/BOX",
            "Nitrile Examination Gloves Blue L 100ct",
            "GLOVE NITRILE BLU LRG BX/100",
            "Blue Nitrile Medical Gloves Lrg (100 pk)",
            "GLV NITRILE BLUE LARGE 100/BX",
            "Nitrile Disp Gloves Blue L 100/Box",
            "BLU NITRILE GLOVE LRG 100 CT BX"
        ]
    },
    {
        "canonical": "Black nitrile gloves, medium, 100 per box",
        "pack_qty": 100,
        "pack_unit": "box",
        "size": "medium",
        "attributes": ["black", "nitrile"],
        "variations": [
            "NITR GLOVE BLK MED 100/BOX",
            "Nitrile Examination Gloves Black M 100ct",
            "GLOVE NITRILE BLK MED BX/100",
            "Black Nitrile Exam Gloves Med 100/bx",
            "GLV NITRILE BLACK MEDIUM 100/BX"
        ]
    },
    {
        "canonical": "Blue nitrile gloves, large, 200 per box",
        "pack_qty": 200,
        "pack_unit": "box",
        "size": "large",
        "attributes": ["blue", "nitrile"],
        "variations": [
            "NITR GLOVE BLU LRG 200/BOX",
            "Nitrile Examination Gloves Blue L 200ct",
            "GLOVE NITRILE BLU LRG BX/200",
            "Blue Nitrile Exam Gloves Large 200/bx (Econo Pack)"
        ]
    },
    {
        "canonical": "USB-C Hub, 7-in-1 Aluminum Dock with 100W Power Delivery",
        "pack_qty": 1,
        "pack_unit": "each",
        "size": None,
        "attributes": ["aluminum", "usb-c", "7-in-1", "100w-pd"],
        "variations": [
            "Type C Dock 7P w/ 100W PD",
            "7-in-1 USB C Hub Multiport Adapter Alum",
            "USB-C MULTIPORT ADPT 7P 100W",
            "Docking Station Type-C 7 Port 100W PD",
            "7in1 Type C Dongle Aluminum Gray",
            "HUB USBC 7-PORT ALUM 100W PD"
        ]
    },
    {
        "canonical": "Braided USB-C to Lightning Cable 2M Black",
        "pack_qty": 1,
        "pack_unit": "each",
        "size": "2m",
        "attributes": ["black", "braided", "usb-c", "lightning"],
        "variations": [
            "Braided Type C to Lightning 2M Black",
            "CBL USBC-LTG 2M NYLON BLK",
            "Type-C to Lightning Cable 6.6FT Braided Blk",
            "Braided C-to-Lightning Sync Cable 2 Meter Black",
            "Nylon Braided TypeC iPhone Cable 2M"
        ]
    },
    {
        "canonical": "65W GaN Fast Wall Charger Dual Port USB-C White",
        "pack_qty": 1,
        "pack_unit": "each",
        "size": None,
        "attributes": ["white", "65w", "gan", "dual-port", "usb-c"],
        "variations": [
            "65W GaN Dual USB Wall Adapter Wht",
            "CHG WALL 65W GAN 2-PORT TYPE-C WHT",
            "Fast Charger 65W GaN Dual Port USB-C White",
            "Power Adapter 65W GaN Dual Output Wht"
        ]
    },
    {
        "canonical": "Stainless steel kitchen shears, 8 inch heavy duty",
        "pack_qty": 1,
        "pack_unit": "each",
        "size": "8-inch",
        "attributes": ["stainless steel", "heavy duty"],
        "variations": [
            "SS KITCH SHEARS 8IN HD",
            "Kitchen Scissors 8\" Stainless Steel Heavy Duty",
            "8 Inch S/S Culinary Shears HD",
            "SHEAR KITCHEN STAINLESS 8\""
        ]
    },
    {
        "canonical": "Thermal receipt paper rolls, 3-1/8 x 230 ft, pack of 50",
        "pack_qty": 50,
        "pack_unit": "pack",
        "size": "3-1/8 x 230 ft",
        "attributes": ["thermal", "receipt paper"],
        "variations": [
            "THERM PAPER 3-1/8X230 50/PK",
            "POS Receipt Paper 3 1/8\" x 230' (Pack of 50)",
            "ROLL PAPER THERMAL 3.125X230 50PK",
            "Receipt Roll 3-1/8 x 230ft 50 rolls/case"
        ]
    },
    {
        "canonical": "Organic extra virgin olive oil, 5 liter tin",
        "pack_qty": 1,
        "pack_unit": "each",
        "size": "5 liter",
        "attributes": ["organic", "extra virgin", "olive oil"],
        "variations": [
            "EVOO ORG 5L TIN",
            "Extra Virgin Olive Oil Organic 5 Liters",
            "OIL OLIVE EV ORGANIC 5LTR CAN",
            "Org Extra Virgin Olive Oil 5L Metal Can"
        ]
    },
    {
        "canonical": "Heavy duty trash bags, 55 gallon, 100 per carton",
        "pack_qty": 100,
        "pack_unit": "carton",
        "size": "55 gallon",
        "attributes": ["heavy duty", "black", "plastic"],
        "variations": [
            "CAN LINER 55GAL HD 100/CTN",
            "Trash Can Liners 55 Gallon Heavy Duty (100/box)",
            "BAG TRASH 55 GAL 100CT CTN",
            "55 Gal Contractor Trash Bags 100 Pack"
        ]
    },
    {
        "canonical": "Corrugated shipping boxes, 12x12x12 inch, bundle of 25",
        "pack_qty": 25,
        "pack_unit": "bundle",
        "size": "12x12x12 inch",
        "attributes": ["corrugated", "kraft", "cube"],
        "variations": [
            "BOX CORR 12X12X12 25/BDL",
            "Shipping Box 12\" Cube 25 Count Bundle",
            "12x12x12 Kraft Box Bdl of 25",
            "BOXES SHIPPING 12X12X12 BUNDLE/25"
        ]
    },
    {
        "canonical": "Clear packing tape with dispenser, 2 inch x 55 yard, pack of 6",
        "pack_qty": 6,
        "pack_unit": "pack",
        "size": "2 in x 55 yd",
        "attributes": ["clear", "packing tape", "dispenser"],
        "variations": [
            "TAPE PACK CLR 2X55YD W/DISP 6PK",
            "Clear Packaging Tape 2\"x55yd 6 Roll Pack",
            "SEALING TAPE CLEAR 2IN 6/PK DISPENSER",
            "Carton Sealing Tape Clear 2x55 6pk"
        ]
    },
    {
        "canonical": "Magnetic car phone mount with Qi wireless charging 15W",
        "pack_qty": 1,
        "pack_unit": "each",
        "size": None,
        "attributes": ["magnetic", "qi wireless", "15w", "car mount"],
        "variations": [
            "Mag Car Phone Qi Wireless Mount 15W",
            "MNT MAG WIRELESS CAR CHG 15W",
            "Magnetic Wireless Auto Air Vent Charger 15W",
            "Auto Phone Mount MagSafe Compat 15W Qi"
        ]
    },
    {
        "canonical": "True wireless earbuds with active noise cancellation and wireless charging case",
        "pack_qty": 1,
        "pack_unit": "each",
        "size": None,
        "attributes": ["true wireless", "anc", "bluetooth", "charging case"],
        "variations": [
            "TWS ANC Earbuds w/ Qi Case",
            "EARBUDS TWS ANC ACTIVE NOISE CANCEL BLK",
            "True Wireless Stereo Earphones w/ ANC",
            "Bluetooth 5.3 Earbuds ANC Case Black"
        ]
    },
    {
        "canonical": "Grade 5 hex cap screws, 1/4-20 x 1 inch zinc plated, box of 100",
        "pack_qty": 100,
        "pack_unit": "box",
        "size": "1/4-20 x 1 in",
        "attributes": ["grade 5", "hex", "zinc plated", "steel"],
        "variations": [
            "HEX CAP SCRW 1/4-20X1 GR5 ZN 100/BX",
            "1/4-20 x 1\" Hex Head Bolt Grade 5 Zinc 100ct",
            "BOLT HEX 1/4-20 X 1IN GR5 ZINC (100 BOX)",
            "SCRW HEX 1/4 20 1 GR5 ZN 100PK"
        ]
    }
]

def generate_datasets(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    random.seed(42)

    base_examples = []
    for prod in PRODUCTS:
        target = {
            "canonical_description": prod["canonical"],
            "pack_quantity": prod["pack_qty"],
            "pack_unit": prod["pack_unit"],
            "size": prod["size"],
            "attributes": prod["attributes"],
            "uncertain_fields": []
        }

        for var in prod["variations"]:
            sku_opt = random.choice([None, f"SKU-{random.randint(100, 999)}", f"VEND-{random.randint(10, 80)}"])
            base_examples.append({
                "input": {
                    "supplier_description": var,
                    "supplier_sku": sku_opt
                },
                "target": target
            })

    # Expand with realistic perturbations:
    # case variations, whitespace, prefix codes, lot numbers, PO references
    expanded = []
    for ex in base_examples:
        desc = ex["input"]["supplier_description"]
        sku = ex["input"]["supplier_sku"]
        target = ex["target"]

        # Original
        expanded.append(ex)

        # Upper case with extra spaces
        expanded.append({
            "input": {"supplier_description": desc.upper(), "supplier_sku": sku},
            "target": target
        })

        # Lower case with vendor item code prefix
        expanded.append({
            "input": {"supplier_description": f"#{random.randint(1000, 9999)} - {desc.lower()}", "supplier_sku": sku},
            "target": target
        })

        # Suffix with lot or batch info
        expanded.append({
            "input": {"supplier_description": f"{desc} [Batch 2026-Q{random.randint(1,4)}]", "supplier_sku": sku},
            "target": target
        })

        # Slight typo/whitespace variant
        desc_sp = desc.replace("-", " ").replace("/", " / ")
        expanded.append({
            "input": {"supplier_description": desc_sp, "supplier_sku": None},
            "target": target
        })

        # Pack abbreviation variant
        if "box" in desc.lower():
            desc_pk = desc.lower().replace("box", "bx").replace("per box", "/bx")
            expanded.append({
                "input": {"supplier_description": desc_pk, "supplier_sku": sku},
                "target": target
            })

    # Ambiguous & Edge Case Examples
    edge_cases = [
        {
            "input": {"supplier_description": "GENERIC ADAPTER USB-C / EQUIV SUBSTITUTE", "supplier_sku": None},
            "target": {
                "canonical_description": "Generic USB-C adapter (substitute)",
                "pack_quantity": 1,
                "pack_unit": "each",
                "size": None,
                "attributes": ["usb-c", "generic"],
                "uncertain_fields": ["substitution_risk", "unspecified_specs"]
            }
        },
        {
            "input": {"supplier_description": "ASSORTED GLOVES SIZE ? 100/BX", "supplier_sku": None},
            "target": {
                "canonical_description": "Assorted gloves, 100 per box",
                "pack_quantity": 100,
                "pack_unit": "box",
                "size": None,
                "attributes": ["assorted"],
                "uncertain_fields": ["unspecified_size", "unspecified_material"]
            }
        },
        {
            "input": {"supplier_description": "MISC PACKAGING SUPPLIES LOT", "supplier_sku": "LOT-99"},
            "target": {
                "canonical_description": "Miscellaneous packaging supplies",
                "pack_quantity": 1,
                "pack_unit": "lot",
                "size": None,
                "attributes": ["packaging", "miscellaneous"],
                "uncertain_fields": ["unspecified_quantity", "unspecified_contents"]
            }
        }
    ]

    for _ in range(15):
        for ec in edge_cases:
            expanded.append(ec)

    random.shuffle(expanded)
    total = len(expanded)

    train_split = int(total * 0.65)
    val_split = int(total * 0.15)

    train_data = expanded[:train_split]
    val_data = expanded[train_split:train_split + val_split]
    test_data = expanded[train_split + val_split:]

    for filename, split in [
        ("train.jsonl", train_data),
        ("val.jsonl", val_data),
        ("test_heldout.jsonl", test_data)
    ]:
        path = os.path.join(output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            for item in split:
                f.write(json.dumps(item) + "\n")
        print(f"Wrote {len(split)} examples to {path}")

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "data")
    generate_datasets(out)
