
import subprocess
import re

#try:
#    from cStringIO import StringIO
#except ImportError:
#    from StringIO import StringIO

class DrushException(Exception):
    pass

class DrushNotFoundException(Exception):
    pass

class DrushVersionException(Exception):
    pass

class Drush(object):
    """An interface to the Drush command. Depends on Drush 6."""

    def __init__(self, command=None, alias=None):
        self.command = self.__find_drush(command)
        self.__check_alias(alias)
        self.alias = alias

    # TODO: Use https://code.google.com/p/which/ to find the full command name.
    def __find_drush(self, command):
        """Takes a command name and verifies that it's a valid Drush 6 (or later) executable.
           Returns the command name (possibly modified) which will execute correctly."""

        if command is None:
            for possibility in ['drush6', 'drush']:
                try:
                    path = self.__find_drush(possibility)
                    break
                except DrushNotFoundException:
                    path = None

            if path is not None:
                return path

        else:
            # Attempt to run the command and verify it's version
            popen = subprocess.Popen([command, '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            popen.wait()
            if popen.returncode == 0:
                version = popen.stdout.read()
                if version is not None:
                    # This regex will work for Drush 4, 5 and 6
                    match = re.search(r'[Dd]rush [Vv]ersion\s+(?::\s+)?([\d\.]+)', version)
                    if match is not None:
                        parts = match.group(1).split('.')
                        if int(parts[0]) < 6:
                            raise DrushVersionException('Drush 6.x or higher is required. Found: ' + version)
                        return command

        raise DrushNotFoundException('Unable to find Drush command')

    def __check_alias(self, alias):
        pass

