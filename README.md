# Bazilio en la nube

Servidor web que compila programas Bazilio con tu proyecto ANTLR y muestra la
partitura y el audio en el navegador del celular.

```
celular → página web → /api/compilar → tu main (ANTLR) → LilyPond → PDF + MP3
```

## Tu proyecto
`proyecto/bazilio.py` ya contiene tu main y tu visitor (un solo archivo). Contrato con el servidor:

- El main se ejecuta como `python bazilio.py programa.bzl` dentro de una carpeta temporal
  y debe dejar ahí `programa.pdf` y `programa.mp3`. Lo que imprima (`<w>`) sale en la Consola.
- Si tu main tiene otro nombre, define la variable de entorno `BAZILIO_MAIN`.
- **No subas** el lexer/parser generados: el `Dockerfile` los genera desde `grammar/Bazilio.g4`
  con ANTLR 4.13.2 (misma versión que el runtime de `requirements.txt`).
  Si tu `import` espera otros nombres, deben ser `BazilioLexer`, `BazilioParser`, `BazilioVisitor`.

## Desplegar en Render (gratis)
1. Crea un repositorio en GitHub y sube esta carpeta (con tu main dentro de `proyecto/`).
2. En https://render.com → **New → Blueprint** (o Web Service) → elige el repositorio.
   Render lee `render.yaml` y construye el `Dockerfile`.
3. Al terminar te da una URL `https://bazilio-xxxx.onrender.com`; ábrela en el celular.

Notas del plan gratis: el servicio se duerme tras ~15 min sin uso (la primera carga tarda
~1 min), y tiene 512 MB de RAM; si LilyPond se queda sin memoria, usa un plan de pago o
reduce el tamaño de las piezas.

## Probar en tu computadora
```
pip install -r requirements.txt
python tests/probar.py        # prueba el servidor con un main falso
docker build -t bazilio . && docker run -p 10000:10000 bazilio   # abre http://localhost:10000
```

## Seguridad
Cualquiera con la URL puede ejecutar programas: hay límite de tamaño (20 000 caracteres),
tiempo (60 s), 2 compilaciones simultáneas y los resultados se borran a los 30 min.
Tu main solo escribe valores de notas en el `.ly` (nunca texto del usuario), así que LilyPond no recibe código arbitrario.
Para uso privado, agrega una contraseña o no compartas la URL.
