# Pull official base image for Python
# As of today, Raspberry Pi OS is based on Debian 11 (bullseye)
FROM python:3.11-slim-bullseye as base

FROM base as deps

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY ./pip/requirements.txt .
RUN pip install --upgrade pip \
    pip install -r requirements.txt

# Stage to build GRBL simulator from source code
# As of today, Raspberry Pi OS is based on Debian 11 (bullseye)
FROM debian:bullseye-slim as build
WORKDIR /app

# Install minimal dependencies, clone repositories and build executable
RUN apt-get update -y && apt-get upgrade -y
RUN apt install -y git make gcc
RUN git clone https://github.com/gnea/grbl.git
WORKDIR /app/grbl/grbl
RUN git clone https://github.com/Leandro-Bertoluzzi/grbl-sim.git
WORKDIR /app/grbl/grbl/grbl-sim
RUN git checkout develop
RUN make new

# In case you want to export the generated executable files
FROM scratch AS export-exe
COPY --from=build /app/grbl/grbl/grbl-sim/*.exe ./

FROM deps as development
WORKDIR /app

# Copy the necessary files from project
COPY ./config.py .
COPY ./database ./database
COPY ./utils ./utils
COPY ./worker ./worker

WORKDIR /app/worker

# Copy executable from build stage
COPY --from=build app/grbl/grbl/grbl-sim/grbl_sim.exe ./grbl_sim.exe

# Install minimal dependencies
RUN apt-get update -y && apt-get upgrade -y
RUN apt install -y socat

# Copy script to create virtual port, to activate later
COPY ./worker/simport.sh .
# Fix line endings
RUN sed -i "s/\r//" ./simport.sh
# Ensure execution permissions
RUN chmod +x ./simport.sh
