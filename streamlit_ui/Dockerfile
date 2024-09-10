FROM  python:slim-bookworm as base
ENV PYTHONUNBUFFERED 1
ENV TZ=Europe/London
ENV DEBIAN_FRONTEND="noninteractive"

RUN apt-get update && \
    apt-get install -y \
    python3-pip

WORKDIR /app
COPY ./requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

FROM base as release
COPY src/ /app/src
WORKDIR /app/src

EXPOSE 8501
# CMD [ "streamlit", "run", "main.py"]
CMD ["sleep", "infinity"]