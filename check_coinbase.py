import subprocess

def check_coinbase_modules():
    result = subprocess.run(['find', '.', '-name', 'coinbase*'], capture_output=True, text=True)
    print("Coinbase files found:\n", result.stdout)

if __name__ == "__main__":
    check_coinbase_modules()
