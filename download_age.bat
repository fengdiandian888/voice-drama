@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
REM ============================================================
REM  下载 @mrlovewords9272 频道 55 个年龄墙视频的音频
REM
REM  ⚠️ 必须在【本机 cmd 命令提示符】里运行（Win+R → 输入 cmd）
REM     不要用 WorkBuddy 里的 Bash —— 那里是沙箱，
REM     yt-dlp 无法调用 node 解 nsig，会卡死。
REM
REM  原理：直接调用 WorkBuddy 自带的 yt-dlp-nightly.exe 和 node，
REM        在本机原生环境下 yt-dlp 才能正常调用 node 解开 nsig，
REM        并用 cookies 突破 YouTube 年龄墙。
REM ============================================================

set "YT=D:\WorkBuddy\2026-07-19-13-09-19\yt-dlp-nightly.exe"
set "NODE=C:\Users\Administrator\.workbuddy\binaries\node\versions\22.22.2"
set "PATH=%NODE%;%PATH%"
set "COOKIES=D:\WorkBuddy\2026-07-19-13-09-19\cookies_youtube.txt"
set "IDLIST=D:\WorkBuddy\2026-07-19-13-09-19\age_video_ids.txt"
set "OUT=D:\yt_age_videos"

if not exist "%OUT%" mkdir "%OUT%"

echo ============================================================
echo  检查环境...
echo ============================================================
node --version
if errorlevel 1 (
  echo [错误] 找不到 node，请确认路径存在：
  echo   %NODE%\node.exe
  pause
  exit /b 1
)
if not exist "%COOKIES%" (
  echo [错误] 找不到 cookies 文件：
  echo   %COOKIES%
  pause
  exit /b 1
)

echo.
echo ============================================================
echo  开始下载 55 个年龄墙视频音频
echo  （破年龄墙用 cookies，解 nsig 用本机 node）
echo  输出目录：%OUT%
echo ============================================================
set /a n=0
for /f %%i in (%IDLIST%) do (
  set /a n+=1
  echo.
  echo ==================================================
  echo  [!n!/55] %%i
  echo ==================================================
  "%YT%" --cookies "%COOKIES%" --extractor-args "youtube:player_client=tv" -x --audio-format wav -o "%OUT%\%%i.%%(ext)s" "https://www.youtube.com/watch?v=%%i"
)

echo.
echo ============================================================
echo  全部完成！音频已保存到：%OUT%
echo  回到 WorkBuddy 让 AI 转写这些音频即可。
echo ============================================================
pause
