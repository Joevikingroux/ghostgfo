; Ghost CFO Agent — Inno Setup Installer Script
; Compile with Inno Setup 6.x:  iscc ghostcfo_agent.iss
;
; Build the exe first:
;   cd agent && pyinstaller build.spec
; Generate the icon first:
;   python assets/generate_icon.py
;
; Output: installer\Output\GhostCFOAgentSetup.exe

#define AppName      "Ghost CFO Agent"
#define AppVersion   "1.3.0"
#define AppPublisher "Numbers10 Technology Solutions"
#define AppURL       "https://ghostcfo.numbers10.co.za"
#define ExeName      "GhostCFOAgent.exe"
#define InstallDir   "C:\GhostCFO"

[Setup]
AppId={{A3F8C2D1-7E4B-4A9F-B6D2-1C5E8F3A9B7C}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
DefaultDirName={#InstallDir}
DisableDirPage=yes
DefaultGroupName=Ghost CFO
OutputDir=Output
OutputBaseFilename=GhostCFOAgentSetup
SetupIconFile=..\assets\ghostcfo.ico
WizardImageFile=..\assets\ghostcfo_256.png
WizardSmallImageFile=..\assets\ghostcfo_256.png
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=admin
UninstallDisplayIcon={#InstallDir}\{#ExeName}
UninstallDisplayName={#AppName}
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription=Ghost CFO Agent — Pastel Evolution connector

; Windows 10 / Server 2016 minimum
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

; ---------------------------------------------------------------------------
; Custom wizard page — collect API key + SQL Server details
; ---------------------------------------------------------------------------

[Code]
var
  ConfigPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  ConfigPage := CreateInputQueryPage(
    wpWelcome,
    'Ghost CFO Configuration',
    'Enter the details provided by Numbers10 Technology Solutions.',
    ''
  );
  ConfigPage.Add('API Key (provided by Numbers10):', False);
  ConfigPage.Add('AES Encryption Key (provided by Numbers10):', False);
  ConfigPage.Add('SQL Server name or IP\instance:', False);
  ConfigPage.Add('Pastel Evolution database name:', False);
  ConfigPage.Add('SQL Server username:', False);
  ConfigPage.Add('SQL Server password:', True);
  ConfigPage.Add('Ghost CFO portal URL:', False);

  ConfigPage.Values[6] := 'https://ghostcfo.numbers10.co.za';
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = ConfigPage.ID then begin
    if Trim(ConfigPage.Values[0]) = '' then begin
      MsgBox('API Key is required.', mbError, MB_OK);
      Result := False;
    end else if Trim(ConfigPage.Values[1]) = '' then begin
      MsgBox('AES Encryption Key is required.', mbError, MB_OK);
      Result := False;
    end else if Trim(ConfigPage.Values[2]) = '' then begin
      MsgBox('SQL Server name is required.', mbError, MB_OK);
      Result := False;
    end else if Trim(ConfigPage.Values[3]) = '' then begin
      MsgBox('Database name is required.', mbError, MB_OK);
      Result := False;
    end else if Trim(ConfigPage.Values[4]) = '' then begin
      MsgBox('SQL Server username is required.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function GetAPIKey(Param: String): String;
begin Result := Trim(ConfigPage.Values[0]); end;

function GetEncKey(Param: String): String;
begin Result := Trim(ConfigPage.Values[1]); end;

function GetSQLServer(Param: String): String;
begin Result := Trim(ConfigPage.Values[2]); end;

function GetDBName(Param: String): String;
begin Result := Trim(ConfigPage.Values[3]); end;

function GetSQLUser(Param: String): String;
begin Result := Trim(ConfigPage.Values[4]); end;

function GetSQLPass(Param: String): String;
begin Result := Trim(ConfigPage.Values[5]); end;

function GetBaseURL(Param: String): String;
begin
  Result := Trim(ConfigPage.Values[6]);
  if Result = '' then Result := 'https://ghostcfo.numbers10.co.za';
end;

[Files]
; Main executable (compiled by PyInstaller)
Source: "..\dist\{#ExeName}"; DestDir: "{#InstallDir}"; Flags: ignoreversion

; Icon for shortcuts
Source: "..\assets\ghostcfo.ico"; DestDir: "{#InstallDir}"; Flags: ignoreversion

; ---------------------------------------------------------------------------
; Shortcuts
; ---------------------------------------------------------------------------

[Icons]
; Desktop shortcut — opens the portal
Name: "{userdesktop}\Ghost CFO"; \
  Filename: "{#InstallDir}\{#ExeName}"; \
  Parameters: "tray"; \
  IconFilename: "{#InstallDir}\ghostcfo.ico"; \
  Comment: "Ghost CFO Agent — click to open status tray"

; Start Menu entry
Name: "{group}\Ghost CFO Agent"; \
  Filename: "{#InstallDir}\{#ExeName}"; \
  Parameters: "tray"; \
  IconFilename: "{#InstallDir}\ghostcfo.ico"

Name: "{group}\View Agent Log"; \
  Filename: "notepad.exe"; \
  Parameters: "{#InstallDir}\agent.log"

Name: "{group}\Uninstall Ghost CFO Agent"; \
  Filename: "{uninstallexe}"

; ---------------------------------------------------------------------------
; Run at login — add tray app to HKCU Run key
; ---------------------------------------------------------------------------

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "GhostCFOTray"; \
  ValueData: """{#InstallDir}\{#ExeName}"" tray"; \
  Flags: uninsdeletevalue

; ---------------------------------------------------------------------------
; Post-install: write config.json + install Windows service + start tray
; ---------------------------------------------------------------------------

[Run]

; 1. Write config and register the Windows service
Filename: "{#InstallDir}\{#ExeName}"; \
  Parameters: "install --api-key=""{code:GetAPIKey}"" --server=""{code:GetSQLServer}"" --db=""{code:GetDBName}"" --username=""{code:GetSQLUser}"" --password=""{code:GetSQLPass}"" --encryption-key=""{code:GetEncKey}"" --base-url=""{code:GetBaseURL}"""; \
  Flags: runhidden waituntilterminated; \
  StatusMsg: "Installing Ghost CFO Agent and testing SQL connection…"

; 2. Start the service
Filename: "sc.exe"; \
  Parameters: "start GhostCFOAgent"; \
  Flags: runhidden waituntilterminated; \
  StatusMsg: "Starting Ghost CFO service…"

; 3. Launch tray icon immediately (no reboot required)
Filename: "{#InstallDir}\{#ExeName}"; \
  Parameters: "tray"; \
  Flags: nowait postinstall skipifsilent; \
  Description: "Launch Ghost CFO system tray icon now"

; ---------------------------------------------------------------------------
; Uninstall: stop + remove the service and tray
; ---------------------------------------------------------------------------

[UninstallRun]
Filename: "sc.exe"; Parameters: "stop GhostCFOAgent"; Flags: runhidden
Filename: "sc.exe"; Parameters: "delete GhostCFOAgent"; Flags: runhidden
Filename: "taskkill.exe"; Parameters: "/f /im {#ExeName}"; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{#InstallDir}"
