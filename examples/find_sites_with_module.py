#!/usr/bin/env python

from drush import Drush

def get_site_aliases(drupal_root=None):
    drush = Drush()
    aliases = drush.sa(local=True, fields=['name','root'])
    if drupal_root is not None:
        if drupal_root[-1] == '/':
            drupal_root = drupal_root[:-1]
        aliases = [name for name, alias in aliases.items() if alias['root'] == drupal_root and alias['context_type'] == 'site']
    else:
        aliases = aliases.keys()
    return aliases

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Print out the site aliases for all the sites with the given module enabled')
    parser.add_argument('module', help='the module to check for')
    parser.add_argument('--root', '-r', default=None)
    args = parser.parse_args()

    for alias in get_site_aliases(args.root):
        drush = Drush(alias=alias)
        info = drush.pm_info(args.module)
        if info and info.has_key(args.module) and info[args.module]['status'] == 'enabled':
            print alias

if __name__ == '__main__': main()

