# build factorio image
FROM debian:stable-slim

# Setup Variables
ARG USER=factorio
ARG GROUP=factorio
ARG PUID=845
ARG PGID=845
ARG BOX64_VERSION=v0.2.4
ARG VERSION=stable
ARG MOUNT_DIR=/factorio
ARG LOG_LEVEL=info

# Setup Environment
ENV PORT=34197 \
    RCON_PORT=27015 \
    USER="$USER" \
    GROUP="$GROUP" \
    PUID="$PUID" \
    PGID="$PGID" \
    LOG_LEVEL="$LOG_LEVEL" \
    MOUNT_DIR=$MOUNT_DIR \
    SAVES="$MOUNT_DIR/saves" \
    PRESET="$PRESET" \
    CONFIG="$MOUNT_DIR/config" \
    MODS="$MOUNT_DIR/mods" \
    SCENARIOS="$MOUNT_DIR/scenarios" \
    SCRIPTOUTPUT="$MOUNT_DIR/script-output" \
    FACTORIO_DIR="/opt/factorio" \
    DLC_SPACE_AGE="true" \
    VERSION=$VERSION


# Create Group and User
RUN apt-get update
RUN addgroup --system --gid "$PGID" "$GROUP" \
    && adduser --system --uid "$PUID" --gid "$PGID" --no-create-home --disabled-password --shell /bin/sh "$USER"

# Setup Directories
RUN mkdir -p /opt $MOUNT_DIR /app

COPY src/* /app
COPY files/config.ini /app

# Setup Python Requirements
RUN apt-get install -y python3 python3-pip python3-requests
# RUN pip3 install --no-cache-dir -r /app/requirements.txt

VOLUME $MOUNT_DIR
EXPOSE $PORT/udp $RCON_PORT/tcp
WORKDIR /app

# ENTRYPOINT ["python3"]
CMD [ "python3", "manager.py" ]