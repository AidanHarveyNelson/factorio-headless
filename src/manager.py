import requests
import logging
import shutil
import sys
import time
import os

from factorio import Factorio

LOG = logging.getLogger("factorio.server")
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/factorio.log', mode='a')
    ]
)


class Manager():
    """Manager class to handle Factorio server operations."""

    def __init__(self,):
        """Initialize the Manager with the necessary parameters."""

        self.mount_dir = os.environ["MOUNT_DIR"]
        self.session = requests.session()
        self.factorio = Factorio.from_environment()
        self._current_version = None
        self._current_version_file = os.path.join('/app', 'VERSION')

    @property
    def current_version(self):
        if self._current_version is None:
            if os.path.isfile(self._current_version_file):
                with open(self._current_version_file, 'r') as f:
                    self.current_version = f.read().strip()
            else:
                self.current_version = self.get_latest_releases()
        return self._current_version
    
    @current_version.setter
    def current_version(self, value):
        """Set the current version of Factorio."""
        with open(self._current_version_file, 'w') as f:
            f.write(value)
        self._current_version = value

    def download_factorio(self) -> str:
        """Download the Factorio server files."""
        # Implement the download logic here
        print(self.factorio.version)
        output_dir = '/tmp/factorio_downloads'
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'factorio.tar.xz')
        url = f"https://www.factorio.com/get-download/{self.factorio.version}/headless/linux64"
        response = self.session.get(url)
        response.raise_for_status()
        print(response)
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f"Factorio server files downloaded to {output_file}")
        return output_file

    def backup_factorio(self) -> str:
        """Backup the Factorio server files."""
        backup_dir = f'/tmp/factorio_backup/'
        print(f"Backing up Factorio server files to {backup_dir}")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        shutil.copytree(self.factorio.factorio_dir, backup_dir, dirs_exist_ok=True)
        print(f"Backup completed successfully to {backup_dir}")
        return backup_dir

    def install_factorio(self):
        """Install the Factorio server files."""

        backup_dir = None
        if os.path.exists(self.factorio.factorio_dir):
            backup_dir = self.backup_factorio()
            print('Rmoving old Factorio directory')
            os.remove(self.factorio.factorio_dir)

        download_loc = self.download_factorio()
        print(f"Installing Factorio server files from {download_loc} to {self.factorio.factorio_dir}")
        if not os.path.exists(self.factorio.factorio_dir):
            os.makedirs(self.factorio.factorio_dir)

        # Archive includes a folder named 'factorio'
        shutil.unpack_archive(download_loc, '/opt', 'tar')
        os.remove(download_loc)

        if backup_dir is None:
            print(f"Creating necessary directories in {self.factorio.factorio_dir}")
            os.makedirs(self.factorio.mods_dir, exist_ok=True)
            os.makedirs(self.factorio.saves_dir, exist_ok=True)
            os.makedirs(self.factorio.scenarios_dir, exist_ok=True)
            os.makedirs(self.factorio.config_dir, exist_ok=True)
            os.symlink(self.factorio.scenarios_dir, os.path.join(self.factorio.factorio_dir, 'scenarios'), target_is_directory=True)
            os.symlink(self.factorio.saves_dir, os.path.join(self.factorio.factorio_dir, 'saves'), target_is_directory=True)
            os.symlink(self.factorio.config_dir, os.path.join(self.factorio.factorio_dir, 'config'), target_is_directory=True)
            shutil.copyfile(os.path.join('/app', 'config.ini'), os.path.join(self.factorio.config_dir, 'config.ini'))
        else:
            print(f"Restoring Factorio server files from backup {backup_dir} to {self.factorio.factorio_dir}")
            shutil.copytree(self.factorio.mods_dir.replace(self.factorio.mods_dir, backup_dir), self.factorio.mods_dir, dirs_exist_ok=True)
            shutil.copytree(self.factorio.saves_dir.replace(self.factorio.saves_dir, backup_dir), self.factorio.saves_dir, dirs_exist_ok=True)
            shutil.copytree(self.factorio.scenarios_dir.replace(self.factorio.scenarios_dir, backup_dir), self.factorio.scenarios_dir, dirs_exist_ok=True)
            shutil.copytree(self.factorio.config_dir.replace(self.factorio.config_dir, backup_dir), self.factorio.config_dir, dirs_exist_ok=True)
            shutil.rmtree(backup_dir)

        print(f"Setting permissions for Factorio server files in {self.factorio.factorio_dir} and {self.mount_dir}")
        os.system(f'chown -R {os.environ["PUID"]}:{os.environ["PGID"]} {self.factorio.factorio_dir}')
        os.system(f'chown -R {os.environ["PUID"]}:{os.environ["PGID"]} {self.mount_dir}')

    def run(self):
        """Run the Manager to start the Factorio server."""
        running = True
        last_updated_check = time.time()
        while running:
            if not os.path.exists(self.factorio.factorio_dir):
                print("Factorio server files not found, downloading...")
                self.install_factorio()
                self.factorio.start(self.factorio.generate_config())

            if time.time() - last_updated_check > 60:  # Check for updates every minute
                if self.current_version != self.get_latest_releases():
                    if self.factorio.is_players_online():
                        print("Players are online, cannot update Factorio server files.")
                        continue

                    print('Stopping Factorio server to update files...')
                    self.factorio.stop()
                    time.sleep(60)
                    print('Finished waiting for Factorio server to stop.')
                    
                    print(f"Current version {self.current_version} does not match expected version {self.factorio.version}.")
                    print("Updating Factorio server files...")
                    self.install_factorio()
                    self.current_version = self.get_latest_releases()
                    self.factorio.start(self.factorio.generate_config())
                last_updated_check = time.time()

            if self.factorio._pid is None:
                print("Factorio server is not running, starting...")
                self.factorio.start(self.factorio.generate_config())

            print("Factorio server is running with the latest files.")
            time.sleep(20)

    def get_latest_releases(self) -> str:
        """Fetch the latest Factorio releases from the API."""
        url = "https://factorio.com/api/latest-releases"
        try:
            response = self._session.get(url)
            response.raise_for_status()
            return response.json()[self.factorio.version]['headless']
        except requests.RequestException as e:
            print(f"Error fetching latest releases: {e}")
            raise requests.RequestException("Failed to fetch latest releases from Factorio API") from e


def main():
    """Main function to run the Manager."""
    manager = Manager()
    print("Manager initialized successfully.")
    manager.run()


if __name__ == "__main__":
    main()




