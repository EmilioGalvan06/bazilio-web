FROM python:3.12-slim

# Herramientas del pipeline: Java (ANTLR), LilyPond (PDF/MIDI), audio (MP3), poppler (PDF -> PNG)
# timidity necesita freepats (sonidos de instrumentos) para que el WAV no salga vacío.
RUN apt-get update && apt-get install -y --no-install-recommends \
        default-jre-headless curl ca-certificates \
        lilypond timidity freepats ffmpeg poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# timidity: la configuración por defecto apunta a un soundfont que no está instalado.
# Se reescribe para usar los instrumentos de freepats; si faltan, la construcción falla a propósito.
RUN if [ -f /etc/timidity/freepats.cfg ]; then \
        echo "source /etc/timidity/freepats.cfg" > /etc/timidity/timidity.cfg; \
    else echo "ERROR: falta /etc/timidity/freepats.cfg" >&2; ls -R /etc/timidity >&2; exit 1; fi

# ANTLR 4.13.2 (misma versión que el runtime de requirements.txt)
RUN curl -fsSL -o /opt/antlr.jar https://www.antlr.org/download/antlr-4.13.2-complete.jar

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Genera lexer, parser, visitor y listener de Python a partir de la gramática
RUN cd grammar && java -jar /opt/antlr.jar -Dlanguage=Python3 -visitor -o ../proyecto Bazilio.g4

ENV PORT=10000
CMD gunicorn -b 0.0.0.0:${PORT} -w 2 --threads 4 --timeout 120 app:app
