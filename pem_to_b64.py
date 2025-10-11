# pem_to_b64.py
import base64

# Paste your full PEM content as a multi-line string
pem_full = """-----BEGIN PRIVATE KEY-----
MHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49
-----END PRIVATE KEY-----"""

# Extract only the base64 part (remove header/footer and newlines)
pem_lines = pem_full.strip().splitlines()
pem_base64 = ''.join(line for line in pem_lines if not line.startswith("-----"))

# Optionally, verify it decodes correctly
decoded = base64.b64decode(pem_base64)

# Output the single-line base64 string
print("Paste this into API_PEM_B64:")
print(pem_base64)
