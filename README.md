# PLSDR

Software-defined radio application written in Python

Home page with full documentation and tutorial: https://arachnoid.com/PLSDR/

In Version 1.8, in response to user feedback, fixed some problems with Windows installation so the app can be installed anywhere the user cares to put it and it will still run.

In verson 1.9, changed default audio device to "" (which invokes the system default) after user problems with the earlier value. It turns out that the original default of "plughw:0,0" is only recognized by certain Linux distributions and causes a failure in others.

Version 2.0. Now that GNURadio 3.8 is generally available, this version uses Python 3.+ and GNURadio 3.8+. While converting, fixed a few small bugs.

NOTE: If you want to download the new version, visit my PLSDR web page (https://arachnoid.com/PLSDR/), it's easier than trying to make Github do anything coherent. I just wasted an hour trying to change one file.
