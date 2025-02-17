FROM python:3.12

WORKDIR /code

COPY ./requirements-unix.txt /code/requirements-unix.txt

RUN apt-get update && apt-get install -y \
  chromium

RUN which chromium

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
  PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

RUN pip install --upgrade pip 

RUN pip install --no-cache-dir --upgrade -r /code/requirements-unix.txt

RUN rm -rf /code/*

COPY ./static /code/static
COPY ./utils /code/utils
COPY ./constants.py /code/constants.py
COPY ./DefaultParameters.py /code/DefaultParameters.py
COPY ./LLM_Handler.py /code/LLM_Handler.py
COPY ./SessionCache.py /code/SessionCache.py
COPY ./TutorBot_Server.py /code/TutorBot_Server.py

EXPOSE 8000

CMD ["python", "TutorBot_Server.py"]