"""Prueba del servidor con un main falso: python tests/probar.py"""
import os, sys
from pathlib import Path
raiz = Path(__file__).resolve().parent.parent
os.environ["BAZILIO_MAIN"] = str(raiz / "tests" / "fake_main.py")
os.environ["BAZILIO_TRABAJOS"] = "/tmp/claude-0/trabajos-test"
sys.path.insert(0, str(raiz))
import app as srv
c = srv.app.test_client()
print("salud:", c.get("/salud").data)
print("inicio:", c.get("/").status_code)
r = c.post("/api/compilar", json={"codigo": "Main |: <:> {C4 D4} :|"}).get_json()
print({k: (v if k != "salida" else v[:30]) for k, v in r.items()})
for u in [r["audio"], r["pdf"], *r["paginas"]]:
    print(u.split("/")[-1], c.get(u).status_code)
print("vacío:", c.post("/api/compilar", json={"codigo": " "}).status_code)
print("grande:", c.post("/api/compilar", json={"codigo": "x" * 30000}).status_code)
print("traversal:", c.get("/archivos/../app.py").status_code, c.get("/archivos/" + "a"*32 + "/../../app.py").status_code)
