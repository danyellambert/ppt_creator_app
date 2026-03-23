FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY ppt_creator /app/ppt_creator
COPY examples /app/examples

RUN pip install --no-cache-dir .

WORKDIR /work

CMD ["python", "-m", "ppt_creator.cli", "--help"]
