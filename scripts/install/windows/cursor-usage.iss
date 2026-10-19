; Cursor Usage Monitor — Windows installer (Inno Setup 6)
; AppVersion comes from pyproject.toml via build-installer.ps1 (/DAppVersion=...).
#ifndef AppVersion
  #define AppVersion "0.0.0-dev"
#endif
#ifndef RepoRoot
  #define RepoRoot "..\..\.."
#endif

#define AppName "Cursor Usage"
#define AppPublisher "Cursor Usage Monitor"
#define AppExeName "cursor-usage.exe"
#define DistDir RepoRoot + "\dist\cursor-usage"

[Setup]
AppId={{A7B3C9E1-4F2D-4A8B-9C0E-1D2E3F4A5B6C}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir={#RepoRoot}\release
OutputBaseFilename=CursorUsageSetup-{#AppVersion}-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile={#RepoRoot}\src\cursor_usage_app\assets\app-icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
LicenseFile={#RepoRoot}\LICENSE
InfoBeforeFile={#RepoRoot}\README-USER.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startup"; Description: "Start Cursor Usage when I sign in"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "redist\vc_redist.x64.exe"; Flags: dontcopy

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: startup

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
function VCRedistInstalled: Boolean;
var
  Installed: Cardinal;
begin
  if RegQueryDWordValue(HKLM, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Installed', Installed) then
  begin
    Result := (Installed = 1);
    Exit;
  end;
  if RegQueryDWordValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Installed', Installed) then
  begin
    Result := (Installed = 1);
    Exit;
  end;
  Result := False;
end;

procedure InstallVCRedistIfNeeded;
var
  ResultCode: Integer;
begin
  if VCRedistInstalled then
    Exit;
  if MsgBox(
    'This app requires the Microsoft Visual C++ 2015-2022 Redistributable (x64).' + #13#10 + #13#10 +
    'Install it now?',
    mbConfirmation, MB_YESNO) = IDNO then
    Exit;
  ExtractTemporaryFile('vc_redist.x64.exe');
  if not Exec(ExpandConstant('{tmp}\vc_redist.x64.exe'), '/install /quiet /norestart', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    MsgBox('Could not run the Visual C++ installer.', mbError, MB_OK);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
    InstallVCRedistIfNeeded;
end;
