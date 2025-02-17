FROM python:3.12

RUN apt-get update && apt-get install -y \
  chromium

RUN which chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
  PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

RUN mkdir -p /code
WORKDIR /code

COPY . /code

RUN pip install --upgrade pip 
RUN pip install --no-cache-dir --upgrade -r /code/requirements-unix.txt


EXPOSE 8000

CMD ["python", "TutorBot_Server.py"]