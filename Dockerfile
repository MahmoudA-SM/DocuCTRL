FROM python:3.9

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

COPY --chown=user . $HOME/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
