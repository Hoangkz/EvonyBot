; EvonyBot.iss — Inno Setup script. Build with installer\build.ps1, which
; stages build\app first and passes /DAppVersion.
;
; Per-user install (no admin) into %LOCALAPPDATA%\EvonyBot. The database
; (evonybot.db) is created there at runtime and kept on uninstall.

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#define AppName "EvonyBot"
#define AppExe "{app}\python\pythonw.exe"

[Setup]
AppId={{69AE1A99-67B9-44F1-BBC9-3968A0F89A2E}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppName}
DefaultDirName={localappdata}\{#AppName}
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename={#AppName}-Setup-{#AppVersion}
SetupIconFile=..\Images\icon.ico
UninstallDisplayIcon={app}\Images\icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[InstallDelete]
; Upgrade: drop the previous runtime/code so no stale files are left behind.
Type: filesandordirs; Name: "{app}\python"
Type: filesandordirs; Name: "{app}\bot"
Type: filesandordirs; Name: "{app}\ui"
Type: filesandordirs; Name: "{app}\Images"
; Older builds shipped readable .py files at the top level.
Type: files; Name: "{app}\*.py"
Type: files; Name: "{app}\*.pyd"
Type: files; Name: "{app}\*.pyw"

[Files]
Source: "..\build\app\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{#AppExe}"; Parameters: """{app}\EvonyBot.pyw"""; WorkingDir: "{app}"; IconFilename: "{app}\Images\icon.ico"; AppUserModelID: "{#AppName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{#AppExe}"; Parameters: """{app}\EvonyBot.pyw"""; WorkingDir: "{app}"; IconFilename: "{app}\Images\icon.ico"; AppUserModelID: "{#AppName}"; Tasks: desktopicon

[Run]
Filename: "{#AppExe}"; Parameters: """{app}\EvonyBot.pyw"""; WorkingDir: "{app}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
; In-app update runs the installer with /SILENT /RELAUNCH: reopen the app afterwards.
Filename: "{#AppExe}"; Parameters: """{app}\EvonyBot.pyw"""; WorkingDir: "{app}"; Flags: nowait skipifnotsilent; Check: ShouldRelaunch

[UninstallDelete]
; __pycache__ folders are written at runtime, so the uninstaller doesn't know them.
Type: filesandordirs; Name: "{app}\python"
Type: filesandordirs; Name: "{app}\bot"
Type: filesandordirs; Name: "{app}\ui"
Type: filesandordirs; Name: "{app}\__pycache__"
Type: files; Name: "{app}\*.py"

[Code]
// Before files are replaced: wait for the closing app (it stops its bots
// first, which can take a while), then kill whatever still runs from
// {app}\python - notably the adb server that adbutils starts from its
// bundled adb.exe and that outlives the app. A locked adb.exe made the
// silent update fail with "Rolling back changes".
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
  Script: String;
begin
  Script :=
    '$d = ''' + ExpandConstant('{app}') + '\python\''; ' +
    '$t = (Get-Date).AddSeconds(20); ' +
    'while ((Get-Process pythonw, python -EA 0 | ? { $_.Path -like ($d + ''*'') }) -and (Get-Date) -lt $t) { Start-Sleep -Milliseconds 300 }; ' +
    'Get-Process adb, pythonw, python -EA 0 | ? { $_.Path -like ($d + ''*'') } | Stop-Process -Force; ' +
    'Start-Sleep -Milliseconds 500';
  Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -Command "' + Script + '"',
    '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := '';
end;

function ShouldRelaunch: Boolean;
var
  I: Integer;
begin
  Result := False;
  for I := 1 to ParamCount do
    if CompareText(ParamStr(I), '/RELAUNCH') = 0 then
      Result := True;
end;
