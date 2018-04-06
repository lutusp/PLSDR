@echo off

echo Launching PLSDR ...

cd ..

set pp=%cd%

set prefix=\program files\

dir /b "%prefix%" | findstr -i gnuradio > temp.xxx

set gnup=

set /p gnup= < temp.xxx

del temp.xxx

if not defined gnup (
echo Error: GnuRadio not found. Please install GnuRadio.
goto noscript
)

set gnup=%prefix%%gnup%

echo GnuRadio located at %gnup%, proceeding ...

REM --- Set Python environment ---

set PYTHONHOME=%gnup%\gr-python27
set PYTHONPATH=%gnup%\gr-python27\Lib\site-packages;%gnup%\gr-python27\dlls;%gnup%\gr-python27\libs;%gnup%\gr-python27\lib;%gnup%\lib\site-packages;%gnup%\gr-python27\Lib\site-packages\pkgconfig;%gnup%\gr-python27\Lib\site-packages\gtk-2.0\glib;%gnup%\gr-python27\Lib\site-packages\gtk-2.0;%gnup%\gr-python27\Lib\site-packages\wx-3.0-msw;%gnup%\gr-python27\Lib\site-packages\sphinx;%gnup%\gr-python27\Lib\site-packages\lxml-3.4.4-py2.7-win.amd64.egg

set PATH=%gnup%;%gnup%\gr-python27\dlls;%gnup%\gr-python27;%PATH%

REM --- Set GRC environment ---
set GRC_BLOCKS_PATH=%gnup%\share\gnuradio\grc\blocks

REM --- Set UHD environment ---
set UHD_PKG_DATA_PATH=%gnup%\share\uhd;%gnup%\share\uhd\images
set UHD_IMAGES_DIR=%gnup%\share\uhd\images

rem if "%1"=="" goto noscript

rem test that Qt5 library is installed

python -c "import PyQt5" >nul 2>&1 && (
  rem OK to launch
  cd %gnup%\bin
  "%gnup%\gr-python27\python.exe" "%pp%\PLSDR.py"
  goto done
) || (
  rem Remind the user
  echo Error: Please install Qt5 library.
  goto noscript
)

:noscript

set /p x="Press Enter:"

:done
