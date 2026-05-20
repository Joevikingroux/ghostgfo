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
#define AppVersion   "1.4.0"
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
; Two wizard pages — page 1: Ghost CFO credentials, page 2: SQL connection
; (splitting avoids field overflow / unclickable password box on one page)
; ---------------------------------------------------------------------------

[Code]
var
  CredPage: TInputQueryWizardPage;   { API Key + AES Encryption Key }
  SQLPage:  TInputQueryWizardPage;   { SQL Server, DB, Username, Password }

procedure InitializeWizard;
begin
  { Page 1 — Ghost CFO credentials provided by Numbers10 }
  CredPage := CreateInputQueryPage(
    wpWelcome,
    'Ghost CFO Credentials',
    'Enter the API Key and Encryption Key provided by Numbers10 Technology Solutions.',
    ''
  );
  CredPage.Add('API Key:', False);
  CredPage.Add('AES Encryption Key:', False);

  { Page 2 — SQL Server connection details }
  SQLPage := CreateInputQueryPage(
    CredPage.ID,
    'SQL Server Connection',
    'Enter the Pastel Evolution SQL Server details for this client.',
    ''
  );
  SQLPage.Add('SQL Server name or IP\instance  (e.g. SERVER\SQLEXPRESS):', False);
  SQLPage.Add('Pastel Evolution database name:', False);
  SQLPage.Add('SQL Server username:', False);
  SQLPage.Add('SQL Server password:', True);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = CredPage.ID then begin
    if Trim(CredPage.Values[0]) = '' then begin
      MsgBox('API Key is required.', mbError, MB_OK);
      Result := False;
    end else if Trim(CredPage.Values[1]) = '' then begin
      MsgBox('AES Encryption Key is required.', mbError, MB_OK);
      Result := False;
    end;
  end else if CurPageID = SQLPage.ID then begin
    if Trim(SQLPage.Values[0]) = '' then begin
      MsgBox('SQL Server name is required.', mbError, MB_OK);
      Result := False;
    end else if Trim(SQLPage.Values[1]) = '' then begin
      MsgBox('Database name is required.', mbError, MB_OK);
      Result := False;
    end else if Trim(SQLPage.Values[2]) = '' then begin
      MsgBox('SQL Server username is required.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function GetAPIKey(Param: String): String;
begin Result := Trim(CredPage.Values[0]); end;

function GetEncKey(Param: String): String;
begin Result := Trim(CredPage.Values[1]); end;

function GetSQLServer(Param: String): String;
begin Result := Trim(SQLPage.Values[0]); end;

function GetDBName(Param: String): String;
begin Result := Trim(SQLPage.Values[1]); end;

function GetSQLUser(Param: String): String;
begin Result := Trim(SQLPage.Values[2]); end;

function GetSQLPass(Param: String): String;
begin Result := Trim(SQLPage.Values[3]); end;

function GetBaseURL(Param: String): String;
begin Result := 'https://ghostcfo.numbers10.co.za'; end;

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
; Run at login — add tray app to HKLM Run key (all users, survives UAC elevation)
; HKCU can be written to the wrong hive when the installer runs elevated.
; HKLM\Run launches in each user's session on login, which is what we need.
; ---------------------------------------------------------------------------

[Registry]
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "GhostCFOTray"; \
  ValueData: """{#InstallDir}\{#ExeName}"" tray"; \
  Flags: uninsdeletevalue

; ---------------------------------------------------------------------------
; Post-install: write config.json + install Windows service + start tray
; ---------------------------------------------------------------------------

[Run]

; 1. Write config, register scheduled tasks, test SQL connection
Filename: "{#InstallDir}\{#ExeName}"; \
  Parameters: "install --api-key=""{code:GetAPIKey}"" --server=""{code:GetSQLServer}"" --db=""{code:GetDBName}"" --username=""{code:GetSQLUser}"" --password=""{code:GetSQLPass}"" --encryption-key=""{code:GetEncKey}"" --base-url=""{code:GetBaseURL}"""; \
  Flags: runhidden waituntilterminated; \
  StatusMsg: "Installing Ghost CFO Agent and testing SQL connection…"

; NOTE: install_service() already fires the poll task once immediately (schtasks /Run).
; No separate sc.exe start step needed — the agent uses Task Scheduler, not a Windows service.

; 2. Launch tray icon immediately (no reboot required)
Filename: "{#InstallDir}\{#ExeName}"; \
  Parameters: "tray"; \
  Flags: nowait postinstall skipifsilent; \
  Description: "Launch Ghost CFO system tray icon now"

; ---------------------------------------------------------------------------
; Uninstall: stop + remove the service and tray
; ---------------------------------------------------------------------------

[UninstallRun]
Filename: "{#InstallDir}\{#ExeName}"; Parameters: "uninstall"; Flags: runhidden waituntilterminated
Filename: "taskkill.exe"; Parameters: "/f /im {#ExeName}"; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{#InstallDir}"
