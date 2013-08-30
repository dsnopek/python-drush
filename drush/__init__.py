
import subprocess
import re
import json

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

class DrushCommandException(Exception):
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

    def __call__(self, command, args = None, opts = None):
        # TODO: this should use the --backend argument so we can seperate out messages!
        if args is None:
            args = []
        args = [command] + args
        if self.__alias is not None:
            args = ['@' + self.__alias] + args
        if opts is None:
            opts = {}
        opts['format'] = 'json'
        for k, v in opts.items():
            if v is True:
                args = args + ['--%s' % k]
            elif v is False:
                pass
            else:
                args = args + ['--%s=%s' % (k, v)]

        popen = subprocess.Popen([self.__drush] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = popen.communicate()
        if popen.returncode == 0:
            return json.loads(stdout)
        else:
            raise DrushCommandException(('Unable to run command "%s":' % ' '.join(args)) + stderr)

    def __load_command_methods(self):
        for module_name, module in self('help').items():
            for name, info in module['commands'].items():
                if name != 'site-set':
                    command = DrushCommand(self, info)
                    self.__attach_command(command)

    def __attach_command(self, command):
        names = [command.name] + command.aliases
        for name in names:
            if hasattr(self, name):
                raise DrushCommandException('Command already exists on Drush object: ' + name)
            setattr(self, name, command)

    def site_set(self, site):
        self.__set_alias(site)

class DrushCommand(object):
    """A callable object which executes a specific Drush command."""

    @property
    def name(self):
        return self.__name

    @property
    def command(self):
        return self.__command

    @property
    def aliases(self):
        return self.__aliases

    def __init__(self, drush, info):
        self.__drush = drush
        self.__command = info['command']
        self.__aliases = info['aliases']
        self.__hidden = info['hidden']
        self.__scope = info['scope']

        self.__name = self.__command.replace('-', '_')

        self.__setup_arguments(info)
        self.__setup_docstring(info)

        #import pprint
        #pprint.pprint(info)

    def __call__(self, *args, **opts):
        real_opts = {}
        for name, value in opts.items():
            real_opts[self.__options[name]['real_name']] = value
        return self.__drush(self.__command, list(args), opts)

    def __setup_arguments(self, info):
        self.__options = {}

        if len(info['options']) == 0:
            return

        for real_name, description in info['options'].items():
            name = real_name.replace('-', '_')
            self.__options[name] = {
                'real_name': real_name,
                'description': description,
            }
            
    def __setup_docstring(self, info):
        # TODO: this should take all the options and arguments into account!
        self.__doc__ = info['description']

