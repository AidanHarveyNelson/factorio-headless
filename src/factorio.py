import random
import logging
import shutil
import string
import subprocess
import os


LOG = logging.getLogger("factorio.server")


class Factorio:
    def __init__(self, port, rcon_port, saves_dir, config_dir, mods_dir, scenarios_dir, script_output, dlc_space_age, version, factorio_dir):
        self.port = port
        self.rcon_port = rcon_port
        self.saves_dir = saves_dir
        self.config_dir = config_dir
        self.mods_dir = mods_dir
        self.scenarios_dir = scenarios_dir
        self.script_output = script_output
        self.dlc_space_age = dlc_space_age
        self.version = version
        self.factorio_dir = factorio_dir

        self._process = None
        self._exec = f'runuser -u {os.environ["USER"]} -g {os.environ["GROUP"]} --'
        self._run_file = os.path.join(self.factorio_dir, 'bin', 'x64', 'factorio')

    @classmethod
    def from_environment(cls):
        """Create a Manager instance using environment variables."""
        try:
            port = os.environ["PORT"]
            rcon_port = os.environ["RCON_PORT"]
            saves_dir = os.environ["SAVES"]
            config_dir = os.environ["CONFIG"]
            mods_dir = os.environ["MODS"]
            scenarios_dir = os.environ["SCENARIOS"]
            script_output = os.environ["SCRIPTOUTPUT"]
            dlc_space_age = os.environ["DLC_SPACE_AGE"]
            version =       os.environ["VERSION"]
            factorio_dir = os.environ["FACTORIO_DIR"]
        except KeyError:
            raise KeyError("Unable to find required environment variables")
        return cls(port, rcon_port, saves_dir, config_dir, mods_dir, scenarios_dir, script_output, dlc_space_age, version, factorio_dir)


    @property
    def rcon_password(self):
        """Return the RCON password."""
        file_path = os.path.join(self.config_dir, 'rconpw')
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                return f.read().strip()
        with open(file_path, 'w') as f:
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

    def create_save(self, save_name: str, preset: str = None) -> str:
        """Create a new save file."""
        if os.path.isfile(os.path.join(self.saves_dir, save_name)):
            LOG.error('Unable to create save, file already exists')

        run_command = [
            self._exec,
            self._run_file,
            f"--create {os.path.join(self.saves_dir, save_name)}.zip",
            f"--map-gen-settings {self.map_gen_settings}",
            f"--map-settings {self.map_settings}",
        ]

        if preset:
            run_command.append(f"--preset {preset}")

        LOG.info(f"Executing command: {' '.join(run_command)}")
        subprocess.run(' '.join(run_command), shell=True, check=True)
        LOG.info(f"Factorio Created Save with name: {save_name}")
        return save_name

    def generate_config(self, save:str = None, load_latest: bool = False) -> list:
        """Generate the Factorio server configuration."""

        config = [
            f"--port {self.port}",
            f"--rcon-port {self.rcon_port}",
            f"--server-settings {self.server_settings}",
            f"--server-banlist {self.server_banlist}",
            f"--server-whitelist {self.server_whitelist}",
            f'--use-server-whitelist',
            f'--server-adminlist {self.server_adminlist }',
            f"--rcon-password {self.rcon_password}",
            f"--server-id {os.path.join(self.config_dir, 'server-id.json')}",
            f"--mod-directory {self.mods_dir}",
        ]

        if save:
            config.append(f"--start-server {os.path.join(self.saves_dir, save)}.zip")
        elif load_latest:
            config.append("--start-server-load-latest")
        else:
            _save_name = self.create_save('default_save')
            config.append(f"--start-server {os.path.join(self.saves_dir, _save_name)}.zip")
        
        LOG.debug(f"Generated configuration: {config}")
        return config

    def is_players_online(self) -> bool:
        """Check if players are online."""
        LOG.info("Checking if players are online...")
        return False
    
    def start(self, config: list):
        """Run the Factorio server."""
        LOG.info(f"Running Factorio server on port {self.port} with RCON port {self.rcon_port}")
        run_command = [
            self._exec,
            self._run_file,
        ] + config

        LOG.info(f"Executing command: {' '.join(run_command)}")
        self._process = subprocess.Popen(' '.join(run_command),
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.PIPE,  
                                         shell=True)
        stdout = self._process.stdout.read().decode().strip() if self._process.stdout else ''
        stderr = self._process.stderr.read().decode().strip() if self._process.stderr else ''
        LOG.debug(stdout)
        LOG.debug(stderr)
        LOG.info(f"Factorio server started with PID {self._process.pid}")

    def stop(self) -> bool:
        """Stop the Factorio server."""
        if self._process is not None:
            LOG.info(f"Stopping Factorio server with PID {self._process.pid}")
            self._process.terminate()
            try:
                self._process.wait(60)
                return True
            except subprocess.TimeoutExpired:
                LOG.error(f"Factorio server with PID {self._process.pid} did not stop in time.")
                self._process.kill()
                return True
        return False