import base64
import sys
from pathlib import Path

def pem_to_b64(pem_path):
    pem_file = Path(pem_path)
    if not pem_file.exists():
        print(f"❌ File not found: {pem_path}")
        return

    # Read file in binary mode (works for PEM or DER)
    with open(pem_file, "rb") as f:
        pem_bytes = f.read()

    # Encode as base64
    b64_str = base64.b64encode(pem_bytes).decode("ascii")

    # Optional: make it one line (Render env vars often require this)
    b64_str_one_line = "".join(b64_str.split())

    print("✅ Base64 string (set this as API_PEM_B64):")
    print(b64_str_one_line)
    print("\nLength:", len(b64_str_one_line))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pem_to_b64.py /path/to/your/key.pem")
    else:
        pem_to_b64(sys.argv[1])
