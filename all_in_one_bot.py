from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sys, os, platform, pkgutil, traceback

app = FastAPI(title="NIJA Diagnostic", version="1.0")

def try_import(name):
    out = {"name": name, "found": False, "import_error": None, "attrs": None}
    try:
        spec = importlib.util.find_spec(name)
        out["find_spec"] = None if spec is None else {"name": spec.name, "origin": getattr(spec, "origin", None)}
        module = importlib.import_module(name)
        out["found"] = True
        out["attrs"] = sorted([a for a in dir(module) if not a.startswith("_")])[:40]
    except Exception as e:
        out["import_error"] = repr(e)
    return out

@app.get("/diag2")
async def diag2():
    try:
        attempts = ["coinbase_advanced_py", "coinbase_advanced", "coinbase.wallet.client", "coinbase"]
        import_results = {name: try_import(name) for name in attempts}
        site_paths = [p for p in sys.path if "site-packages" in p or "dist-packages" in p][:6]
        response = {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "platform": platform.platform(),
            "cwd": os.getcwd(),
            "site_paths": site_paths,
            "import_attempts": import_results,
            "sys_path": sys.path[:50],
            "loaded_modules_sample": sorted(list(sys.modules.keys()))[:150],
        }
        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(content={"error": repr(e), "traceback": tb}, status_code=500)
