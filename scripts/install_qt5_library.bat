@echo off

echo Setting GnuRadio Python context ...

set prefix=\program files\

dir /b "%prefix%" | findstr -i gnuradio > temp.xxx

set pp=

set /p pp= < temp.xxx

del temp.xxx

if not defined pp (
echo *** Error: GnuRadio not found. ***
goto noscript
)

set pp=%prefix%%pp%

echo GnuRadio located at %pp%, proceeding ...

REM --- Set Python environment ---

set PYTHONHOME=%pp%\gr-python27
set PYTHONPATH=%pp%\gr-python27\Lib\site-packages;%pp%\gr-python27\dlls;%pp%\gr-python27\libs;%pp%\gr-python27\lib;%pp%\lib\site-packages;%pp%\gr-python27\Lib\site-packages\pkgconfig;%pp%\gr-python27\Lib\site-packages\gtk-2.0\glib;%pp%\gr-python27\Lib\site-packages\gtk-2.0;%pp%\gr-python27\Lib\site-packages\wx-3.0-msw;%pp%\gr-python27\Lib\site-packages\sphinx;%pp%\gr-python27\Lib\site-packages\lxml-3.4.4-py2.7-win.amd64.egg

set PATH=%pp%;%pp%\gr-python27\dlls;%pp%\gr-python27;%PATH%

REM --- Set GRC environment ---
set GRC_BLOCKS_PATH=%pp%\share\gnuradio\grc\blocks

REM --- Set UHD environment ---
set UHD_PKG_DATA_PATH=%pp%\share\uhd;%pp%\share\uhd\images
set UHD_IMAGES_DIR=%pp%\share\uhd\images

rem test that Qt5 library is installed

python -c "import PyQt5" >nul 2>&1 && (
  echo *** Qt5 Library is installed. ***
) || (
  net session >nul 2>&1 && (
    echo *** Installing Qt5 library ... ***
    "%pp%\gr-python27\scripts\pip-script.py" install python-qt5 
  ) || (
    echo *** Please run this script as administrator. ***
  )
)

set /p x="Press Enter:"
