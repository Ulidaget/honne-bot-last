FROM python:3.11
EXPOSE 8088
WORKDIR /app
COPY requirements.txt ./
# # Instalar dependencias y Tesseract con idioma español
# RUN apt-get update && apt-get install -y \
#     tesseract-ocr \
#     tesseract-ocr-spa \
#     libtesseract-dev \
#     && rm -rf /var/lib/apt/lists/*

# # Configurar la variable TESSDATA_PREFIX para Tesseract
# ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata/

RUN pip install -r requirements.txt
COPY . ./
ENTRYPOINT [ "streamlit", "run", "honne-enterprise-last.py", "--server.port=8088", "--server.address=0.0.0.0" ]