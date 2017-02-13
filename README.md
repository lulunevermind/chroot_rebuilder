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

then you can see package in ../ dir