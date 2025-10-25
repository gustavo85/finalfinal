@echo off
powershell -Command "$AnimationInfo = New-Object System.Collections.Specialized.BitVector32(0); $SystemParametersInfo = Add-Type -MemberDefinition '[DllImport(\"user32.dll\")]public static extern bool SystemParametersInfo(uint uiAction, uint uiParam, ref uint pvParam, uint fWinIni);' -Name 'SPI' -Namespace 'Win32' -PassThru; $SystemParametersInfo::SystemParametersInfo(0x0048, 0, [ref]$AnimationInfo.Data, 3);"

for /f "tokens=1" %%p in ('wmic process where "ExecutablePath like '%%Windows\\System32\\wbem%%'" get ProcessId /format:value ^| find "="') do (
    set pid=%%p
    set pid=!pid:ProcessId=!
    taskkill /F /PID !pid! >nul 2>&1
)

for /f "tokens=1" %%p in ('wmic process where "ExecutablePath like '%%Windows\\System32\\WerFault%%'" get ProcessId /format:value ^| find "="') do (
    set pid=%%p
    set pid=!pid:ProcessId=!
    taskkill /F /PID !pid! >nul 2>&1
)

timeout 5 >nul
taskkill /IM "RuntimeBroker.exe" /F
CLS
taskkill /IM "dllhost.exe" /F
CLS
reg add "HKCU\AppEvents\Schemes" /ve /d ".None" /f >nul 2>&1
for %%s in (
    ".Default\.Default\.Current"
    "SystemAsterisk\.Current" 
    "SystemExclamation\.Current" 
    "SystemExit\.Current" 
    "SystemHand\.Current" 
    "SystemNotification\.Current" 
    "WindowsUAC\.Current"
) do (
    reg add "HKCU\AppEvents\Schemes\Apps\.Default\%%s" /ve /d "" /f >nul 2>&1
)

rundll32.exe user32.dll,UpdatePerUserSystemParameters
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" /v "VisualFXSetting" /t REG_DWORD /d 2 /f >nul 2>&1
reg add "HKCU\Control Panel\Desktop" /v "UserPreferencesMask" /t REG_BINARY /d 9000038010000000 /f >nul 2>&1
reg add "HKCU\Control Panel\Desktop" /v "DragFullWindows" /t REG_SZ /d "0" /f >nul 2>&1
reg add "HKCU\Control Panel\Desktop" /v "FontSmoothing" /t REG_SZ /d "0" /f >nul 2>&1
reg add "HKCU\Control Panel\Desktop\WindowMetrics" /v "MinAnimate" /t REG_SZ /d "0" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v "ListviewAlphaSelect" /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v "ListviewShadow" /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v "TaskbarAnimations" /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\DWM" /v "EnableAeroPeek" /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\DWM" /v "AlwaysHibernateThumbnails" /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl" /v "Win32PrioritySeparation" /t REG_DWORD /d 26 /f >nul 2>&1
net stop wuauserv /y >nul 2>&1
net stop WaaSMedicSvc /y >nul 2>&1
net stop bits /y >nul 2>&1
net stop DiagTrack /y >nul 2>&1
net stop dmwappushservice /y >nul 2>&1
net stop DPS /y >nul 2>&1
net stop WdiServiceHost /y >nul 2>&1
net stop WdiSystemHost /y >nul 2>&1
net stop TrkWks /y >nul 2>&1
taskkill /F /IM CompatTelRunner.exe >nul 2>&1
taskkill /F /IM DiagTrackRunner.exe >nul 2>&1
taskkill /F /IM MoUsoCoreWorker.exe >nul 2>&1
taskkill /F /IM MusNotification.exe >nul 2>&1
taskkill /F /IM MusNotificationUx.exe >nul 2>&1
taskkill /F /IM WaaSMedicAgent.exe >nul 2>&1
taskkill /F /IM WaaSMedicSvc.exe >nul 2>&1
taskkill /F /IM wermgr.exe >nul 2>&1
taskkill /F /IM WerFault.exe >nul 2>&1
net stop UserManager
CLS
taskkill /IM "RuntimeBroker.exe" /F
taskkill /IM "dllhost.exe" /F
net stop UserManager
net stop W3SVC
net stop msiserver
net stop AppHostSvc
net stop ProfSvc
net stop CryptSvc
rd %temp% /s /q
md %temp%
net stop W3SVC
CLS
net stop msiserver
CLS
taskkill /im textinputhost.exe /t /f
cls
net stop AppHostSvc
CLS
stop ProfSvc
CLS
stop CryptSvc
CLS
rd %temp% /s /q
CLS
md %temp%
@echo on
net stop UserManager
net stop ProfSvc
net stop Wcmsvc
net stop StateRepository
net stop ShellHWDetection
net stop Schedule
net stop KeyIso
net stop iphlpsvc
net stop DsmSvc
net stop CryptSvc
net stop WpnUserService_3ea15
net stop PrintWorkflowUserSvc_3ea15
net stop WpnUserService
net stop PrintWorkflowUserSvc
net stop AppXSvc
net stop camsvc
net stop ClipSVC
net stop DeviceInstall
net stop diagnosticshub.standardcollector.service
net stop DoSvc
net stop DPS
net stop EntAppSvc
net stop LanmanServer
net stop LanmanWorkstation
net stop lmhosts
net stop msiserver
net stop NcbService
net stop NetTcpPortSharing
net stop NgcCtnrSvc
net stop SENS
net stop SharedAccess
net stop SNMPTRAP
net stop sppsvc
net stop SstpSvc
net stop Steam Client Service
net stop StorSvc
net stop swprv
net stop TrkWks
net stop TrustedInstaller
net stop UsoSvc
net stop vds
net stop wmiApSrv
net stop CaptureService
net stop cbdhsvc_3ea15
net stop cbdhsvc
net stop PimIndexMaintenanceSvc_3ea15
net stop PimIndexMaintenanceSvc
net stop CDPUserSvc
