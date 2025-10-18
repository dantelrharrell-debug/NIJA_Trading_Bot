# list_accounts.py — run this in your Render shell
from dotenv import load_dotenv
load_dotenv()
import os, json, traceback
try:
    from coinbase.wallet.client import Client
    client = Client(os.getenv("API_KEY"), os.getenv("API_SECRET"))
    print("Using coinbase.wallet.Client")
except Exception as e:
    try:
        import coinbase_advanced_py as cbadv
        client = cbadv.Client(os.getenv("API_KEY"), os.getenv("API_SECRET"))
        print("Using coinbase_advanced_py.Client")
    except Exception as e2:
        print("Failed to init any client:", e, e2)
        raise SystemExit(1)

def dump_accounts():
    try:
        if hasattr(client, "get_accounts"):
            accts = client.get_accounts()
            try:
                all_accts = list(accts)
            except Exception:
                all_accts = accts
            print("Returned accounts type:", type(all_accts))
            for i, a in enumerate(all_accts[:50]):
                print("------ ACCOUNT", i+1, "------")
                try:
                    print("repr:", repr(a)[:2000])
                except:
                    try:
                        print(str(a)[:2000])
                    except:
                        print("<unable to repr>")
        else:
            print("client.get_accounts not present; trying get_account for common currencies")
            for cur in ["USD","BTC","ETH","LTC","SOL","DOGE","XRP"]:
                try:
                    acct = client.get_account(cur)
                    print("get_account(",cur,") repr:", repr(acct)[:2000])
                except Exception as e:
                    print("get_account(",cur,") failed:", e)
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    dump_accounts()
