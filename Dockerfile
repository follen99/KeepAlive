# Usa un'immagine base leggera
FROM python:3.9-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file necessari
COPY requirements.txt .
COPY src/app.py .
COPY src/templates/ templates/

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Crea la directory per il database (utile per il volume mounting)
RUN mkdir -p /app/instance

# Esponi la porta di Flask
EXPOSE 5000

# Variabili d'ambiente per Flask
ENV FLASK_APP=app.py

# Esegui l'app
CMD ["python", "app.py"]