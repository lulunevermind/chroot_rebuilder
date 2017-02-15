#!/usr/bin/python
import argparse
import os

#
# Repo located in /var/packages - do get valid debian packages
#

#
# Default params
#
parser = argparse.ArgumentParser(description='Rebuild packages from repo in chroot')
parser.add_argument('-r', '--repo', help='Provided repository path', required=True)
# parser.add_argument('-pl', '--packageslist', help='List of valid .deb packages to rebuild', required=True)
parser.add_argument('-W', '--wipe', action="store_true", help='Provided repository path', required=False)

CHRPREFIX = "sudo chroot /stable-temp-jail /bin/bash -c '%s'"

REBUILD_DIR = "/home/rebuild/"


def get_packages(filename):
    with open(filename) as f:
        return f.read()


def jail_exec(command, comment, check):
    print '>>  %s' % comment
    os.system(CHRPREFIX % command)
    #TODO: do a check


def host_exec(command, comment, check):
    print comment
    os.system(command)


def make_deb_chroot(apt_repo):
    if args.wipe:
        host_exec(command='sudo rm -rf /stable-temp-jail',
                  comment='Wiping environment in /stable-temp-jail...',
                  check=None)

    host_exec(command='sudo debootstrap stable /stable-temp-jail http://deb.debian.org/debian/',
              comment='Creating jail...',
              check=None)

    jail_exec(command='echo "127.0.0.1   %s" >> /etc/hosts' % apt_repo,
              comment='Adding vhost repo to hosts...',
              check=None)

    jail_exec(command='wget -O - -q http://%s/apt.example.com.gpg.key | apt-key add -' % apt_repo,
              comment='Getting pgp key...',
              check=None)

    jail_exec(command='echo "deb http://%s/debian testing main" >> /etc/apt/sources.list' % apt_repo,
              comment='Adding repo to source.list...',
              check=None)

    jail_exec(command='echo "deb-src http://%s/debian testing main" >> /etc/apt/sources.list' % apt_repo,
              comment='Adding repo to source.list...',
              check=None)

    jail_exec(command="apt-get update",
              comment='Updating repos...',
              check=None)

    jail_exec(command='''cat <<EOT >> /etc/apt/preferences.d/preferences
Package: *
Pin: origin %s
Pin-Priority: 1001
EOT''' % apt_repo,
              comment='',
              check=None)

    jail_exec(command='apt-get install build-essential devscripts -y',
              comment='Installing required build-deps',
              check=None)


def rebuild_package(pkg):
    jail_exec(command='mkdir -p %s' % REBUILD_DIR,
              comment='Creating home dir for packages rebuild...',
              check=None)

    jail_exec(command='cd %s && apt-get source %s' % (REBUILD_DIR, pkg),
              comment='Download package source...',
              check=None)

    jail_exec(command='cd %s*' % pkg,
              comment='Cd to pkg dir %s*...' % pkg,
              check=None)

    jail_exec(command='cd %s%s* && apt-get build-dep %s -y' % (REBUILD_DIR, pkg, pkg),
              comment='Get build-deps...',
              check=None)

    jail_exec(command='cd %s%s* && debuild -us -uc' % (REBUILD_DIR, pkg),
              comment='Rebuild...',
              check=None)


if __name__ == '__main__':
    args = parser.parse_args()
    # make_deb_chroot(args.repo)
    rebuild_package('mc')
