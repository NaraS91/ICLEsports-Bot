FROM python:3.8

ENV PYTHONUNBUFFERED=1

WORKDIR /app/bot

COPY Settings/requirements.txt /app/
COPY bot /app/bot

RUN pip install -r ../requirements.txt

CMD ["python", "ICLBot.py"]