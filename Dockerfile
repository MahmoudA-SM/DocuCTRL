FROM node:18 AS frontend-build

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Python backend
FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Create a non-root user
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

ENV STORAGE_DIR=/tmp/storage

# Download font to assets directory
RUN mkdir -p /home/user/app/assets && \
	curl -o /home/user/app/assets/Amiri-Regular.ttf https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf

COPY --chown=user . $HOME/app

# Copy React build from frontend stage
COPY --from=frontend-build --chown=user /frontend/build $HOME/app/frontend/build

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
