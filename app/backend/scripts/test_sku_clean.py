import re

skus = [
    'USP-SP-2022-01-R1',
    'PROVA USP-SP 2022 - R1Q04',
    'SUS-SP-2022-Q96-R1',
    'USP-SP-2022-10-R1 ',
    'TEEM-AUTORAL-2026-DISCURSIVA-4'
]

def parse_sku_qnum(sku: str, fallback: int) -> tuple[int, bool]:
    sku = sku.strip()
    # If it's a completely different exam (e.g. TEEM discursiva)
    if "DISCURSIVA" in sku or "TEEM" in sku:
        return None, False
        
    # Match R1Q04, Q96, etc.
    m = re.search(r"R\dQ(\d+)", sku, re.IGNORECASE)
    if m:
        return int(m.group(1)), True
        
    m = re.search(r"-Q?(\d+)-R\d", sku, re.IGNORECASE)
    if m:
        return int(m.group(1)), True
        
    m = re.search(r"-\d{4}-(\d+)", sku)
    if m:
        return int(m.group(1)), True
        
    m = re.search(r"-(\d+)", sku)
    if m:
        return int(m.group(1)), True
        
    return fallback, True

for s in skus:
    num, keep = parse_sku_qnum(s, 999)
    print(f"{s!r} -> num={num}, keep={keep}")
