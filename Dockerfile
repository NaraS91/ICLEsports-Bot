FROM python:3.8

ENV PYTHONUNBUFFERED=1

WORKDIR /bot

COPY CI/requirements.txt /app
COPY bot /app/bot

RUN pip install -r ../requirements.txt

CMD ["python", "ICLBot.py"]