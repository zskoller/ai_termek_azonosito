FROM python:3.10-slim
WORKDIR /app
# Itt feltételezzük, hogy a frontendhez a streamlit kell
RUN pip install streamlit pandas requests openpyxl
COPY . .
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]