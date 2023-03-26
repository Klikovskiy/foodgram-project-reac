FROM python:3.10-slim
WORKDIR /backend
COPY requirements.txt .
RUN pip3 install --upgrade pip setuptools --no-cache-dir && pip3 install -r requirements.txt --no-cache-dir
COPY . .
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000"]