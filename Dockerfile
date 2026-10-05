FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./

RUN python -m pip install --no-cache-dir -r requirements.txt \
    && python -m pip check

COPY . .

CMD ["python", "-m", "pytest", "-v", "--alluredir=allure-results", "--clean-alluredir"]