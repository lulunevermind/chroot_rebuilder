#!/usr/bin/python
import argparse

#
# Default params
#
parser = argparse.ArgumentParser(description='Rebuild packages from repo in chroot')
parser.add_argument('-r', '--repo', help='Provided repository path', required=True)
parser.add_argument('-pl', '--packageslist', help='List of valid .deb packages to rebuild', required=True)


def get_packages(filename):
    with open(filename) as f:
        return f.read()

if __name__ == '__main__':
    args = parser.parse_args()
    print args.repo, get_packages(args.packageslist)
