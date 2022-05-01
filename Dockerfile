#
FROM python:3.7.12

#
WORKDIR /code

#
COPY ./requirements.txt /code/requirements.txt

RUN apt-get -y update && \
    apt-get -y install git && \
    apt-get -y install curl &&\
    pip install --upgrade pip

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Add .cargo/bin to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

#
RUN pip install -r /code/requirements.txt

#
COPY . /code

#
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
