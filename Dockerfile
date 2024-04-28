# Usa un'immagine ufficiale di Python come parent image
FROM python:3.9-slim

# Imposta la directory di lavoro nel container
WORKDIR /app

RUN mkdir -p ./db-data

# Copia i file di requisiti e installa le dipendenze
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice sorgente dell'app nella directory di lavoro del container
COPY . .

# Comunica al Docker host che il container ascolta sulla porta specificata a runtime.
EXPOSE 5000

