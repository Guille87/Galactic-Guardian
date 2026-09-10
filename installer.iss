; Instalador de Galactic Guardian (Inno Setup 6).
;
;   iscc /DVersion=0.1.4 installer.iss
;
; Genera GalacticGuardian-setup.exe. Instalación por usuario (sin UAC) en
; %LOCALAPPDATA%\Programs\Galactic Guardian. El AppId fijo permite que una
; instalación nueva actualice la anterior en su sitio; la partida y la
; configuración viven en %APPDATA%\GalacticGuardian y no se tocan.

#ifndef Version
  #define Version "0.0.0"
#endif
#define AppName "Galactic Guardian"

[Setup]
AppId={{7F3B2A18-6C4D-4E9A-9B21-2D5E8C1A4F70}
AppName={#AppName}
AppVersion={#Version}
AppPublisher=Guillermo Amado
DefaultDirName={localappdata}\Programs\Galactic Guardian
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=.
OutputBaseFilename=GalacticGuardian-setup
SetupIconFile=data\assets\imagenes\favicon.ico
UninstallDisplayIcon={app}\GalacticGuardian.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Cierra el juego si está abierto antes de sustituir archivos (actualización).
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: desktopicon; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "dist\GalacticGuardian\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\GalacticGuardian.exe"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\GalacticGuardian.exe"; Tasks: desktopicon

[Run]
; Sin skipifsilent: tras una actualización silenciosa el juego se vuelve a abrir solo.
Filename: "{app}\GalacticGuardian.exe"; Description: "Iniciar {#AppName}"; Flags: nowait postinstall runascurrentuser
