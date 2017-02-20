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

then use
```
./orchestra.py -r apt.example.com -p packages -W
```
where apt.example.com is local repo for rebuilded packages (DIY experience)
https://www.howtoforge.com/setting-up-an-apt-repository-with-reprepro-and-nginx-on-debian-wheezy

after nginx is up add apt.example.com to /etc/hosts
