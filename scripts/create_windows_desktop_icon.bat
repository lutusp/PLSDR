echo off

echo Building PLSDR desktop icon ...

cd ..

set pp=%cd%

echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%HOMEDRIVE%%HOMEPATH%\Desktop\PLSDR.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%pp%\scripts" >> CreateShortcut.vbs
echo oLink.TargetPath = "%pp%\scripts\launch_PLSDR.bat" >> CreateShortcut.vbs
echo oLink.IconLocation = "%pp%\icon\app_icon.ico, 0" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript CreateShortcut.vbs
rem del CreateShortcut.vbs

set /p x="Done, press Enter:"
