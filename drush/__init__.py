
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

#
# TODO: We could do some magic with meta-classes that would allow __doc__ strings on
#       commands to show actually useful information to Python developers... Is it
#       worth it?
#

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

        self.__commands = {}
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
        if alias is not None:
            try:
                self.__alias_info = self('site-alias', ['@' + alias], use_alias=False)
            except DrushCommandException:
                raise DrushCommandException('Invalid alias: ' + alias)

        self.__alias = alias
        self.__load_command_methods()

    def __call__(self, command, args = None, opts = None, use_alias = True):
        # TODO: this should use the --backend argument so we can seperate out messages!

        full_args = [self.__drush]
        if use_alias:
            if use_alias is True:
                use_alias = self.__alias
            if use_alias is not None:
                full_args += ['@' + use_alias]
        full_args += [command]
        if args is not None:
          full_args += args
        if opts is None:
            opts = {}
        opts['format'] = 'json'
        for k, v in opts.items():
            if v is True:
                full_args += ['--%s' % k]
            elif v is False:
                pass
            else:
                full_args += ['--%s=%s' % (k, v)]

        popen = subprocess.Popen(full_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = popen.communicate()
        if popen.returncode == 0:
            return json.loads(stdout)
        else:
            raise DrushCommandException(('Unable to run command "%s":' % ' '.join(full_args)) + stderr)

    def __load_command_methods(self):
        for name, command in self.__commands.items():
            self.__detach_command(command)

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

        self.__commands[command.name] = command

    def __detach_command(self, command):
        names = [command.name] + command.aliases
        for name in names:
            delattr(self, name)

        del self.__commands[command.name]

    def site_set(self, site):
        self.__set_alias(site)

    def __get__(self, name):
        msg = 'No command named "%s"' % name
        if self.__alias is not None:
            msg = msg + " (alias: %s)" % self.__alias
        raise DrushCommandException(msg)

class DrushCommand(object):
    """A callable object which executes a specific Drush command."""

    def __init__(self, drush, info):
        self.drush = drush
        self.command = info['command']
        self.aliases = info['aliases']
        self.hidden = info['hidden']
        self.scope = info['scope']
        self.info = info

        self.name = self.command.replace('-', '_')

        self.__setup_arguments()

    def __setup_arguments(self):
        self.options = {}

        if len(self.info['options']) == 0:
            return

        for real_name, description in self.info['options'].items():
            name = real_name.replace('-', '_')
            self.options[name] = {
                'real_name': real_name,
                'description': description,
            }

    def __call__(self, *args, **opts):
        real_opts = {}
        for name, value in opts.items():
            real_opts[self.options[name]['real_name']] = value
        return self.drush(self.command, list(args), opts)

