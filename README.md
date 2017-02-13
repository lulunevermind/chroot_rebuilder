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