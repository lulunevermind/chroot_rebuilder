#!/usr/bin/python
import argparse
import os
import re

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
        return f.read().split('\n')


def jail_exec(command, comment, check=None):
    print '>>  %s' % comment
    os.system(CHRPREFIX % command)
    #TODO: do a check


def host_exec(command, comment, check=None):
    print '>>  %s' % comment
    os.system(command)


def get_stdout_host_exec(command, comment, check=None):
    res = ''
    print '>>  %s' % comment
    try:
        res = subprocess.check_output(command, shell=True)
    except CalledProcessError:
        # Non-zero status in bash process when no result are yielded??!
        pass
    return res


def get_stdout_jail_exec(command, comment, check=None):
    res = ''
    print '>>  %s' % comment
    try:
        res = subprocess.check_output(CHRPREFIX % command, shell=True)
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
              comment='Pinning repo...',)

    jail_exec(command='mkdir -p %s' % PKG_RDY_DIR,
              comment='Making packages dir...',)

    jail_exec(command='mkdir -p %s' % SHARED_DIR,
              comment='Making shared dir from chroot to host...',)

    jail_exec(command='apt-get install build-essential devscripts -y',
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


# https://www.electricmonk.nl/log/2008/08/07/dependency-resolving-algorithm/
# resolve via graphs

class Node:
    def __init__(self, name):
        self.name = name
        self.edges = []

    def add_edge(self, node):
        self.edges.append(node)


def search_tree(node, search_param):
    if node.name == search_param:
        return node
    else:
        for edge in node.edges:
            res = search_tree(edge, search_param)
            if res:
                return res


def visualize_tree(node):
    for edge in node.edges:
        print 'Node: %s, Edge: %s' % (node.name, edge.name)
        visualize_tree(edge)


def dep_resolve(node, resolved, seen):
    seen.append(node)
    for edge in node.edges:
        if edge not in resolved:
            if edge in seen:
                raise Exception('Circular reference detected: %s -> %s' % (node.name, edge.name))
        dep_resolve(edge, resolved, seen)
    resolved.append(node)


def get_deps_list(package):
    dep_list = get_stdout_jail_exec(command='apt-cache depends %s | grep Depends' % package,
                                    comment='Getting list of dependencies for %s' % package)
    dep_list = dep_list.split('\n')
    # stripping and splitting if el is not empty
    dep_list = [el.split(':')[1].strip() for el in dep_list if el]
    print dep_list
    return dep_list


def get_build_deps(package):
    build_deps = get_stdout_jail_exec(command='apt-cache showsrc %s | grep ^Build-Depends' % package,
                                      comment='Getting list of build-deps for %s' % package)
    prefix = 'Build-Depends:'
    if build_deps:
        build_deps = build_deps[len(prefix):].split(',')
        build_deps = [re.sub('\(.+\)|\[.+\]', '', dep) for dep in build_deps]
        build_deps = [dep.strip() for dep in build_deps]
    print build_deps
    return build_deps


def build_package_tree(r, packages):
    for p in packages:
        pn = Node(p)
        deps = get_deps_list(p)
        bdeps = get_build_deps(p)
        all_deps = deps + bdeps
        for d in all_deps:
            if d in packages:
                exists = search_tree(r, p)
                if exists:
                    exists.add_edge(Node(d))
                else:
                    r.add_edge(pn)
                    pn.add_edge(Node(d))
    return r


if __name__ == '__main__':
    args = parser.parse_args()
    packages = get_packages(args.packageslist)

    r = Node('root')

    build_package_tree(r, packages)
    visualize_tree(r)

    resolved = []
    dep_resolve(r, resolved, [])
    for node in resolved:
        print node.name


        # order = resolve_rebuild_order(get_packages(args.packageslist))
    # for p in order:
    #     make_deb_chroot(args.repo)
    #     rebuild_package(p, wipe=True)
