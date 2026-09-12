FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN git clone --quiet https://github.com/tqdm/tqdm.git /testbed
WORKDIR /testbed
RUN pip install --quiet --no-cache-dir -e . && pip install --quiet --no-cache-dir pandas numpy
