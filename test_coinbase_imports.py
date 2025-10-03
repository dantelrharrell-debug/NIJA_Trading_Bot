import importlib, pkgutil

# 1) Check module specs
names = ["coinbase_advanced_py","coinbase_advanced","coinbase","coinbase.client","coinbase.wallet.client"]
for n in names:
    spec = importlib.util.find_spec(n)
    print(n, "->", spec)

# 2) Show top-level modules
print("\nSample top-level modules (first 200):")
print(sorted([m.name for m in pkgutil.iter_modules()])[:200])

# 3) Try importing and list attributes
for n in names:
    try:
        m = __import__(n)
        print("\nImported", n, "-> attrs sample:", sorted([a for a in dir(m) if not a.startswith('_')])[:40])
    except Exception as e:
        print("\nImport failed for", n, ":", e)
