@echo off
"C:\Program Files (x86)\WinSCP\WinSCP.com" ^
  /log="C:\workspace\Python\ftpsync\winscp_script\dalianbei.log" /ini=nul ^
  /loglevel=0 /logsize=1*5M ^
  /command ^
    "open ftp://cchbds:hbds2005@192.168.3.98/" ^
    "echo connected" ^
    "cd /ftp_sync_test" ^
    "echo in /ftp_sync_test" ^
    "lcd C:\sync_test\daliangbei" ^
    "get -delete eel" ^
    "close" ^
    "exit"

set WINSCP_RESULT=%ERRORLEVEL%
if %WINSCP_RESULT% equ 0 (
  echo Success
) else (
  echo Error
)

exit /b %WINSCP_RESULT%