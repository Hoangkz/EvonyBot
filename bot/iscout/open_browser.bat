@echo off
rem Open the browser the bot reads iScout bosses from (DevTools port 9222). Log in once; the profile keeps the session.
rem Any Chromium browser works (Chrome, Edge, Brave, Coc Coc); the first one found is used. Firefox is not supported.
rem Keep this browser open while the bot runs.
rem Optional: pass the browser exe as the first argument (open_browser.bat "D:\Apps\msedge.exe") when it is not installed in a default folder.
set "PROFILE=%USERPROFILE%\iscout_browser"
if not "%~1"=="" call :try "%~1" && exit /b 0
call :try "%ProgramFiles%\Google\Chrome\Application\chrome.exe" && exit /b 0
call :try "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" && exit /b 0
call :try "%LocalAppData%\Google\Chrome\Application\chrome.exe" && exit /b 0
call :try "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" && exit /b 0
call :try "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" && exit /b 0
call :try "%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe" && exit /b 0
call :try "%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe" && exit /b 0
call :try "%ProgramFiles%\CocCoc\Browser\Application\browser.exe" && exit /b 0
call :try "%LocalAppData%\CocCoc\Browser\Application\browser.exe" && exit /b 0
echo Khong tim thay Chrome, Edge, Brave hay Coc Coc. Hay cai mot trinh duyet nen Chromium.
pause
exit /b 1

:try
if exist %1 (
    start "" %1 --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="%PROFILE%" --no-first-run --no-default-browser-check https://www.iscout.club/vi/dashboard
    exit /b 0
)
exit /b 1
