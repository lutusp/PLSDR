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

rem if "%1"=="" goto noscript

rem test that Qt5 library is installed

python -c "import PyQt5" >nul 2>&1 && (
  rem OK to launch
  cd %pp%\bin
  "%pp%\gr-python27\python.exe" \PLSDR\PLSDR\PLSDR.py
  goto done
) || (
  rem Remind the user
  echo *** Error: Please install Qt5 library. ***
  goto noscript
)

:noscript

set /p x="Press Enter:"

:done
