FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

# our main dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake libpapi-dev python3 python3-psutil python3-dateutil python3-sqlalchemy ca-certificates

# additional dependencies required for some benchmarks
RUN apt-get update && apt-get install -y --no-install-recommends wget software-properties-common gpg-agent

# place to store results
VOLUME /data
