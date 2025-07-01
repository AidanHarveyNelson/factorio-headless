# Factorio Headless Server

A Docker image for running a Factorio headless server with automatic updates and mod management.

## Quick Start

```bash
docker run -d \
  --name factorio \
  -p 34197:34197/udp \
  -p 27015:27015/tcp \
  -v /path/to/factorio:/factorio \
  your-image-name:latest
```

This will create a new Factorio server with default settings. The server will be available on port 34197 (UDP) with RCON access on port 27015 (TCP).

## Features

- **Automatic Updates**: Checks for and installs the latest Factorio version
- **Space Age DLC Support**: Toggle Space Age DLC and related mods
- **Persistent Storage**: All saves, configs, and mods are stored in a volume
- **RCON Support**: Remote console access for server management
- **Configurable Save Management**: Load latest save, specific saves, or generate new ones
- **Scenario Support**: Run custom scenarios
- **Whitelist/Banlist Support**: Player access control

## Environment Variables

### Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `34197` | Game server port (UDP) |
| `RCON_PORT` | `27015` | RCON port (TCP) |
| `LOG_LEVEL` | `info` | Logging level (debug, info, warning, error) |
| `VERSION` | `stable` | Factorio version channel (stable, experimental) |
| `FACTORIO_DIR` | `/opt/factorio` | Internal Factorio installation directory |
| `DLC_SPACE_AGE` | `true` | Enable/disable Space Age DLC and related mods |
| `LOAD_LATEST_SAVE` | `true` | Load the most recent save file |
| `SAVE_NAME` | `_autosave1` | Specific save file to load (without .zip extension) |
| `GENERATE_NEW_SAVE` | `false` | Generate a new save instead of loading existing |
| `SERVER_SCENARIO` | `""` | Load a specific scenario instead of a save |
| `PRESET` | `""` | Map generation preset when creating new saves |
| `USER` | `factorio` | Username for running the server |
| `GROUP` | `factorio` | Group name for running the server |
| `PUID` | `845` | User ID for file permissions |
| `PGID` | `845` | Group ID for file permissions |
| `MOUNT_DIR` | `/factorio` | Main volume mount point for persistent data |
| `TOKEN` | `""` | Factorio.com authentication token for public servers |

## Volume Structure

The container expects a volume mounted at `/factorio` with the following structure:

```
/factorio/
├── saves/          # Save files (.zip)
├── config/         # Server configuration files
│   ├── server-settings.json
│   ├── server-whitelist.json
│   ├── server-banlist.json
│   ├── server-adminlist.json
│   ├── map-gen-settings.json
│   ├── map-settings.json
│   ├── rconpw      # Auto-generated RCON password
│   └── config.ini
├── mods/           # Mod files and mod-list.json
└── scenarios/      # Custom scenarios
```

## Usage Examples

### Basic Server

```bash
docker run -d \
  --name factorio \
  -p 34197:34197/udp \
  -p 27015:27015/tcp \
  -v factorio-data:/factorio \
  your-image-name:latest
```

### Server with Custom Settings

```bash
docker run -d \
  --name factorio \
  -p 34197:34197/udp \
  -p 27015:27015/tcp \
  -e SAVE_NAME="my-world" \
  -e DLC_SPACE_AGE=false \
  -e LOG_LEVEL=debug \
  -v factorio-data:/factorio \
  your-image-name:latest
```

### Load Specific Scenario

```bash
docker run -d \
  --name factorio \
  -p 34197:34197/udp \
  -p 27015:27015/tcp \
  -e SERVER_SCENARIO="my-scenario" \
  -e PRESET="rich-resources" \
  -v factorio-data:/factorio \
  your-image-name:latest
```

### Experimental Version

```bash
docker run -d \
  --name factorio \
  -p 34197:34197/udp \
  -p 27015:27015/tcp \
  -e VERSION=experimental \
  -v factorio-data:/factorio \
  your-image-name:latest
```

## Docker Compose

```yaml
version: '3.8'

services:
  factorio:
    image: your-image-name:latest
    container_name: factorio
    ports:
      - "34197:34197/udp"
      - "27015:27015/tcp"
    environment:
      - SAVE_NAME=my-world
      - DLC_SPACE_AGE=true
      - LOG_LEVEL=info
      - PUID=1000
      - PGID=1000
    volumes:
      - factorio-data:/factorio
    restart: unless-stopped

volumes:
  factorio-data:
```

## Configuration Files

### Server Settings

The server will automatically create default configuration files if they don't exist. You can customize these by placing your own files in the `/factorio/config/` directory:

- `server-settings.json` - Main server configuration
- `server-whitelist.json` - Player whitelist
- `server-banlist.json` - Banned players
- `server-adminlist.json` - Server administrators
- `map-gen-settings.json` - World generation settings
- `map-settings.json` - Game difficulty and behavior settings

### RCON Password

The RCON password is automatically generated and stored in `/factorio/config/rconpw`. You can retrieve it with:

```bash
docker exec factorio cat /factorio/config/rconpw
```

## Mod Management

Mods should be placed in the `/factorio/mods/` directory. The `mod-list.json` file will be automatically managed for Space Age DLC mods based on the `DLC_SPACE_AGE` environment variable.

### Space Age DLC Mods

When `DLC_SPACE_AGE=true`, the following mods are automatically enabled:
- `elevated-rails`
- `quality` 
- `space-age`

## Building

To build the image yourself:

```bash
git clone <repository-url>
cd factorio-headless
docker build -t factorio-headless .
```

## Logs

Server logs are available through Docker:

```bash
# View server output
docker logs factorio

# Follow logs in real-time
docker logs -f factorio
```

The container also creates log files at:
- `/var/log/factorio/access.log` - Server access logs
- `/var/log/factorio/error.log` - Server error logs
- `/app/factorio.log` - Manager application logs

## Troubleshooting

### Server Won't Start

1. Check the logs: `docker logs factorio`
2. Verify volume permissions match `PUID`/`PGID`
3. Ensure the game port (UDP) is not blocked by firewall

### Can't Connect to Server

1. Verify port mapping: `-p 34197:34197/udp`
2. Check if server is running: `docker exec factorio ps aux`
3. Verify RCON access: `telnet <server-ip> 27015`

### Permission Issues

If you encounter permission issues, ensure the `PUID` and `PGID` environment variables match your host user:

```bash
docker run -d \
  -e PUID=$(id -u) \
  -e PGID=$(id -g) \
  # ... other options
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
