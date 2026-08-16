FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    cmake \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY CMakeLists.txt .
COPY src/ ./src/

RUN mkdir build && cd build && cmake .. && make

EXPOSE 8080

CMD ["./build/server"]