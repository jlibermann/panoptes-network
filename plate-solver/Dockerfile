ARG base_tag=latest

FROM gcr.io/panoptes-exp/panoptes-utils:$base_tag

COPY ./requirements.txt /

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc pkg-config build-essential && \
    pip install --no-cache-dir -r /requirements.txt && \
    # Cleanup apt.
    apt-get autoremove --purge -y \
        gcc pkg-config build-essential && \
    apt-get autoremove --purge -y && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app

CMD ["python", "-u", "main.py"]
