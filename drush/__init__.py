
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
    """An interface to the Drush command-line program - requires Drush 6 or later."""

    def __init__(self, drush=None, alias=None, verify=True, load_command_methods=True):
        if drush is None:
            if verify:
                drush = ['drush6','drush']
            else:
                drush = 'drush'

        if verify:
            (self.__drush, self.__version_string, self.__version) = self.__find_drush(drush)
        else:
            if type(drush) is list:
                drush = drush[0]
            self.__drush = drush
            self.__version_string = None
            self.__version = None

        self.__has_command_methods = load_command_methods
        self.__set_alias(alias)

    @property
    def _drush(self):
        return self.__drush

    @property
    def _version(self):
        return self.__version

    @property
    def _version_string(self):
        return self.__version_string

    @property
    def _alias(self):
        return self.__alias

    @property
    def has_command_methods(self):
        return self.__has_command_methods

    def __get_drush_version(self, drush):
        """Attempts to run drush (via the given command) in order to get it's version.
        Returns a tuple containing the version string and an list of integers."""

        # Attempt to run the command and verify it's version
        popen = subprocess.Popen([drush, '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        popen.wait()
        if popen.returncode == 0:
            output = popen.stdout.read()
            if output is not None:
                return self.__parse_drush_version(output)

        return (None, None)

    def __parse_drush_version(self, output):
        # This regex will work for Drush 4, 5 and 6
        match = re.search(r'[Dd]rush [Vv]ersion\s+(?::\s+)?([\d\.]+)', output)
        if match is not None:
            version_string = match.group(1)
            version = [int(x) for x in version_string.split('.')]
            return (version_string, version)

        return (None, None)

    def __find_drush(self, possibilities):
        """Takes a list of possible drush commands and tries run them each in turn. The first to work
        and return valid version will be used. Returns a tuple containing the command, version string and
        version list."""

        if type(possibilities) is not list:
            possibilities = [possibilities]

        for drush in possibilities:
            version_string, version = self.__get_drush_version(drush)
            if version is not None:
                if version[0] >= 6:
                    return (drush, version_string, version)
                else:
                    raise DrushVersionException('Drush 6.x or higher is required. Found: ' + version_string)

        raise DrushNotFoundException('Unable to find Drush command')

    def __set_alias(self, alias):
        # TODO: verify that this is a valid alias (or None)
        
        self.__alias = alias

        self.__load_command_methods()

    def __call__(self, command, args, opts):
        pass

    def __load_command_methods(self):
        pass

    def site_set(self, site):
        self.__set_alias(site)

class DrushCommand(object):
    """A callable object which executes a specific Drush command."""

    def __init__(self, info):
        pass


