FROM python:3.11-slim

WORKDIR /streamlit_app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python","-m","streamlit","run","app/streamlit_app.py","--server.address=0.0.0.0","--server.port=8080"]