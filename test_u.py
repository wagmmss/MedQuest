import sys, os
sys.path.insert(0, os.path.abspath('app/backend'))
from api.universal_pool import generate_content_with_fallback
try:
    print(generate_content_with_fallback('test', timeout=15))
except Exception as e:
    print("Error:", e)
