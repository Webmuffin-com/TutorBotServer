FROM python:3.12

WORKDIR /code

COPY ./requirements-unix.txt /code/requirements-unix.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements-unix.txt

RUN apt-get update && apt-get install -y \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg \
  --no-install-recommends \
  && curl -sSL https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
  && echo "deb [arch=amd64] https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
  && apt-get update && apt-get install -y \
  google-chrome-stable \
  --no-install-recommends

RUN groupadd chrome && useradd -g chrome -s /bin/bash -G audio,video chrome \
  && mkdir -p /home/chrome && chown -R chrome:chrome /home/chrome

COPY ./static /code/static
COPY ./utils /code/utils
COPY ./constants.py /code/constants.py
COPY ./DefaultParameters.py /code/DefaultParameters.py
COPY ./LLM_Handler.py /code/LLM_Handler.py
COPY ./SessionCache.py /code/SessionCache.py
COPY ./TutorBot_Server.py /code/TutorBot_Server.py

CMD ["python", "TutorBot_Server.py"]