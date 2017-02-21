#Chroot rebuild for packages from distinct repo (provided as .deb source package)

###Make build from root of directory
```
sudo apt-get install devscripts
```

```
debuild -us -uc
```
or
```
debuild clean
```

Then you can see package in ../ dir

Install with

```
dpkg -i orchestra_1.0_all.deb
sudo apt-get install -f (to force depenencies)
```

As it's a test task, so things that are not included in task are not automated, sorry, but you need to have
deb repo up and running somewhere.. ;(

1) https://www.howtoforge.com/setting-up-an-apt-repository-with-reprepro-and-nginx-on-debian-wheezy
Good manual to get local repo with nginx.
After nginx is up add apt.example.com to /etc/hosts
2) Download and include packages dependent on each other in your repo, for example:

testing|main|amd64: bash 4.2+dfsg-0.1+deb7u4
testing|main|amd64: libcomerr2 1.42.5-1.1+deb7u1
testing|main|amd64: mc 3:4.8.3-10
testing|main|amd64: mc-data 3:4.8.3-10
testing|main|amd64: mc-dbg 3:4.8.3-10
testing|main|source: e2fsprogs 1.42.5-1.1+deb7u1
testing|main|source: gawk 1:4.1.1+dfsg-1
testing|main|source: glibc 2.19-18+deb8u7
testing|main|source: mc 3:4.8.3-10

Include source packages:
```
cd /var/packages/debian
sudo reprepro includedsc testing $PACKAGES_PATH/*.dsc
```
or .deb, as described in manual
```
sudo reprepro includedeb testing $PACKAGES_PATH/*.deb
```

then use
```
./orchestra.py -r apt.example.com -p packages -W
```
