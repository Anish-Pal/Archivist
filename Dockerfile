# ---------------------------------------------------------------------------
# Archivist — Hugging Face Spaces (Docker SDK) image
#
# Spaces run the container as UID 1000, expose a single port (7860 by default)
# and mount optional persistent storage at /data.
# ---------------------------------------------------------------------------
FROM python:3.11-slim

# curl is used by the container healthcheck; the rest of the stack ships wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Model weights are baked into the image under this cache.
    HF_HOME=/home/user/.cache/huggingface \
    # Overridden by the entrypoint when persistent storage is mounted.
    DATA_FOLDER=/data/uploads \
    CHROMA_DB_PATH=/data/chroma_db \
    COOKIE_SECURE=true \
    PORT=7860

WORKDIR /home/user/app

# Torch from PyPI bundles CUDA (~2.5 GB). The CPU index keeps the image small
# and the Space has no GPU anyway. Installed first so the requirements pin
# below resolves against the already-present 2.13.0+cpu build.
RUN pip install --no-cache-dir --user \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.13.0

COPY --chown=user requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

# Bake the embedding and reranker weights into the image. Downloading these at
# boot would add minutes to every cold start and re-download on each restart.
RUN python -c "\
from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('BAAI/bge-small-en-v1.5'); \
CrossEncoder('BAAI/bge-reranker-base'); \
print('models cached')"

# Scripts under docker/ import the app packages, and Python puts the script's
# own directory on sys.path rather than the working directory. Declared after
# the layers above so changing it does not invalidate the model cache.
ENV PYTHONPATH=/home/user/app

COPY --chown=user . .

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/login" || exit 1

ENTRYPOINT ["/home/user/app/docker/entrypoint.sh"]
