# PLSDR

Software-defined radio application written in Python

Home page with full documentation and tutorial: https://arachnoid.com/PLSDR/

In Version 1.8, in response to user feedback, fixed some problems with Windows installation so the app can be installed anywhere the user cares to put it and it will still run.

In verson 1.9, changed default audio device to "" (which invokes the system default) after user problems with the earlier value. It turns out that the original default of "plughw:0,0" is only recognized by certain Linux distributions and causes a failure in others.
