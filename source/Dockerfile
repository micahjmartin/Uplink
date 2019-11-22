FROM alpine:latest
RUN apk add --update python3 tzdata git

# Set the timezone
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN mkdir -p /opt/uplink
WORKDIR /opt/uplink
COPY . .
