"""Manager class to handle Factorio server operations."""

import logging
import os
import shutil
import sys
import time

import requests

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

        self.session = requests.session()
        self.factorio = Factorio.from_environment()
        self._current_version = None
        self._current_version_file = os.path.join('/app', 'VERSION')

    @property
    def current_version(self):
        if self._current_version is None:
            if os.path.isfile(self._current_version_file):
                with open(self._current_version_file, 'r', encoding='utf-8') as f:
                    self.current_version = f.read().strip()
            else:
                self.current_version = self.get_latest_releases()
        return self._current_version

    @current_version.setter
    def current_version(self, value):
        """Set the current version of Factorio."""
        with open(self._current_version_file, 'w', encoding='utf-8') as f:
            f.write(value)
        self._current_version = value

    def download_factorio(self) -> str:
        """Download the Factorio server files."""
        LOG.info("Pulling factorio files for version %s", self.current_version)
        output_dir = '/tmp/factorio_downloads'
        os.makedirs(output_dir, exist_ok=True)
        # output_file = os.path.join(output_dir, f'factorio_{self.current_version}.tar.xz')
        # url = f"https://www.factorio.com/get-download/{self.current_version}/headless/linux64"
        # response = self.session.get(url)
        # response.raise_for_status()
        # LOG.debug(response)
        # with open(output_file, 'wb') as f:
        #     f.write(response.content)
        # LOG.info(f"Factorio server files downloaded to {output_file}")
        # return output_file

        file_name = f'factorio-headless_linux_{self.current_version}.tar.xz'
        output_file = os.path.join(output_dir, file_name)
        if self.current_version == '2.0.53':
            shutil.copyfile(
                os.path.join('/app', 'archives', file_name),
                os.path.join(output_file)
            )
        elif self.current_version == '2.0.55':
            shutil.copyfile(
                os.path.join('/app', 'archives', file_name),
                os.path.join(output_file)
            )
        return output_file

    def backup_factorio(self) -> str:
        """Backup the Factorio server files."""
        backup_dir = '/tmp/factorio_backup/'
        LOG.info("Backing up Factorio server files to %s", backup_dir)
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        shutil.copytree(self.factorio.factorio_dir, backup_dir, dirs_exist_ok=True)
        LOG.info("Backup completed successfully to %s", backup_dir)
        return backup_dir

    def install_factorio(self):
        """Install the Factorio server files."""

        # To-DO: Remove the backup functionality as all required files are mounted and symlinked which will be preserved
        backup_dir = None
        if os.path.exists(self.factorio.factorio_dir):
            backup_dir = self.backup_factorio()
            LOG.info('Removing old Factorio directory')
            shutil.rmtree(self.factorio.factorio_dir)

        download_loc = self.download_factorio()
        LOG.info("Installing Factorio server files from %s to %s", download_loc, self.factorio.factorio_dir)
        if not os.path.exists(self.factorio.factorio_dir):
            os.makedirs(self.factorio.factorio_dir)
        shutil.unpack_archive(download_loc, '/opt', 'tar')
        os.remove(download_loc)

        LOG.info("Creating necessary directories in %s", self.factorio.factorio_dir)
        os.makedirs(self.factorio.mods_dir, exist_ok=True)
        os.makedirs(self.factorio.saves_dir, exist_ok=True)
        os.makedirs(self.factorio.scenarios_dir, exist_ok=True)
        os.makedirs(self.factorio.config_dir, exist_ok=True)
        os.symlink(self.factorio.scenarios_dir,
                   os.path.join(self.factorio.factorio_dir, 'scenarios'),
                   target_is_directory=True)
        os.symlink(self.factorio.saves_dir,
                   os.path.join(self.factorio.factorio_dir, 'saves'),
                   target_is_directory=True)
        os.symlink(self.factorio.config_dir,
                   os.path.join(self.factorio.factorio_dir, 'config'),
                   target_is_directory=True)
        shutil.copyfile(os.path.join('/app', 'config.ini'), os.path.join(self.factorio.config_dir, 'config.ini'))

        LOG.info("Setting permissions for Factorio server files in %s and %s",
                 self.factorio.factorio_dir,
                 self.factorio.mount_dir)
        os.system(f'chown -R {os.environ["PUID"]}:{os.environ["PGID"]} {self.factorio.factorio_dir}')
        os.system(f'chown -R {os.environ["PUID"]}:{os.environ["PGID"]} {self.factorio.mount_dir}')

        if backup_dir:
            shutil.rmtree(backup_dir)

    def run(self):
        """Run the Manager to start the Factorio server."""
        running = True
        last_updated_check = time.time()
        while running:
            if not os.path.exists(self.factorio.factorio_dir):
                LOG.info("Factorio server files not found, downloading...")
                self.install_factorio()
                self.factorio.start(self.factorio.generate_config())

            if time.time() - last_updated_check > (60):  # Check for updates every hour
                LOG.info("Checking for Factorio server updates...")
                if self.current_version != self.get_latest_releases():
                    LOG.info("Current version %s does not match expected version %s.",
                             self.current_version, self.factorio.version)
                    if self.factorio.is_players_online():
                        LOG.info("Players are online, cannot update Factorio server files.")
                        continue
                    LOG.info('Stopping Factorio server to update files...')
                    self.factorio.stop()
                    LOG.info("Updating Factorio server files...")
                    self.current_version = self.get_latest_releases()
                    self.install_factorio()
                    self.factorio.start(self.factorio.generate_config())
                else:
                    LOG.debug("Factorio server is up to date with version")
                last_updated_check = time.time()

            if not self.factorio.is_running:
                LOG.info("Factorio server is not running, starting...")
                self.factorio.start(self.factorio.generate_config())
            # time.sleep(60)
            time.sleep(5)
            LOG.debug("Finished running loop iteration, sleeping for 60 seconds.")

    def get_latest_releases(self) -> str:
        """Fetch the latest Factorio releases from the API."""
        url = "https://factorio.com/api/latest-releases"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()[self.factorio.version]['headless']
        except requests.RequestException as e:
            LOG.error("Error fetching latest releases: %s", e)
            raise requests.RequestException("Failed to fetch latest releases from Factorio API") from e


def main():
    """Main function to run the Manager."""
    manager = Manager()
    LOG.info("Manager initialized successfully.")
    try:
        manager.run()
    except KeyboardInterrupt:
        if manager.factorio.is_running:
            LOG.info("KeyboardInterrupt received, stopping Factorio server...")
            manager.factorio.stop()
            LOG.info("Factorio server stopped successfully.")


if __name__ == "__main__":
    main()
