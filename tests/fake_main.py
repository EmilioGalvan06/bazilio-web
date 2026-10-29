"""Main falso SOLO para probar el servidor sin tu proyecto."""
import shutil, sys
from pathlib import Path
n = Path(sys.argv[1]).stem
src = Path(__file__).parent / "muestra"
shutil.copy(src / "hello.pdf", f"{n}.pdf")
shutil.copy(src / "hello.mp3", f"{n}.mp3")
print("compilado", n)
