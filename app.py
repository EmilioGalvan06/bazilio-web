"""Servidor web de Bazilio: recibe código .bzl, lo compila con tu proyecto ANTLR
y devuelve partitura (PNG/PDF) y audio (MP3) para verlos desde el celular."""
import os
import re
import resource
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

BASE = Path(__file__).parent
MAIN = Path(os.environ.get("BAZILIO_MAIN", BASE / "proyecto" / "bazilio.py"))
TRABAJOS = Path(os.environ.get("BAZILIO_TRABAJOS", "/tmp/bazilio-trabajos"))
MAX_CODIGO = 20_000          # caracteres
TIMEOUT = 60                 # segundos por compilación
VIDA = 30 * 60               # los resultados se borran a los 30 min
MAX_PAGINAS = 6

TRABAJOS.mkdir(parents=True, exist_ok=True)
app = Flask(__name__)
cupo = threading.BoundedSemaphore(int(os.environ.get("BAZILIO_SIMULTANEOS", "2")))


def limpiar_viejos():
    ahora = time.time()
    for d in TRABAJOS.iterdir():
        if d.is_dir() and ahora - d.stat().st_mtime > VIDA:
            shutil.rmtree(d, ignore_errors=True)


def limites():
    """Límites para el proceso hijo (se ejecuta antes del exec)."""
    resource.setrlimit(resource.RLIMIT_CPU, (TIMEOUT, TIMEOUT))
    resource.setrlimit(resource.RLIMIT_FSIZE, (50 * 2**20, 50 * 2**20))


@app.get("/")
def inicio():
    return render_template("index.html")


@app.get("/salud")
def salud():
    return "ok"


@app.post("/api/compilar")
def compilar():
    datos = request.get_json(silent=True) or {}
    codigo = datos.get("codigo", "")
    if not isinstance(codigo, str) or not codigo.strip():
        return jsonify(ok=False, salida="Escribe un programa Bazilio."), 400
    if len(codigo) > MAX_CODIGO:
        return jsonify(ok=False, salida=f"Programa demasiado largo (máx. {MAX_CODIGO} caracteres)."), 413
    if not cupo.acquire(blocking=False):
        return jsonify(ok=False, salida="Servidor ocupado, intenta en unos segundos."), 429
    try:
        limpiar_viejos()
        trabajo = uuid.uuid4().hex
        carpeta = TRABAJOS / trabajo
        carpeta.mkdir()
        (carpeta / "programa.bzl").write_text(codigo, encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(MAIN), "programa.bzl"], cwd=carpeta,
                               capture_output=True, text=True, stdin=subprocess.DEVNULL,
                               timeout=TIMEOUT, preexec_fn=limites)
            ok = r.returncode == 0
            salida = ((r.stdout or "") + ("\n" + r.stderr if r.stderr else "")).strip()
        except subprocess.TimeoutExpired:
            ok, salida = False, f"Tiempo agotado ({TIMEOUT} s). ¿Un while infinito?"
        except OSError as e:
            ok, salida = False, f"No se pudo ejecutar el proyecto: {e}"
    finally:
        cupo.release()

    pdf = next(iter(sorted(carpeta.glob("*.pdf"))), None)
    mp3 = next(iter(sorted(carpeta.glob("*.mp3"))), None)
    paginas = []
    if pdf:
        subprocess.run(["pdftoppm", "-r", "110", "-l", str(MAX_PAGINAS), "-png", str(pdf),
                        str(carpeta / "pagina")], capture_output=True)
        paginas = [f"/archivos/{trabajo}/{p.name}" for p in sorted(carpeta.glob("pagina*.png"))]
    return jsonify(
        ok=ok, salida=salida or "(sin salida)", paginas=paginas,
        pdf=f"/archivos/{trabajo}/{pdf.name}" if pdf else None,
        audio=f"/archivos/{trabajo}/{mp3.name}" if mp3 else None)


@app.get("/archivos/<trabajo>/<nombre>")
def archivos(trabajo, nombre):
    if not re.fullmatch(r"[0-9a-f]{32}", trabajo):
        return "no encontrado", 404
    return send_from_directory(TRABAJOS / trabajo, nombre, conditional=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
