#!/usr/bin/python
import argparse
import os

#
# Repo located in /var/packages - do get valid debian packages
#

# DEPENDENCIES FOR PACKAGE !!!!!!!!!!!!!!

# Use for include SRC             sudo reprepro -b /var/packages/debian/ includedsc testing *.dsc
# Use for include DEB             sudo reprepro -b /var/packages/debian/ includedeb testing *.deb

#
# Default params
#
import subprocess
from subprocess import CalledProcessError

parser = argparse.ArgumentParser(description='Rebuild packages from repo in chroot')
parser.add_argument('-r', '--repo', help='Provided repository path', required=True)
parser.add_argument('-p', '--packageslist', help='File with packages to rebuild', required=True)
parser.add_argument('-W', '--wipe', action="store_true", help='Provided repository path', required=False)

CHRPREFIX = "sudo chroot /stable-temp-jail /bin/bash -c '%s'"

JAIL_PATH = "/stable-temp-jail"
REBUILD_DIR = "/home/rebuild/"
PKG_RDY_DIR = "/var/packages/"
SHARED_DIR = "/var/shared-packages"
REPREPRO_PATH = "/var/packages/debian"


def get_packages(filename):
    with open(filename) as f:
        return f.read()


def jail_exec(command, comment, check=None):
    print '>>  %s' % comment
    os.system(CHRPREFIX % command)
    #TODO: do a check


def host_exec(command, comment, check=None):
    print '>>  %s' % comment
    os.system(command)


def get_stdout_exec(command, comment, check=None):
    res = ''
    print '>>  %s' % comment
    try:
        res = subprocess.check_output(command, shell=True)
    except CalledProcessError:
        # Non-zero status in bash process when no result are yielded??!
        pass
    return res


def make_deb_chroot(apt_repo):
    if args.wipe:
        host_exec(command='sudo umount %s%s' % (JAIL_PATH, SHARED_DIR),
                  comment='Unmount shared dir...',)

        host_exec(command='sudo rm -rf /stable-temp-jail',
                  comment='Wiping environment in /stable-temp-jail...',)

    host_exec(command='sudo debootstrap stable /stable-temp-jail http://deb.debian.org/debian/',
              comment='Creating jail from repo...',)

    jail_exec(command='echo "127.0.0.1   %s" >> /etc/hosts' % apt_repo,
              comment='Adding vhost repo to hosts...',)

    # For testing purposes repository provided for jail and repository for rebuilded changes is not the same thing
    jail_exec(command='wget -O - -q http://%s/apt.example.com.gpg.key | apt-key add -' % apt_repo,
              comment='Getting pgp key...',)

    jail_exec(command='echo "deb http://%s/debian testing main" >> /etc/apt/sources.list' % apt_repo,
              comment='Adding repo to source.list...',)

    jail_exec(command='echo "deb-src http://%s/debian testing main" >> /etc/apt/sources.list' % apt_repo,
              comment='Adding repo to source.list...',)

    jail_exec(command="apt-get update",
              comment='Updating repos...',)

    jail_exec(command='''cat <<EOT >> /etc/apt/preferences.d/preferences
Package: *
Pin: origin %s
Pin-Priority: 1001
EOT''' % apt_repo,
              comment='',)

    jail_exec(command='mkdir -p %s' % PKG_RDY_DIR,
              comment='Making packages dir...',)

    jail_exec(command='mkdir -p %s' % SHARED_DIR,
              comment='Making shared dir from chroot to host...',)

    jail_exec(command='apt-get install build-essential devscripts -y',
              comment='Installing required build-deps',)

    jail_exec(command='export LANGUAGE="C"; export LC_ALL="C"',
              comment='Installing required build-deps',)

    # TODO: Here data is lost, umount from jail needed?
    host_exec(command='sudo mount --bind %s %s%s' % (SHARED_DIR, '/stable-temp-jail', SHARED_DIR),
              comment='Mounting dir for reprepro...',)


def rebuild_package(pkg, wipe=False):
    if wipe:
        jail_exec(command='rm -rf %s' % REBUILD_DIR,
                  comment='Removing rebuild directory...')

    jail_exec(command='mkdir -p %s' % REBUILD_DIR,
              comment='Creating home dir for packages rebuild...',)

    jail_exec(command='cd %s && apt-get source %s' % (REBUILD_DIR, pkg),
              comment='Download package source...',)

    jail_exec(command='cd %s*' % pkg,
              comment='Cd to pkg dir %s*...' % pkg,)

    jail_exec(command='cd %s%s* && apt-get build-dep %s -y' % (REBUILD_DIR, pkg, pkg),
              comment='Get build-deps...',)

    jail_exec(command='cd %s%s* && debuild -us -uc' % (REBUILD_DIR, pkg),
              comment='Rebuilding...',)

    # from host
    jail_exec(command='cd %s && cp %s* %s' % (REBUILD_DIR, pkg, SHARED_DIR),
              comment='Copying all debs to delivery place..')

    host_exec(command='cd %s && sudo reprepro -A amd64 remove testing %s' % (REPREPRO_PATH, pkg),
              comment='Removing amd64 packages from repo...')

    host_exec(command='cd %s && sudo reprepro includedeb testing %s/*.deb' % (REPREPRO_PATH, SHARED_DIR),
              comment='Including new packages...')

    host_exec(command='cd %s && sudo reprepro export' % REPREPRO_PATH,
              comment='Export changes')

    host_exec(command='cd %s && sudo rm -rf %s*' % (SHARED_DIR, pkg),
              comment='')

    # TODO: Handle including more than one package produced... (mc-dbg, mc-data for example)

    # apt-cache showsrc mc | grep ^Build-Depends
    # apt-cache depends bash | grep Depends


class Node:
    def __init__(self, name):
        self.name = name
        self.edges = []

    def add_edge(self, node):
        self.edges.append(node)


def get_deps_list(package):
    dep_list = get_stdout_exec(command='apt-cache depends %s | grep Depends' % package,
                               comment='Getting list of dependencies for %s' % package)
    dep_list = dep_list.split('\n')
    # stripping and splitting if el is not empty
    dep_list = [el.split(':')[1].strip() for el in dep_list if el]
    return dep_list


def make_tree(packages):
    for p in packages:
        deps = get_deps_list(p)
        print deps


if __name__ == '__main__':
    args = parser.parse_args()
    # make_deb_chroot(args.repo)
    # rebuild_package('mc', wipe=True)
    make_tree()
