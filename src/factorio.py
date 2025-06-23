"""Factorio server management module."""

import random
import logging
import shutil
import string
import subprocess
import os


LOG = logging.getLogger("factorio.server")


class Factorio:
    """Factorio class to handle server operations."""
    # pylint: disable=too-many-positional-arguments,too-many-instance-attributes
    def __init__(self, mount_dir, port, rcon_port, dlc_space_age, version, factorio_dir):
        """Initialize the Factorio server manager."""

        self.mount_dir = mount_dir
        self.port = port
        self.rcon_port = rcon_port
        self.saves_dir = os.path.join(mount_dir, 'saves')
        self.config_dir = os.path.join(mount_dir, 'config')
        self.mods_dir = os.path.join(mount_dir, 'mods')
        self.scenarios_dir = os.path.join(mount_dir, 'scenarios')
        self.script_output = os.path.join(mount_dir, 'script-output')
        self.dlc_space_age = dlc_space_age
        self.version = version
        self.factorio_dir = factorio_dir

        self._process = None
        self._run_command = [
            'runuser', '-u', os.environ['USER'], '-g', os.environ['GROUP'], '--',
            os.path.join(self.factorio_dir, 'bin', 'x64', 'factorio')
        ]

    @classmethod
    def from_environment(cls):
        """Create a Manager instance using environment variables."""
        try:
            mount_dir = os.environ["MOUNT_DIR"]
            port = os.environ["PORT"]
            rcon_port = os.environ["RCON_PORT"]
            dlc_space_age = os.environ["DLC_SPACE_AGE"]
            version =       os.environ["VERSION"]
            factorio_dir = os.environ["FACTORIO_DIR"]
        except KeyError as error:
            raise KeyError("Unable to find required environment variables") from error
        return cls(mount_dir, port, rcon_port, dlc_space_age, version, factorio_dir)

    @property
    def rcon_password(self):
        """Return the RCON password."""
        file_path = os.path.join(self.config_dir, 'rconpw')
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding="utf-8") as f:
                return f.read().strip()
        with open(file_path, 'w', encoding="utf-8") as f:
            passwod = ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))
            f.write(passwod)
            return passwod

    @property
    def server_settings(self):
        """Return the server settings."""
        file_path = os.path.join(self.config_dir, 'server-settings.json')
        if not os.path.isfile(file_path):
            shutil.copyfile(os.path.join(self.factorio_dir, 'data', 'server-settings.example.json'), file_path)
        return file_path

    @property
    def server_banlist(self):
        """Return the server banlist."""
        file_path = os.path.join(self.config_dir, 'server-banlist.json')
        return file_path

    @property
    def server_whitelist(self):
        """Return the server whitelist."""
        file_path = os.path.join(self.config_dir, 'server-whitelist.json')
        if not os.path.isfile(file_path):
            shutil.copyfile(os.path.join(self.factorio_dir, 'data', 'server-whitelist.example.json'), file_path)
        return file_path
    
    @property
    def server_adminlist(self): 
        """Return the server adminlist."""
        file_path = os.path.join(self.config_dir, 'server-adminlist.json')
        return file_path
    
    @property
    def map_gen_settings(self):
        """Return the map generation settings."""
        file_path = os.path.join(self.config_dir, 'map-gen-settings.json')
        if not os.path.isfile(file_path):
            shutil.copyfile(os.path.join(self.factorio_dir, 'data', 'map-gen-settings.example.json'), file_path)
        return file_path

    @property
    def map_settings(self):
        """Return the map settings."""
        file_path = os.path.join(self.config_dir, 'map-settings.json')
        if not os.path.isfile(file_path):
            shutil.copyfile(os.path.join(self.factorio_dir, 'data', 'map-settings.example.json'), file_path)
        return file_path

    @property
    def is_running(self) -> bool:
        """Check if the Factorio server is running."""
        if self._process is None:
            return False
        return True

    def has_saves(self) -> bool:
        """Check if there are any saves available."""
        LOG.info("Checking for existing saves...")
        has_saves = any(os.path.isfile(os.path.join(self.saves_dir, f)) for f in os.listdir(self.saves_dir))
        return has_saves

    def create_save(self, save_name: str, preset: str = None) -> str:
        """Create a new save file."""
        if os.path.isfile(os.path.join(self.saves_dir, save_name)):
            LOG.error('Unable to create save, file already exists')

        run_command =  self._run_command + [
            "--create", os.path.join(self.saves_dir, save_name) + ".zip",
            "--map-gen-settings", self.map_gen_settings,
            "--map-settings", self.map_settings,
        ]

        if preset:
            run_command = run_command + ["--preset", preset]

        LOG.info("Executing command: %s", ' '.join(run_command))
        subprocess.run(run_command, check=True)
        LOG.info("Factorio Created Save with name: %s", save_name)
        return save_name

    def generate_config(self, save:str = None, load_latest: bool = False) -> list:
        """Generate the Factorio server configuration."""

        config = [
            "--port", str(self.port),
            "--rcon-port", str(self.rcon_port),
            "--server-settings", self.server_settings,
            "--server-banlist", self.server_banlist,
            "--server-whitelist", self.server_whitelist,
            "--use-server-whitelist",
            "--server-adminlist", self.server_adminlist,
            "--rcon-password", self.rcon_password,
            "--server-id", os.path.join(self.config_dir, 'server-id.json'),
            "--mod-directory", self.mods_dir,
            "--console-log", os.path.join(self.mount_dir, 'factorio-console.log'),
        ]

        if save:
            config = config + ["--start-server", os.path.join(self.saves_dir, save) + ".zip"]
        elif load_latest:
            config = config + ["--start-server-load-latest"]
        else:
            if not self.has_saves():
                LOG.info("No saves found, creating a default save.")
                # Create a default save if none exist
                _save_name = self.create_save('default_save')
                config = config + ["--start-server", os.path.join(self.saves_dir, _save_name) + ".zip"]
            else:
                LOG.info("No save specified, using the latest save.")
                config = config + ["--start-server-load-latest"]

        LOG.debug("Generated configuration: %s", config)
        return config

    def is_players_online(self) -> bool:
        """Check if players are online."""
        LOG.info("Checking if players are online...")
        return False

    # pylint: disable=consider-using-with
    def start(self, config: list):
        """Run the Factorio server."""
        LOG.info("Running Factorio server on port %s with RCON port %s", self.port, self.rcon_port)
        run_command = self._run_command + config

        LOG.info("Executing command: %s", " ".join(run_command))
        self._process = subprocess.Popen(run_command,
                                         stdout=open('/var/log/factorio/access.log', 'w', encoding='utf-8'),
                                         stderr=open('/var/log/factorio/error.log', 'w', encoding='utf-8'),
                                         start_new_session=True)
        LOG.info("Factorio server started with PID %s", self._process.pid)

    def stop(self):
        """Stop the Factorio server."""
        if self._process is None:
            LOG.warning("Factorio server is not running, nothing to stop.")
            return
        LOG.debug("Stopping factorio server with PID %s", self._process.pid)
        self._process.terminate()
        LOG.debug("Waiting for Factorio server process to terminate...")
        self._process.wait(60)
        LOG.info("Factorio server process terminated.")
