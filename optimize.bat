@echo off
setlocal enabledelayedexpansion

rem Elevación a administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%~dp0NSudo.exe" (
        "%~dp0NSudo.exe" -U:T -ShowWindowMode:Hide -Wait:True -WorkingDirectory:%~dp0 "%~f0"
        exit /b %errorlevel%
    ) else (
        powershell -Command "Start-Process '%~f0' -Verb RunAs"
        exit /b 1
    )
)

rem Importar .reg con máximos privilegios (64 y 32 bits) si existen en la misma carpeta
if exist "%~dp0reg.reg" (
    reg.exe import "%~dp0reg.reg" /reg:64 >nul 2>&1
    reg.exe import "%~dp0reg.reg" /reg:32 >nul 2>&1
)
if exist "%~dp0reg1.reg" (
    reg.exe import "%~dp0reg1.reg" /reg:64 >nul 2>&1
    reg.exe import "%~dp0reg1.reg" /reg:32 >nul 2>&1
)

:CREATE_QOS_POLICY
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Version" /t REG_SZ /d "1.0" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Application Name" /t REG_SZ /d %APPLICATION% /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Protocol" /t REG_SZ /d "*" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Local Port" /t REG_SZ /d "*" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Local IP" /t REG_SZ /d "*" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Local IP Prefix Length" /t REG_SZ /d "*" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Remote Port" /t REG_SZ /d "*" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Remote IP" /t REG_SZ /d "*" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Remote IP Prefix Length" /t REG_SZ /d "*" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "DSCP Value" /t REG_SZ /d "1" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Throttle Rate" /t REG_SZ /d "-1" /f >nul 2>&1
goto :eof

:CREATE_QOS_POLICY_NON_NATIVE
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Version" /t REG_SZ /d "1.0" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Application Name" /t REG_SZ /d %APPLICATION% /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Protocol" /t REG_SZ /d "*" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Local Port" /t REG_SZ /d "*" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Local IP" /t REG_SZ /d "*" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Local IP Prefix Length" /t REG_SZ /d "*" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Remote Port" /t REG_SZ /d "*" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Remote IP" /t REG_SZ /d "*" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Remote IP Prefix Length" /t REG_SZ /d "*" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "DSCP Value" /t REG_SZ /d "5" /f >nul 2>&1
Reg.exe add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\%PROFILENAME%" /v "Throttle Rate" /t REG_SZ /d "-1" /f >nul 2>&1
goto :eof

:apply_policy
set "app_path=%~1"
if /i "%~x1"==".exe" (
    set "filename=%~n1"
    set "profilename=Low_!filename!"
    reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\!profilename!" /v "Version" /t REG_SZ /d "1.0" /f >nul 2>&1
    reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\!profilename!" /v "Application Name" /t REG_SZ /d "!app_path!" /f >nul 2>&1
    reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\!profilename!" /v "DSCP Value" /t REG_SZ /d "0" /f >nul 2>&1
    reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\!profilename!" /v "Throttle Rate" /t REG_SZ /d "-1" /f >nul 2>&1
    reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\!profilename!" /v "Protocol" /t REG_SZ /d "*" /f >nul 2>&1
    reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\!profilename!" /v "Local Port" /t REG_SZ /d "*" /f >nul 2>&1
    reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\!profilename!" /v "Local IP" /t REG_SZ /d "*" /f >nul 2>&1
    reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\!profilename!" /v "Local IP Prefix Length" /t REG_SZ /d "*" /f >nul 2>&1
    reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\!profilename!" /v "Remote Port" /t REG_SZ /d "*" /f >nul 2>&1
    reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\!profilename!" /v "Remote IP" /t REG_SZ /d "*" /f >nul 2>&1
    reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\QoS\!profilename!" /v "Remote IP Prefix Length" /t REG_SZ /d "*" /f >nul 2>&1
)
goto :eof

rem BCDEdit y arranque
bcdedit /set disabledynamictick yes >nul 2>&1
bcdedit /set useplatformtick yes >nul 2>&1
bcdedit /set hypervisorlaunchtype off >nul 2>&1
bcdedit /set tscsyncpolicy Enhanced >nul 2>&1
bcdedit /timeout 0 >nul 2>&1
bcdedit /set nolowmem yes >nul 2>&1
bcdedit /debug No >nul 2>&1
bcdedit /deletevalue useplatformclock >nul 2>&1
bcdedit /set bootux disabled >nul 2>&1
bcdedit /set bootmenupolicy Legacy >nul 2>&1
bcdedit /set quietboot yes >nul 2>&1
bcdedit /set {globalsettings} custom:16000067 true >nul 2>&1
bcdedit /set {globalsettings} custom:16000068 true >nul 2>&1
bcdedit /set {globalsettings} custom:16000069 true >nul 2>&1
bcdedit /set linearaddress57 OptOut >nul 2>&1
bcdedit /set increaseuserva 268435328 >nul 2>&1
bcdedit /set firstmegabytepolicy UseAll >nul 2>&1
bcdedit /set avoidlowmemory 0x8000000 >nul 2>&1
bcdedit /set vm No >nul 2>&1
bcdedit /set configaccesspolicy Default >nul 2>&1
bcdedit /set MSI Default >nul 2>&1
bcdedit /set usephysicaldestination No >nul 2>&1
bcdedit /set usefirmwarepcisettings No >nul 2>&1

rem VBS/Hyper-V
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" /v "Enabled" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v "LsaCfgFlags" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v "EnableVirtualizationBasedSecurity" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v "RequirePlatformSecurityFeatures" /t REG_DWORD /d "0" /f >nul 2>&1
dism /online /disable-feature /featurename:Microsoft-Hyper-V-All /norestart >nul 2>&1
dism /online /disable-feature /featurename:HypervisorPlatform /norestart >nul 2>&1
dism /online /disable-feature /featurename:VirtualMachinePlatform /norestart >nul 2>&1

rem DWM y tipografías (1ª vez; duplicados eliminados)
reg add "HKCU\Software\Microsoft\Windows\DWM" /v "Composition" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\Dwm" /v "OneCoreNoComposition" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\Dwm" /v "OverlayTestMode" /t REG_DWORD /d "5" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\Dwm" /v "MaxQueuedBuffers" /t REG_DWORD /d "2" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\Dwm" /v "ForceDoubleBuffer" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\Dwm" /v "MaximumFlipQueueSize" /t REG_DWORD /d "2" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\DWM" /v "AnimationsShiftKey" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\DWM" /v "AnimationAttributionEnabled" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\DWM" /v "AnimationAttributionHashingEnabled" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\DWM" /v "ColorizationGlassAttribute" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\DWM" /v "AlwaysHibernateThumbnails" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\DWM" /v "EnableWindowColorization" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DWM" /v "DisallowAnimations" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DWM" /v "DWMWA_TRANSITIONS_FORCEDISABLED" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows" /v "EnableDwmInputProcessing" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows" /v "DwmInputUsesIoCompletionPort" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows" /v "DesktopHeapLogging" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\Dwm" /v "OverrideVSyncMode" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\Dwm" /v "DisableFullscreenOptimizations" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\Dwm" /v "EnablePerProcessSystemScheduling" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers\Scheduler" /v "VsyncIdleTimeout" /t REG_DWORD /d "0" /f >nul 2>&1

sc stop "FontCache" >nul 2>&1
sc config "FontCache" start= disabled >nul 2>&1
sc stop "FontCache3.0.0.0" >nul 2>&1
sc config "FontCache3.0.0.0" start= disabled >nul 2>&1
del /a /q /f "%WinDir%\ServiceProfiles\LocalService\AppData\Local\FontCache\*.dat" >nul 2>&1
del /a /q /f "%WinDir%\ServiceProfiles\LocalService\AppData\Local\FontCache\*.tmp" >nul 2>&1
del /a /q /f "%WinDir%\System32\FNTCACHE.DAT" >nul 2>&1
del /a /q /f "%WinDir%\SysWOW64\FNTCACHE.DAT" >nul 2>&1
del /a /q /f "%LocalAppData%\Microsoft\Windows\Fonts\*.dat" >nul 2>&1
del /a /q /f "%LocalAppData%\Microsoft\Windows\Fonts\*.tmp" >nul 2>&1
reg add "HKCU\Control Panel\Desktop" /v "FontSmoothing" /t REG_SZ /d "2" /f >nul 2>&1
reg add "HKCU\Control Panel\Desktop" /v "FontSmoothingType" /t REG_DWORD /d "2" /f >nul 2>&1
reg add "HKCU\Control Panel\Desktop" /v "FontSmoothingGamma" /t REG_DWORD /d "1400" /f >nul 2>&1
reg add "HKCU\Control Panel\Desktop" /v "FontSmoothingOrientation" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Avalon.Graphics" /v "DisableHWAcceleration" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Avalon.Graphics" /v "MaxMultisampleType" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Avalon.Graphics" /v "DisableHWAcceleration" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Font Drivers" /v "Adobe Type Manager" /t REG_SZ /d "atmfd.dll" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontCache" /v "CacheSize" /t REG_DWORD /d "16384" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontCache" /v "CacheLimit" /t REG_DWORD /d "32768" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" /v "DisableUnusedFonts" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontMapperFamilyFallback" /v "OptimizeForPerformance" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontSubstitutes" /v "CacheLookups" /t REG_DWORD /d "1" /f >nul 2>&1
sc config "FontCache" start= auto >nul 2>&1
sc start "FontCache" >nul 2>&1
powershell -NoProfile -Command "Get-Process fontdrvhost -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue" >nul 2>&1

rem Memoria/prefetch (1ª vez; duplicados eliminados)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters" /v "EnablePrefetcher" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters" /v "EnableSuperfetch" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters" /v "SfTracingState" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters" /v "EnableBootTrace" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v "LargeSystemCache" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v "DisablePagingExecutive" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v "DisablePageCombining" /t REG_DWORD /d "1" /f >nul 2>&1
powershell -NoProfile -Command "Disable-MMAgent -MemoryCompression -ErrorAction SilentlyContinue" >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v "ClearPageFileAtShutdown" /t REG_DWORD /d "0" /f >nul 2>&1
for /f %%i in ('powershell -Command "(Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize"') do set /a RAM=%%i + 100000
reg add "HKLM\SYSTEM\CurrentControlSet\Control" /v "SvcHostSplitThresholdInKB" /t REG_DWORD /d "%RAM%" /f >nul 2>&1
for /f %%i in ('powershell -Command "(Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize"') do set RAM_KB=%%i
set /a IOPAGELOCKLIMIT=%RAM_KB% * 1024
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v "IoPageLockLimit" /t REG_DWORD /d "%IOPAGELOCKLIMIT%" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v "DontVerifyRandomDrivers" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v "SecondLevelDataCache" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v "SessionViewSize" /t REG_DWORD /d "192" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v "SessionPoolSize" /t REG_DWORD /d "192" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v "NonPagedPoolSize" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v "PagedPoolSize" /t REG_DWORD /d "0" /f >nul 2>&1
for /f "skip=1 tokens=2 delims==" %%i in ('wmic os get TotalVisibleMemorySize /format:value') do set /a RAM_MB=%%i/1024
if %RAM_MB% GEQ 16384 (
    wmic computersystem where name="%computername%" set AutomaticManagedPagefile=False >nul 2>&1
    wmic pagefileset delete >nul 2>&1
)

rem Sistema de archivos / fsutil
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v "NtfsMemoryUsage" /t REG_DWORD /d "2" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v "NtfsDisable8dot3NameCreation" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v "NtfsDisableLastAccessUpdate" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v "NtfsMftZoneReservation" /t REG_DWORD /d "4" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v "LongPathsEnabled" /t REG_DWORD /d "1" /f >nul 2>&1
fsutil behavior set DisableDeleteNotify 0 >nul 2>&1
fsutil behavior set disablecompression 1 >nul 2>&1
fsutil behavior set disableencryption 1 >nul 2>&1
fsutil behavior set encryptpagingfile 0 >nul 2>&1
diskperf -N >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\mountmgr" /v "NoAutoMount" /t REG_DWORD /d "0" /f >nul 2>&1

for /f "tokens=*" %%s in ('reg query "HKLM\SYSTEM\CurrentControlSet\Enum" /S /F "StorPort" 2^>nul ^| findstr /e "StorPort"') do (
    reg add "%%s" /v "EnableIdlePowerManagement" /t REG_DWORD /d "0" /f >nul 2>&1
    reg add "%%s" /v "IdlePowerManagement" /t REG_DWORD /d "0" /f >nul 2>&1
)
reg add "HKLM\SYSTEM\CurrentControlSet\Services\storahci\Parameters\Device" /v "QueueDepth" /t REG_DWORD /d "32" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\stornvme\Parameters\Device" /v "QueueDepth" /t REG_DWORD /d "32" /f >nul 2>&1
FOR /F "eol=E" %%a in ('REG QUERY "HKLM\SYSTEM\CurrentControlSet\Services" /S /F "EnableHIPM" 2^>nul ^| FINDSTR /V "EnableHIPM"') DO (
    REG ADD "%%a" /F /V "EnableHIPM" /T REG_DWORD /d "0" >NUL 2>&1
    REG ADD "%%a" /F /V "EnableDIPM" /T REG_DWORD /d "0" >NUL 2>&1
    REG ADD "%%a" /F /V "EnableHDDParking" /T REG_DWORD /d "0" >NUL 2>&1
)
FOR /F "eol=E" %%a in ('REG QUERY "HKLM\SYSTEM\CurrentControlSet\Services" /S /F "EnableALPM" 2^>nul ^| FINDSTR /V "EnableALPM"') DO (
    REG ADD "%%a" /F /V "EnableALPM" /T REG_DWORD /d "0" >NUL 2>&1
)
reg add "HKLM\SYSTEM\CurrentControlSet\Services\storahci\Parameters" /v "DisableDeviceStop" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\storahci\Parameters" /v "TreatAsInternalPort" /t REG_MULTI_SZ /d "0\01\02\03\04\05\06" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\stornvme\Parameters\Device" /v "IdlePowerMode" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\stornvme\Parameters\Device" /v "AutonomousPowerStateTransition" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\stornvme\Parameters\Device" /v "IoQueuesPerCore" /t REG_DWORD /d "2" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\stornvme\Parameters\Device" /v "MaxIoQueues" /t REG_DWORD /d "16" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\stornvme\Parameters\Device" /v "EnableLatencyControl" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\stornvme\Parameters\Device" /v "LowLatencyMode" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\stornvme\Parameters\Device" /v "ThermalThrottling" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\stornvme\Parameters\Device" /v "WriteCacheEnabled" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\stornvme\Parameters\Device" /v "ForcedPhysicalSectorSizeInBytes" /t REG_MULTI_SZ /d "* 4096" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\stornvme\Parameters\Device" /v "EnableVolatileWriteCache" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\stornvme\Parameters\Device" /v "KeepAliveTime" /t REG_DWORD /d "30000" /f >nul 2>&1
FOR /F "eol=E" %%a in ('REG QUERY "HKLM\SYSTEM\CurrentControlSet\Services" /S /F "IoLatencyCap" 2^>nul ^| FINDSTR /V "IoLatencyCap"') DO (
    REG ADD "%%a" /F /V "IoLatencyCap" /T REG_DWORD /d "0" >NUL 2>&1
)
powershell -NoProfile -Command "$disks = Get-PhysicalDisk; foreach($disk in $disks){Set-PhysicalDisk -FriendlyName $disk.FriendlyName -Usage AutoSelect -ErrorAction SilentlyContinue}" >nul 2>&1

rem Prioridades/Multimedia
reg add "HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl" /v "IRQ1Priority" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl" /v "IRQ8Priority" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl" /v "IRQ14Priority" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl" /v "IRQ39Priority" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v "SystemResponsiveness" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v "NetworkThrottlingIndex" /t REG_DWORD /d "0xffffffff" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v "NoLazyMode" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v "LazyModeTimeout" /t REG_DWORD /d "10000" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "GPU Priority" /t REG_DWORD /d "8" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "Priority" /t REG_DWORD /d "6" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "Scheduling Category" /t REG_SZ /d "High" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "SFIO Priority" /t REG_SZ /d "High" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "Background Only" /t REG_SZ /d "False" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "Affinity" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "Clock Rate" /t REG_DWORD /d "10000" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Audio" /v "GPU Priority" /t REG_DWORD /d "31" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Audio" /v "Priority" /t REG_DWORD /d "8" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Audio" /v "Scheduling Category" /t REG_SZ /d "High" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Playback" /v "GPU Priority" /t REG_DWORD /d "31" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Playback" /v "Priority" /t REG_DWORD /d "8" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Playback" /v "Scheduling Category" /t REG_SZ /d "High" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Capture" /v "GPU Priority" /t REG_DWORD /d "31" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Capture" /v "Priority" /t REG_DWORD /d "8" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Capture" /v "Scheduling Category" /t REG_SZ /d "High" /f >nul 2>&1
sc config MMCSS start= auto >nul 2>&1
sc stop MMCSS >nul 2>&1
sc start MMCSS >nul 2>&1

rem GameDVR y barra de juegos
reg add "HKCU\System\GameConfigStore" /v "GameDVR_Enabled" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\System\GameConfigStore" /v "GameDVR_FSEBehaviorMode" /t REG_DWORD /d "2" /f >nul 2>&1
reg add "HKCU\System\GameConfigStore" /v "GameDVR_FSEBehavior" /t REG_DWORD /d "2" /f >nul 2>&1
reg add "HKCU\System\GameConfigStore" /v "GameDVR_HonorUserFSEBehaviorMode" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKCU\System\GameConfigStore" /v "GameDVR_EFSEFeatureFlags" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v "AppCaptureEnabled" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\GameDVR" /v "AllowGameDVR" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\PolicyManager\default\ApplicationManagement\AllowGameDVR" /v "value" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\SOFTWARE\Microsoft\GameBar" /v "AutoGameModeEnabled" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\SOFTWARE\Microsoft\GameBar" /v "AllowAutoGameMode" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\SOFTWARE\Microsoft\GameBar" /v "UseNexusForGameBarEnabled" /t REG_DWORD /d "0" /f >nul 2>&1
reg delete "HKCU\SYSTEM\GameConfigStore\Children" /f >nul 2>&1
reg delete "HKCU\SYSTEM\GameConfigStore\Parents" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\GameDVR" /v "AudioCaptureEnabled" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\GameDVR" /v "CursorCaptureEnabled" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\GameDVR" /v "HistoricalCaptureEnabled" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\System\GameConfigStore" /v "GameDVR_DXGIHonorFSEWindowsCompatible" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKCU\SOFTWARE\Microsoft\Multimedia\Audio" /v "UserDuckingPreference" /t REG_DWORD /d "3" /f >nul 2>&1

rem Gráficos
reg add "HKCU\Software\Microsoft\DirectX\UserGpuPreferences" /v "GpuPreference" /t REG_DWORD /d "2" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v "HwSchMode" /t REG_DWORD /d "2" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v "DpiMapIommuContiguous" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\DXGKrnl" /v "MonitorLatencyTolerance" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\DXGKrnl" /v "MonitorRefreshLatencyTolerance" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers\Scheduler" /v "EnablePreemption" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v "TdrLevel" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v "TdrDelay" /t REG_DWORD /d "60" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v "TdrDdiDelay" /t REG_DWORD /d "60" /f >nul 2>&1
reg query "HKLM\SYSTEM\CurrentControlSet\Services\igfx" >nul 2>&1
if %errorlevel% equ 0 (
    reg add "HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000" /v "Disable_OverlayDSQualityEnhancement" /t REG_DWORD /d "1" /f >nul 2>&1
    reg add "HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000" /v "IncreaseFixedSegment" /t REG_DWORD /d "1" /f >nul 2>&1
    reg add "HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000" /v "AdaptiveVsyncEnable" /t REG_DWORD /d "0" /f >nul 2>&1
)

rem MSI y afinidad
for /f %%i in ('powershell -Command "Get-CimInstance Win32_USBController | Select-Object -ExpandProperty PNPDeviceID" ^| findstr /L "PCI\VEN_"') do (
    reg add "HKLM\System\CurrentControlSet\Enum\%%i\Device Parameters\Interrupt Management\MessageSignaledInterruptProperties" /v "MSISupported" /t REG_DWORD /d "1" /f >nul 2>&1
    reg delete "HKLM\SYSTEM\CurrentControlSet\Enum\%%i\Device Parameters\Interrupt Management\Affinity Policy" /v "DevicePriority" /f >nul 2>&1
)
for /f %%i in ('powershell -Command "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty PNPDeviceID" ^| findstr /L "PCI\VEN_"') do (
    reg add "HKLM\System\CurrentControlSet\Enum\%%i\Device Parameters\Interrupt Management\MessageSignaledInterruptProperties" /v "MSISupported" /t REG_DWORD /d "1" /f >nul 2>&1
    reg delete "HKLM\System\CurrentControlSet\Enum\%%i\Device Parameters\Interrupt Management\Affinity Policy" /v "DevicePriority" /f >nul 2>&1
)
powershell -Command "(Get-CimInstance Win32_ComputerSystem).Manufacturer" | findstr /i /C:VMWare >nul 2>&1
if %errorlevel% neq 0 (
    for /f %%i in ('powershell -Command "Get-CimInstance Win32_NetworkAdapter | Select-Object -ExpandProperty PNPDeviceID" ^| findstr /L "PCI\VEN_"') do (
        reg add "HKLM\System\CurrentControlSet\Enum\%%i\Device Parameters\Interrupt Management\MessageSignaledInterruptProperties" /v "MSISupported" /t REG_DWORD /d "1" /f >nul 2>&1
        reg delete "HKLM\System\CurrentControlSet\Enum\%%i\Device Parameters\Interrupt Management\Affinity Policy" /v "DevicePriority" /f >nul 2>&1
    )
)
for /f %%i in ('powershell -Command "Get-CimInstance Win32_IDEController | Select-Object -ExpandProperty PNPDeviceID" ^| findstr /L "PCI\VEN_"') do (
    reg add "HKLM\System\CurrentControlSet\Enum\%%i\Device Parameters\Interrupt Management\MessageSignaledInterruptProperties" /v "MSISupported" /t REG_DWORD /d "1" /f >nul 2>&1
    reg delete "HKLM\SYSTEM\CurrentControlSet\Enum\%%i\Device Parameters\Interrupt Management\Affinity Policy" /v "DevicePriority" /f >nul 2>&1
    reg add "HKLM\System\CurrentControlSet\Enum\%%i\Device Parameters\Interrupt Management\Affinity Policy" /v "DevicePolicy" /t REG_DWORD /d "4" /f >nul 2>&1
)
for /f "tokens=*" %%i in ('reg query "HKLM\SYSTEM\CurrentControlSet\Enum\PCI" ^| findstr "HKEY"') do (
    for /f "tokens=*" %%a in ('reg query "%%i" ^| findstr "HKEY"') do (
        reg delete "%%a\Device Parameters\Interrupt Management\Affinity Policy" /v "DevicePriority" /f >nul 2>&1
    )
)

rem USB energía
for /f "tokens=*" %%i in ('powershell -Command "Get-PnpDevice -Class 'USB' | Select-Object -ExpandProperty DeviceID" ^| findstr "USB\VID_"') do (
    reg add "HKLM\System\CurrentControlSet\Enum\%%i\Device Parameters" /v "EnhancedPowerManagementEnabled" /t REG_DWORD /d "0" /f >nul 2>&1
    reg add "HKLM\System\CurrentControlSet\Enum\%%i\Device Parameters" /v "AllowIdleIrpInD3" /t REG_DWORD /d "0" /f >nul 2>&1
    reg add "HKLM\System\CurrentControlSet\Enum\%%i\Device Parameters" /v "EnableSelectiveSuspend" /t REG_DWORD /d "0" /f >nul 2>&1
    reg add "HKLM\System\CurrentControlSet\Enum\%%i\Device Parameters" /v "DeviceSelectiveSuspended" /t REG_DWORD /d "0" /f >nul 2>&1
    reg add "HKLM\System\CurrentControlSet\Enum\%%i\Device Parameters" /v "SelectiveSuspendEnabled" /t REG_DWORD /d "0" /f >nul 2>&1
    reg add "HKLM\System\CurrentControlSet\Enum\%%i\Device Parameters" /v "SelectiveSuspendOn" /t REG_DWORD /d "0" /f >nul 2>&1
    reg add "HKLM\System\CurrentControlSet\Enum\%%i\Device Parameters" /v "D3ColdSupported" /t REG_DWORD /d "0" /f >nul 2>&1
)
for %%a in (fid_D1Latency fid_D2Latency fid_D3Latency D3ColdSupported) do (
    for /f "delims=" %%b in ('reg query "HKLM\SYSTEM\CurrentControlSet\Enum" /s /f "%%a" ^| findstr "HKEY"') do (
        reg add "%%b" /v "%%a" /t REG_DWORD /d "0" /f >nul 2>&1
    )
)

rem Drivers/metadata
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\DriverSearching" /v "SearchOrderConfig" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Device Metadata" /v "PreventDeviceMetadataFromNetwork" /t REG_DWORD /d "1" /f >nul 2>&1

rem Entrada
reg add "HKCU\Control Panel\Mouse" /v "MouseSpeed" /t REG_SZ /d "0" /f >nul 2>&1
reg add "HKCU\Control Panel\Mouse" /v "MouseThreshold1" /t REG_SZ /d "0" /f >nul 2>&1
reg add "HKCU\Control Panel\Mouse" /v "MouseThreshold2" /t REG_SZ /d "0" /f >nul 2>&1
reg add "HKCU\Control Panel\Mouse" /v "MouseHoverTime" /t REG_SZ /d "0" /f >nul 2>&1
reg add "HKCU\Control Panel\Desktop" /v "MouseWheelRouting" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\Control Panel\Keyboard" /v "InitialKeyboardIndicators" /t REG_SZ /d "0" /f >nul 2>&1
reg add "HKCU\Control Panel\Keyboard" /v "KeyboardDelay" /t REG_SZ /d "0" /f >nul 2>&1
reg add "HKCU\Control Panel\Keyboard" /v "KeyboardSpeed" /t REG_SZ /d "31" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\kbdclass\Parameters" /v "KeyboardDataQueueSize" /t REG_DWORD /d "50" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\mouclass\Parameters" /v "MouseDataQueueSize" /t REG_DWORD /d "50" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\mouclass\Parameters" /v "ThreadPriority" /t REG_DWORD /d "31" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\kbdclass\Parameters" /v "ThreadPriority" /t REG_DWORD /d "31" /f >nul 2>&1

rem Accesibilidad rápida
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v "DisallowShaking" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKCU\Control Panel\Accessibility" /v "Animation" /t REG_SZ /d "0" /f >nul 2>&1
reg add "HKCU\SOFTWARE\Microsoft\Ease of Access" /v "selfscan" /t REG_DWORD /d "0" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Microsoft\Active Accessibility\InstalledHandlers" /f >nul 2>&1
reg add "HKCU\Control Panel\Accessibility\Keyboard Response" /v "AutoRepeatDelay" /t REG_SZ /d "0" /f >nul 2>&1
reg add "HKCU\Control Panel\Accessibility\Keyboard Response" /v "AutoRepeatRate" /t REG_SZ /d "0" /f >nul 2>&1
reg add "HKCU\Control Panel\Accessibility\Keyboard Response" /v "DelayBeforeAcceptance" /t REG_SZ /d "0" /f >nul 2>&1
reg add "HKCU\Control Panel\Accessibility\Keyboard Response" /v "Flags" /t REG_SZ /d "26" /f >nul 2>&1
reg add "HKCU\Control Panel\Accessibility\StickyKeys" /v "Flags" /t REG_SZ /d "58" /f >nul 2>&1
reg add "HKCU\Control Panel\Accessibility\ToggleKeys" /v "Flags" /t REG_SZ /d "58" /f >nul 2>&1
reg add "HKCU\Control Panel\Accessibility\MouseKeys" /v "Flags" /t REG_SZ /d "130" /f >nul 2>&1
reg add "HKCU\Control Panel\Accessibility\SoundSentry" /v "Windows Effect" /t REG_SZ /d "0" /f >nul 2>&1
reg add "HKCU\Control Panel\Accessibility\TimeOut" /v "Flags" /t REG_SZ /d "2" /f >nul 2>&1
reg add "HKCU\Control Panel\Accessibility\TimeOut" /v "TimeToWait" /t REG_SZ /d "300000" /f >nul 2>&1
reg add "HKCU\Control Panel\Accessibility\Slate Launch" /v "ATapp" /t REG_SZ /d "" /f >nul 2>&1
reg add "HKCU\Control Panel\Accessibility\Slate Launch" /v "Launchpad" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\Control Panel\Accessibility\StickyKeys" /v "Flags" /t REG_SZ /d "506" /f >nul 2>&1

rem Netsh global
netsh int tcp set global autotuninglevel=normal >nul 2>&1
netsh int tcp set global chimney=disabled >nul 2>&1
netsh int tcp set global dca=enabled >nul 2>&1
netsh int tcp set global netdma=disabled >nul 2>&1
netsh int tcp set global ecncapability=disabled >nul 2>&1
netsh int tcp set global timestamps=disabled >nul 2>&1
netsh int tcp set global rsc=disabled >nul 2>&1
netsh int tcp set global nonsackrttresiliency=disabled >nul 2>&1
netsh int tcp set global maxsynretransmissions=2 >nul 2>&1
netsh int tcp set global initialRto=2000 >nul 2>&1
netsh int tcp set global rss=enabled >nul 2>&1
netsh int tcp set heuristics disabled >nul 2>&1
netsh int tcp set heuristics wsh=disabled >nul 2>&1
netsh int tcp set security mpp=disabled >nul 2>&1
netsh int tcp set security profiles=disabled >nul 2>&1
netsh int tcp set supplemental Internet congestionprovider=ctcp >nul 2>&1
netsh int ip set global neighborcachelimit=4096 >nul 2>&1
netsh int ip set global routecachelimit=4096 >nul 2>&1
netsh int ip set global sourceroutingbehavior=drop >nul 2>&1
netsh int ip set global taskoffload=disabled >nul 2>&1
netsh int ip set global dhcpmediasense=disabled >nul 2>&1
netsh int ip set global mediasenseeventlog=disabled >nul 2>&1
netsh int ip set global icmpredirects=disabled >nul 2>&1
netsh int ip set global redirect=disabled >nul 2>&1
netsh int ipv4 set dynamicport tcp start=1025 num=64510 >nul 2>&1
netsh int ipv4 set dynamicport udp start=1025 num=64510 >nul 2>&1
netsh int ipv6 set global neighborcachelimit=4096 >nul 2>&1
netsh int ipv6 set global routecachelimit=4096 >nul 2>&1
netsh int ipv6 set global dhcpmediasense=disabled >nul 2>&1
netsh int ipv6 set global redirect=disabled >nul 2>&1
netsh int ipv6 set global mldlevel=none >nul 2>&1
netsh int ipv6 set global randomizeidentifiers=disabled >nul 2>&1
netsh int ipv6 set dynamicport tcp start=1025 num=64510 >nul 2>&1
netsh int ipv6 set dynamicport udp start=1025 num=64510 >nul 2>&1
netsh interface teredo set state disabled >nul 2>&1
netsh interface isatap set state disabled >nul 2>&1
rem eliminado: netsh winsock set autotuning on (comando inválido)
netsh winsock reset >nul 2>&1

rem TCP parámetros
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "DefaultTTL" /t REG_DWORD /d "64" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "EnablePMTUDiscovery" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "EnablePMTUBHDetect" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "MTU" /t REG_DWORD /d "1500" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "Tcp1323Opts" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "TcpWindowSize" /t REG_DWORD /d "131072" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "GlobalMaxTcpWindowSize" /t REG_DWORD /d "131072" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "TcpMaxDataRetransmissions" /t REG_DWORD /d "3" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "TcpMaxConnectRetransmissions" /t REG_DWORD /d "5" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "TcpMaxDupAcks" /t REG_DWORD /d "2" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "TcpTimedWaitDelay" /t REG_DWORD /d "30" /f >nul 2>&1
rem (eliminada línea suelta "Full path: ...")
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "MaxUserPort" /t REG_DWORD /d "65534" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "TcpNumConnections" /t REG_DWORD /d "16777214" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "MaxConnectionsPerServer" /t REG_DWORD /d "16" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "KeepAliveTime" /t REG_DWORD /d "300000" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "KeepAliveInterval" /t REG_DWORD /d "1000" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "SynAttackProtect" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "EnableICMPRedirect" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "EnableDeadGWDetect" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "DisableDHCPMediaSense" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "DontAddDefaultGatewayDefaultMetric" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "TcpDelAckTicks" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "SackOpts" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "DisableUserTOSetting" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "InterfaceMetric" /t REG_DWORD /d "10" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "EnableWsd" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "EnableMSS" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "DisableTaskOffload" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "EnableTCPA" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "EnableTCPChimney" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "EnableRSS" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "ArpUseEtherSNAP" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "TcpAckFrequency" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "TCPNoDelay" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\ServiceProvider" /v "Class" /t REG_DWORD /d "8" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\ServiceProvider" /v "DnsPriority" /t REG_DWORD /d "6" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\ServiceProvider" /v "HostsPriority" /t REG_DWORD /d "5" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\ServiceProvider" /v "LocalPriority" /t REG_DWORD /d "4" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\ServiceProvider" /v "NetbtPriority" /t REG_DWORD /d "7" /f >nul 2>&1

for /f "tokens=*" %%i in ('reg query "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces" ^| findstr "HKEY"') do (
    reg add "%%i" /v "TcpAckFrequency" /t REG_DWORD /d "1" /f >nul 2>&1
    reg add "%%i" /v "TcpDelAckTicks" /t REG_DWORD /d "0" /f >nul 2>&1
    reg add "%%i" /v "TCPNoDelay" /t REG_DWORD /d "1" /f >nul 2>&1
    reg add "%%i" /v "TCPInitialRtt" /t REG_DWORD /d "300" /f >nul 2>&1
    reg add "%%i" /v "InterfaceMetric" /t REG_DWORD /d "10" /f >nul 2>&1
    reg add "%%i" /v "UseZeroBroadcast" /t REG_DWORD /d "0" /f >nul 2>&1
)

reg add "HKLM\SYSTEM\CurrentControlSet\Services\AFD\Parameters" /v "DefaultReceiveWindow" /t REG_DWORD /d "131072" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\AFD\Parameters" /v "DefaultSendWindow" /t REG_DWORD /d "131072" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\AFD\Parameters" /v "FastSendDatagramThreshold" /t REG_DWORD /d "1500" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\AFD\Parameters" /v "FastCopyReceiveThreshold" /t REG_DWORD /d "1500" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\AFD\Parameters" /v "DynamicSendBufferDisable" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\AFD\Parameters" /v "IgnorePushBitOnReceives" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\AFD\Parameters" /v "NonBlockingSendSpecialBuffering" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\AFD\Parameters" /v "DisableRawSecurity" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\AFD\Parameters" /v "DoNotHoldNICBuffers" /t REG_DWORD /d "1" /f >nul 2>&1

reg add "HKLM\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" /v "NegativeCacheTime" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" /v "NegativeSOACacheTime" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" /v "NetFailureCacheTime" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" /v "MaxCacheTtl" /t REG_DWORD /d "86400" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" /v "MaxNegativeCacheTtl" /t REG_DWORD /d "0" /f >nul 2>&1

rem NIC ajustes avanzados
for /f "skip=2 tokens=*" %%a in ('powershell -NoProfile -Command "Get-NetAdapter -Physical | Select-Object -ExpandProperty Name"') do (
    powershell -NoProfile -Command "Get-NetAdapter -Name '%%a' -ErrorAction SilentlyContinue | Set-NetAdapterPowerManagement -SelectiveSuspend Disabled -DeviceSleepOnDisconnect Disabled -WakeOnMagicPacket Disabled -WakeOnPattern Disabled -ErrorAction SilentlyContinue" >nul 2>&1
    powershell -NoProfile -Command "$a=Get-NetAdapter -Name '%%a' -ErrorAction SilentlyContinue; if($a){Disable-NetAdapterChecksumOffload -Name '%%a' -ErrorAction SilentlyContinue; Disable-NetAdapterLso -Name '%%a' -ErrorAction SilentlyContinue; Disable-NetAdapterRsc -Name '%%a' -ErrorAction SilentlyContinue; Disable-NetAdapterIPsecOffload -Name '%%a' -ErrorAction SilentlyContinue}" >nul 2>&1
    powershell -NoProfile -Command "Set-NetAdapterRss -Name '%%a' -Enabled $true -ErrorAction SilentlyContinue" >nul 2>&1
    powershell -NoProfile -Command "Set-NetAdapterAdvancedProperty -Name '%%a' -RegistryKeyword '*FlowControl' -RegistryValue 0 -ErrorAction SilentlyContinue" >nul 2>&1
    powershell -NoProfile -Command "Set-NetAdapterAdvancedProperty -Name '%%a' -RegistryKeyword '*ReceiveBuffers' -RegistryValue 2048 -ErrorAction SilentlyContinue" >nul 2>&1
    powershell -NoProfile -Command "Set-NetAdapterAdvancedProperty -Name '%%a' -RegistryKeyword '*TransmitBuffers' -RegistryValue 2048 -ErrorAction SilentlyContinue" >nul 2>&1
    powershell -NoProfile -Command "Set-NetAdapterAdvancedProperty -Name '%%a' -RegistryKeyword '*InterruptModeration' -RegistryValue 0 -ErrorAction SilentlyContinue" >nul 2>&1
    powershell -NoProfile -Command "Set-NetAdapterAdvancedProperty -Name '%%a' -RegistryKeyword '*JumboPacket' -RegistryValue 1514 -ErrorAction SilentlyContinue" >nul 2>&1
    powershell -NoProfile -Command "Disable-NetAdapterBinding -Name '%%a' -ComponentID ms_tcpip6 -ErrorAction SilentlyContinue" >nul 2>&1
)

rem SMB y red
sc config lanmanworkstation depend= bowser/mrxsmb20/nsi >nul 2>&1
sc config mrxsmb10 start= disabled >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v "DisableBandwidthThrottling" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v "DisableLargeMtu" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v "FileInfoCacheEntriesMax" /t REG_DWORD /d "1024" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v "DirectoryCacheEntriesMax" /t REG_DWORD /d "1024" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v "FileNotFoundCacheEntriesMax" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v "MaxCmds" /t REG_DWORD /d "8192" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" /v "IRPStackSize" /t REG_DWORD /d "32" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" /v "SizReqBuf" /t REG_DWORD /d "17424" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v "UseLargeMTU" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v "EnableRawPrinting" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v "MaxMpxCt" /t REG_DWORD /d "50" /f >nul 2>&1
for /f "tokens=*" %%i in ('reg query "HKLM\SYSTEM\CurrentControlSet\Services\NetBT\Parameters\Interfaces" ^| findstr "HKEY"') do (
    reg add "%%i" /v "NetbiosOptions" /t REG_DWORD /d "2" /f >nul 2>&1
)
reg add "HKLM\SYSTEM\CurrentControlSet\Services\NetBT\Parameters" /v "EnableLMHOSTS" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\NetBT\Parameters" /v "NodeType" /t REG_DWORD /d "2" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\NetworkConnectivityStatusIndicator" /v "NoActiveProbe" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\NlaSvc\Parameters\Internet" /v "EnableActiveProbing" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" /v "EnableMulticast" /t REG_DWORD /d "0" /f >nul 2>&1
netsh advfirewall firewall set rule name="Core Networking - Multicast Listener Done (ICMPv6-In)" new enable=no >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\AutoRotation" /v "Enable" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\WcmSvc\Tethering" /v "Hotspot2SignUp" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\WlanSvc\AnqpCache" /v "OsuRegistrationStatus" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\BITS" /v "EnableBITSMaxBandwidth" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\BITS" /v "MaxDownloadTime" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Psched" /v "NonBestEffortLimit" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Psched" /v "TimerResolution" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\NetworkProvider" /v "RestoreConnection" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\NetworkProvider\HwOrder" /v "ProviderOrder" /t REG_SZ /d "RDPNP,LanmanWorkstation,webclient" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\NetworkProvider\Order" /v "ProviderOrder" /t REG_SZ /d "RDPNP,LanmanWorkstation,webclient" /f >nul 2>&1

rem Aplicar QoS bajo a apps clave
set "hardcoded_apps=C:\Windows\System32\CompatTelRunner.exe C:\Windows\System32\TrustedInstaller.exe C:\Windows\System32\TiWorker.exe C:\Windows\System32\MsMpEng.exe C:\Windows\System32\SecurityHealthService.exe C:\Windows\System32\SgrmBroker.exe C:\Windows\System32\WaaSMedicSvc.exe C:\Windows\explorer.exe"
for %%a in (%hardcoded_apps%) do (
    call :apply_policy "%%a"
)
for /f "delims=" %%b in ('powershell.exe -noprofile -command "& {$paths=@('C:\Windows\System32','C:\Windows\SysWOW64','C:\Windows'); $updateExes=@(); foreach($path in $paths){if(Test-Path $path){$updateExes += Get-ChildItem -Path $path -Filter 'update.exe' -ErrorAction SilentlyContinue | ForEach-Object {$_.FullName}}}; $updateExes | ForEach-Object {$_}}"') do (
    call :apply_policy "%%b"
)
powershell -Command "New-NetQosPolicy -Name 'GlobalDSCP1' -Default -DSCPAction 1 -IPProtocolMatchCondition Both" >nul 2>&1
set PROFILENAME=Svchost_QoS & set APPLICATION=C:\Windows\System32\svchost.exe & call :CREATE_QOS_POLICY
set PROFILENAME=TrustedInstaller_QoS & set APPLICATION=C:\Windows\servicing\TrustedInstaller.exe & call :CREATE_QOS_POLICY
set PROFILENAME=Wusa_QoS & set APPLICATION=C:\Windows\System32\Wusa.exe & call :CREATE_QOS_POLICY
set PROFILENAME=UsoClient_QoS & set APPLICATION=C:\Windows\System32\usoclient.exe & call :CREATE_QOS_POLICY
set PROFILENAME=msiexec_QoS & set APPLICATION=C:\Windows\System32\msiexec.exe & call :CREATE_QOS_POLICY
set PROFILENAME=SecurityHealthService_QoS & set APPLICATION=C:\Windows\System32\SecurityHealthService.exe & call :CREATE_QOS_POLICY
set PROFILENAME=CompatTelRunner_QoS & set APPLICATION=C:\Windows\System32\CompatTelRunner.exe & call :CREATE_QOS_POLICY
set PROFILENAME=Explorer_QoS & set APPLICATION=C:\Windows\explorer.exe & call :CREATE_QOS_POLICY
set PROFILENAME=SearchIndexer_QoS & set APPLICATION=C:\Windows\System32\SearchIndexer.exe & call :CREATE_QOS_POLICY
set PROFILENAME=SearchHost_QoS & set APPLICATION=C:\Windows\System32\SearchHost.exe & call :CREATE_QOS_POLICY
set PROFILENAME=audiodg_QoS & set APPLICATION=C:\Windows\System32\audiodg.exe & call :CREATE_QOS_POLICY
set PROFILENAME=dwm_QoS & set APPLICATION=C:\Windows\System32\dwm.exe & call :CREATE_QOS_POLICY
set PROFILENAME=RuntimeBroker_QoS & set APPLICATION=C:\Windows\System32\RuntimeBroker.exe & call :CREATE_QOS_POLICY
set PROFILENAME=ctfmon_QoS & set APPLICATION=C:\Windows\System32\ctfmon.exe & call :CREATE_QOS_POLICY
set PROFILENAME=fontdrvhost_QoS & set APPLICATION=C:\Windows\System32\fontdrvhost.exe & call :CREATE_QOS_POLICY
set PROFILENAME=sihost_QoS & set APPLICATION=C:\Windows\System32\sihost.exe & call :CREATE_QOS_POLICY
set PROFILENAME=taskhostw_QoS & set APPLICATION=C:\Windows\System32\taskhostw.exe & call :CREATE_QOS_POLICY
set PROFILENAME=spoolsv_QoS & set APPLICATION=C:\Windows\System32\spoolsv.exe & call :CREATE_QOS_POLICY
set PROFILENAME=StartMenuExperienceHost_QoS & set APPLICATION=C:\Windows\System32\StartMenuExperienceHost.exe & call :CREATE_QOS_POLICY
set PROFILENAME=auditpol_QoS & set APPLICATION=C:\Windows\System32\auditpol.exe & call :CREATE_QOS_POLICY
set PROFILENAME=msdt_QoS & set APPLICATION=C:\Windows\System32\msdt.exe & call :CREATE_QOS_POLICY
set PROFILENAME=msinfo32_QoS & set APPLICATION=C:\Windows\System32\msinfo32.exe & call :CREATE_QOS_POLICY
set PROFILENAME=wermgr_QoS & set APPLICATION=C:\Windows\System32\wermgr.exe & call :CREATE_QOS_POLICY
set PROFILENAME=WerFault_QoS & set APPLICATION=C:\Windows\System32\WerFault.exe & call :CREATE_QOS_POLICY
set PROFILENAME=dispdiag_QoS & set APPLICATION=C:\Windows\System32\dispdiag.exe & call :CREATE_QOS_POLICY
set PROFILENAME=bcdboot_QoS & set APPLICATION=C:\Windows\System32\bcdboot.exe & call :CREATE_QOS_POLICY
set PROFILENAME=bcdedit_QoS & set APPLICATION=C:\Windows\System32\bcdedit.exe & call :CREATE_QOS_POLICY
set PROFILENAME=bdehdcfg_QoS & set APPLICATION=C:\Windows\System32\bdehdcfg.exe & call :CREATE_QOS_POLICY
set PROFILENAME=chkdsk_QoS & set APPLICATION=C:\Windows\System32\chkdsk.exe & call :CREATE_QOS_POLICY
set PROFILENAME=chkntfs_QoS & set APPLICATION=C:\Windows\System32\chkntfs.exe & call :CREATE_QOS_POLICY
set PROFILENAME=cleanmgr_QoS & set APPLICATION=C:\Windows\System32\cleanmgr.exe & call :CREATE_QOS_POLICY
set PROFILENAME=defrag_QoS & set APPLICATION=C:\Windows\System32\defrag.exe & call :CREATE_QOS_POLICY
set PROFILENAME=diskpart_QoS & set APPLICATION=C:\Windows\System32\diskpart.exe & call :CREATE_QOS_POLICY
set PROFILENAME=diskperf_QoS & set APPLICATION=C:\Windows\System32\diskperf.exe & call :CREATE_QOS_POLICY
set PROFILENAME=diskraid_QoS & set APPLICATION=C:\Windows\System32\diskraid.exe & call :CREATE_QOS_POLICY
set PROFILENAME=diskshadow_QoS & set APPLICATION=C:\Windows\System32\diskshadow.exe & call :CREATE_QOS_POLICY
set PROFILENAME=netsh_QoS & set APPLICATION=C:\Windows\System32\netsh.exe & call :CREATE_QOS_POLICY
set PROFILENAME=netstat_QoS & set APPLICATION=C:\Windows\System32\netstat.exe & call :CREATE_QOS_POLICY
set PROFILENAME=ipconfig_QoS & set APPLICATION=C:\Windows\System32\ipconfig.exe & call :CREATE_QOS_POLICY
set PROFILENAME=ping_QoS & set APPLICATION=C:\Windows\System32\ping.exe & call :CREATE_QOS_POLICY
set PROFILENAME=tracert_QoS & set APPLICATION=C:\Windows\System32\tracert.exe & call :CREATE_QOS_POLICY
set PROFILENAME=nslookup_QoS & set APPLICATION=C:\Windows\System32\nslookup.exe & call :CREATE_QOS_POLICY
set PROFILENAME=nbtstat_QoS & set APPLICATION=C:\Windows\System32\nbtstat.exe & call :CREATE_QOS_POLICY
set PROFILENAME=netcfg_QoS & set APPLICATION=C:\Windows\System32\netcfg.exe & call :CREATE_QOS_POLICY
set PROFILENAME=route_QoS & set APPLICATION=C:\Windows\System32\route.exe & call :CREATE_QOS_POLICY
set PROFILENAME=ftp_QoS & set APPLICATION=C:\Windows\System32\ftp.exe & call :CREATE_QOS_POLICY
set PROFILENAME=finger_QoS & set APPLICATION=C:\Windows\System32\finger.exe & call :CREATE_QOS_POLICY
set PROFILENAME=irftp_QoS & set APPLICATION=C:\Windows\System32\irftp.exe & call :CREATE_QOS_POLICY
set PROFILENAME=mstsc_QoS & set APPLICATION=C:\Windows\System32\mstsc.exe & call :CREATE_QOS_POLICY
set PROFILENAME=reg_QoS & set APPLICATION=C:\Windows\System32\reg.exe & call :CREATE_QOS_POLICY
set PROFILENAME=regedit_QoS & set APPLICATION=C:\Windows\System32\regedit.exe & call :CREATE_QOS_POLICY
set PROFILENAME=regini_QoS & set APPLICATION=C:\Windows\System32\regini.exe & call :CREATE_QOS_POLICY
set PROFILENAME=sc_QoS & set APPLICATION=C:\Windows\System32\sc.exe & call :CREATE_QOS_POLICY
set PROFILENAME=schtasks_QoS & set APPLICATION=C:\Windows\System32\schtasks.exe & call :CREATE_QOS_POLICY
set PROFILENAME=taskkill_QoS & set APPLICATION=C:\Windows\System32\taskkill.exe & call :CREATE_QOS_POLICY
set PROFILENAME=tasklist_QoS & set APPLICATION=C:\Windows\System32\tasklist.exe & call :CREATE_QOS_POLICY
set PROFILENAME=shutdown_QoS & set APPLICATION=C:\Windows\System32\shutdown.exe & call :CREATE_QOS_POLICY
set PROFILENAME=systeminfo_QoS & set APPLICATION=C:\Windows\System32\systeminfo.exe & call :CREATE_QOS_POLICY
set PROFILENAME=powercfg_QoS & set APPLICATION=C:\Windows\System32\powercfg.exe & call :CREATE_QOS_POLICY
set PROFILENAME=gpupdate_QoS & set APPLICATION=C:\Windows\System32\gpupdate.exe & call :CREATE_QOS_POLICY
set PROFILENAME=gpresult_QoS & set APPLICATION=C:\Windows\System32\gpresult.exe & call :CREATE_QOS_POLICY
set PROFILENAME=gpfixup_QoS & set APPLICATION=C:\Windows\System32\gpfixup.exe & call :CREATE_QOS_POLICY
set PROFILENAME=runas_QoS & set APPLICATION=C:\Windows\System32\runas.exe & call :CREATE_QOS_POLICY
set PROFILENAME=whoami_QoS & set APPLICATION=C:\Windows\System32\whoami.exe & call :CREATE_QOS_POLICY
set PROFILENAME=certreq_QoS & set APPLICATION=C:\Windows\System32\certreq.exe & call :CREATE_QOS_POLICY
set PROFILENAME=certutil_QoS & set APPLICATION=C:\Windows\System32\certutil.exe & call :CREATE_QOS_POLICY
set PROFILENAME=cipher_QoS & set APPLICATION=C:\Windows\System32\cipher.exe & call :CREATE_QOS_POLICY
set PROFILENAME=cmdkey_QoS & set APPLICATION=C:\Windows\System32\cmdkey.exe & call :CREATE_QOS_POLICY
set PROFILENAME=icacls_QoS & set APPLICATION=C:\Windows\System32\icacls.exe & call :CREATE_QOS_POLICY
set PROFILENAME=takeown_QoS & set APPLICATION=C:\Windows\System32\takeown.exe & call :CREATE_QOS_POLICY
set PROFILENAME=secedit_QoS & set APPLICATION=C:\Windows\System32\secedit.exe & call :CREATE_QOS_POLICY
set PROFILENAME=klist_QoS & set APPLICATION=C:\Windows\System32\klist.exe & call :CREATE_QOS_POLICY
set PROFILENAME=ksetup_QoS & set APPLICATION=C:\Windows\System32\ksetup.exe & call :CREATE_QOS_POLICY
set PROFILENAME=ktpass_QoS & set APPLICATION=C:\Windows\System32\ktpass.exe & call :CREATE_QOS_POLICY
set PROFILENAME=nltest_QoS & set APPLICATION=C:\Windows\System32\nltest.exe & call :CREATE_QOS_POLICY
set PROFILENAME=sfc_QoS & set APPLICATION=C:\Windows\System32\sfc.exe & call :CREATE_QOS_POLICY
set PROFILENAME=robocopy_QoS & set APPLICATION=C:\Windows\System32\robocopy.exe & call :CREATE_QOS_POLICY
set PROFILENAME=xcopy_QoS & set APPLICATION=C:\Windows\System32\xcopy.exe & call :CREATE_QOS_POLICY
set PROFILENAME=makecab_QoS & set APPLICATION=C:\Windows\System32\makecab.exe & call :CREATE_QOS_POLICY
set PROFILENAME=label_QoS & set APPLICATION=C:\Windows\System32\label.exe & call :CREATE_QOS_POLICY
set PROFILENAME=find_QoS & set APPLICATION=C:\Windows\System32\find.exe & call :CREATE_QOS_POLICY
set PROFILENAME=findstr_QoS & set APPLICATION=C:\Windows\System32\findstr.exe & call :CREATE_QOS_POLICY
set PROFILENAME=where_QoS & set APPLICATION=C:\Windows\System32\where.exe & call :CREATE_QOS_POLICY
set PROFILENAME=forfiles_QoS & set APPLICATION=C:\Windows\System32\forfiles.exe & call :CREATE_QOS_POLICY
set PROFILENAME=lpq_QoS & set APPLICATION=C:\Windows\System32\lpq.exe & call :CREATE_QOS_POLICY
set PROFILENAME=lpr_QoS & set APPLICATION=C:\Windows\System32\lpr.exe & call :CREATE_QOS_POLICY
set PROFILENAME=lodctr_QoS & set APPLICATION=C:\Windows\System32\lodctr.exe & call :CREATE_QOS_POLICY
set PROFILENAME=unlodctr_QoS & set APPLICATION=C:\Windows\System32\unlodctr.exe & call :CREATE_QOS_POLICY
set PROFILENAME=logman_QoS & set APPLICATION=C:\Windows\System32\logman.exe & call :CREATE_QOS_POLICY
set PROFILENAME=relog_QoS & set APPLICATION=C:\Windows\System32\relog.exe & call :CREATE_QOS_POLICY
set PROFILENAME=tracerpt_QoS & set APPLICATION=C:\Windows\System32\tracerpt.exe & call :CREATE_QOS_POLICY
set PROFILENAME=typeperf_QoS & set APPLICATION=C:\Windows\System32\typeperf.exe & call :CREATE_QOS_POLICY
set PROFILENAME=eventcreate_QoS & set APPLICATION=C:\Windows\System32\eventcreate.exe & call :CREATE_QOS_POLICY
set PROFILENAME=wevtutil_QoS & set APPLICATION=C:\Windows\System32\wevtutil.exe & call :CREATE_QOS_POLICY
set PROFILENAME=wecutil_QoS & set APPLICATION=C:\Windows\System32\wecutil.exe & call :CREATE_QOS_POLICY
set PROFILENAME=bitsadmin_QoS & set APPLICATION=C:\Windows\System32\bitsadmin.exe & call :CREATE_QOS_POLICY
set PROFILENAME=choice_QoS & set APPLICATION=C:\Windows\System32\choice.exe & call :CREATE_QOS_POLICY
set PROFILENAME=clip_QoS & set APPLICATION=C:\Windows\System32\clip.exe & call :CREATE_QOS_POLICY
set PROFILENAME=cmstp_QoS & set APPLICATION=C:\Windows\System32\cmstp.exe & call :CREATE_QOS_POLICY
set PROFILENAME=dnscmd_QoS & set APPLICATION=C:\Windows\System32\dnscmd.exe & call :CREATE_QOS_POLICY
set PROFILENAME=doskey_QoS & set APPLICATION=C:\Windows\System32\doskey.exe & call :CREATE_QOS_POLICY
set PROFILENAME=driverquery_QoS & set APPLICATION=C:\Windows\System32\driverquery.exe & call :CREATE_QOS_POLICY
set PROFILENAME=dtrace_QoS & set APPLICATION=C:\Windows\System32\dtrace.exe & call :CREATE_QOS_POLICY
set PROFILENAME=flattemp_QoS & set APPLICATION=C:\Windows\System32\flattemp.exe & call :CREATE_QOS_POLICY
set PROFILENAME=fondue_QoS & set APPLICATION=C:\Windows\System32\fondue.exe & call :CREATE_QOS_POLICY
set PROFILENAME=fveupdate_QoS & set APPLICATION=C:\Windows\System32\fveupdate.exe & call :CREATE_QOS_POLICY
set PROFILENAME=getmac_QoS & set APPLICATION=C:\Windows\System32\getmac.exe & call :CREATE_QOS_POLICY
set PROFILENAME=graftabl_QoS & set APPLICATION=C:\Windows\System32\graftabl.exe & call :CREATE_QOS_POLICY
set PROFILENAME=hostname_QoS & set APPLICATION=C:\Windows\System32\hostname.exe & call :CREATE_QOS_POLICY
set PROFILENAME=logoff_QoS & set APPLICATION=C:\Windows\System32\logoff.exe & call :CREATE_QOS_POLICY
set PROFILENAME=sdbinst_QoS & set APPLICATION=C:\Windows\System32\sdbinst.exe & call :CREATE_QOS_POLICY
set PROFILENAME=shadow_QoS & set APPLICATION=C:\Windows\System32\shadow.exe & call :CREATE_QOS_POLICY
set PROFILENAME=timeout_QoS & set APPLICATION=C:\Windows\System32\timeout.exe & call :CREATE_QOS_POLICY
set PROFILENAME=ver_QoS & set APPLICATION=C:\Windows\System32\ver.exe & call :CREATE_QOS_POLICY
set PROFILENAME=waitfor_QoS & set APPLICATION=C:\Windows\System32\waitfor.exe & call :CREATE_QOS_POLICY
set PROFILENAME=wbadmin_QoS & set APPLICATION=C:\Windows\System32\wbadmin.exe & call :CREATE_QOS_POLICY
set PROFILENAME=winrm_QoS & set APPLICATION=C:\Windows\System32\winrm.exe & call :CREATE_QOS_POLICY
set PROFILENAME=winrs_QoS & set APPLICATION=C:\Windows\System32\winrs.exe & call :CREATE_QOS_POLICY
set PROFILENAME=winsat_QoS & set APPLICATION=C:\Windows\System32\winsat.exe & call :CREATE_QOS_POLICY
set PROFILENAME=wmic_QoS & set APPLICATION=C:\Windows\System32\wmic.exe & call :CREATE_QOS_POLICY
set PROFILENAME=Chrome_QoS & set APPLICATION="C:\Program Files\Google\Chrome\Application\chrome.exe" & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=Edge_QoS & set APPLICATION="C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=Firefox_QoS & set APPLICATION="C:\Program Files\Mozilla Firefox\firefox.exe" & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=OneDrive_QoS & set APPLICATION=%USERPROFILE%\AppData\Local\Microsoft\OneDrive\OneDrive.exe & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=Dropbox_QoS & set APPLICATION=%USERPROFILE%\AppData\Local\Dropbox\Update\Dropbox.exe & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=Discord_QoS & set APPLICATION=%USERPROFILE%\AppData\Local\Discord\update.exe & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=TeamsUpdate_QoS & set APPLICATION=%USERPROFILE%\AppData\Local\Microsoft\Teams\Update.exe & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=MSTeamsApp_QoS & set APPLICATION="C:\Program Files\WindowsApps\MSTeams_*_x64__8wekyb3d8bbwe\ms-teams.exe" & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=Steam_QoS & set APPLICATION="C:\Program Files (x86)\Steam\steam.exe" & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=SpotifyRoaming_QoS & set APPLICATION=%USERPROFILE%\AppData\Roaming\Spotify\Spotify.exe & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=SpotifyWebHelperRoaming_QoS & set APPLICATION=%USERPROFILE%\AppData\Roaming\Spotify\SpotifyWebHelper.exe & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=SpotifyLocal_QoS & set APPLICATION=%USERPROFILE%\AppData\Local\Spotify\Spotify.exe & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=SpotifyWebHelperLocal_QoS & set APPLICATION=%USERPROFILE%\AppData\Local\Spotify\SpotifyWebHelper.exe & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=VLCUpdater_QoS & set APPLICATION="C:\Program Files (x86)\VLC Updater\vlc-updater.exe" & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=GoogleUpdateX86_QoS & set APPLICATION="C:\Program Files (x86)\Google\Update\GoogleUpdate.exe" & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=GoogleUpdaterX86_QoS & set APPLICATION="C:\Program Files (x86)\Google\Update\updater.exe" & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=GoogleUpdateUser_QoS & set APPLICATION=%USERPROFILE%\AppData\Local\Google\Update\GoogleUpdate.exe & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=GoogleUpdaterUser_QoS & set APPLICATION=%USERPROFILE%\AppData\Local\Google\Update\updater.exe & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=GoogleUpdaterNew_QoS & set APPLICATION="C:\Program Files (x86)\Google\GoogleUpdater\updater.exe" & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=AdobeUpdater6_QoS & set APPLICATION="C:\Program Files (x86)\Common Files\Adobe\Updater6\Adobe_Updater.exe" & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=AdobeARM_QoS & set APPLICATION="C:\Program Files (x86)\Common Files\Adobe\ARM\1.0\AdobeARM.exe" & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=AdobeCollabSync_QoS & set APPLICATION="C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AdobeCollabSync.exe" & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=OfficeC2RClient_QoS & set APPLICATION="C:\Program Files\Common Files\Microsoft Shared\ClickToRun\OfficeC2RClient.exe" & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=NortonNUA_QoS & set APPLICATION="C:\ProgramData\Norton\NUA.exe" & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=NortonAshUpd_QoS & set APPLICATION="C:\Program Files\Norton\Suite\ashUpd.exe" & call :CREATE_QOS_POLICY_NON_NATIVE
set PROFILENAME=NordUpdater_QoS & set APPLICATION="C:\Program Files\NordUpdater\NordUpdateService.exe" & call :CREATE_QOS_POLICY_NON_NATIVE

gpupdate /force >nul 2>&1

rem Deshabilitar lista de servicios
for %%s in (AJRouter ALG AppMgmt AppVClient AssignedAccessManagerSvc AxInstSV BcastDVRUserService BDESVC CDPSvc CDPUserSvc CertPropSvc ClipSVC cloudidsvc COMSysApp ConsentUxUserSvc CscService defragsvc DeviceAssociationBrokerSvc DeviceAssociationService DeviceInstall DevicePickerUserSvc DevicesFlowUserSvc DevQueryBroker diagnosticshub.standardcollector.service diagsvc DialogBlockingService DispBrokerDesktopSvc DisplayEnhancementService DmEnrollmentSvc dmwappushservice DoSvc DPS DsmSvc DsSvc DusmSvc Eaphost EFS embeddedmode EntAppSvc Fax fdPHost fhsvc FontCache FrameServer GraphicsPerfSvc hidserv HvHost icssvc IKEEXT InstallService iphlpsvc IpxlatCfgSvc irmon KtmRm lfsvc lltdsvc lmhosts LxpSvc MapsBroker MessagingService MicrosoftEdgeElevationService MixedRealityOpenXRSvc MSDTC MSiSCSI NaturalAuthentication NcaSvc NcbService NcdAutoSetup Netlogon Netman NetSetupSvc NetTcpPortSharing NgcCtnrSvc NgcSvc NvContainerLocalSystem p2pimsvc p2psvc P9RdrService PcaSvc PeerDistSvc perceptionsimulation PerfHost PhoneSvc PimIndexMaintenanceSvc pla PNRPAutoReg PNRPsvc PolicyAgent PrintNotify PrintWorkflowUserSvc QWAVE RasAuto RasMan RemoteAccess RemoteRegistry RetailDemo RmSvc RpcLocator SCardSvr ScDeviceEnum SCPolicySvc SDRSVC seclogon SEMgrSvc SensorDataService SensorService SensrSvc SessionEnv SgrmBroker shpamsvc SharedAccess SharedRealitySvc SmsRouter SNMPTRAP spectrum SSDPSRV ssh-agent stisvc StorSvc svsvc swprv SysMain TabletInputService TapiSrv TermService TieringEngineService TimeBrokerSvc TokenBroker TrkWks TroubleshootingSvc tzautoupdate UevAgentService UmRdpService upnphost UserDataSvc UsoSvc VacSvc VaultSvc vds vmicguestinterface vmicheartbeat vmickvpexchange vmicrdv vmicshutdown vmictimesync vmicvmsession vmicvss VSS W32Time WaaSMedicSvc WalletService WarpJITSvc WbioSrvc WdiServiceHost WdiSystemHost WdNisSvc WebClient Wecsvc WEPHOSTSVC wercplsupport WerSvc WiaRpc WindowsTrustedRT WindowsTrustedRTProxy WinHttpAutoProxySvc WinRM wisvc wlidsvc wlpasvc WManSvc wmiApSrv WMPNetworkSvc workfolderssvc WPDBusEnum WpcMonSvc WpnService WpnUserService wscsvc WSearch wuauserv WwanSvc XblAuthManager XblGameSave XboxGipSvc XboxNetApiSvc DiagTrack HomeGroupListener HomeGroupProvider) do (
    sc config "%%s" start= disabled >nul 2>&1
    sc stop "%%s" >nul 2>&1
)

rem Windows Update y WaaS
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v "NoAutoUpdate" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v "AUOptions" /t REG_DWORD /d "2" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v "AutomaticMaintenanceEnabled" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update" /v "AUOptions" /t REG_DWORD /d "2" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update" /v "CachedEngineVersion" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update" /v "EnableFeaturedSoftware" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization" /v "DODownloadMode" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\DeliveryOptimization\Config" /v "DODownloadMode" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DriverSearching" /v "DontSearchWindowsUpdate" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" /v "ExcludeWUDriversInQualityUpdate" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\WaaSMedicSvc" /v "Start" /t REG_DWORD /d "4" /f >nul 2>&1
takeown /f "C:\Windows\System32\WaaSMedicAgent.exe" /a >nul 2>&1
icacls "C:\Windows\System32\WaaSMedicAgent.exe" /deny "SYSTEM:(X)" >nul 2>&1
icacls "C:\Windows\System32\WaaSMedicAgent.exe" /deny "Administrators:(X)" >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" /v "TargetReleaseVersion" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" /v "TargetReleaseVersionInfo" /t REG_SZ /d "21H2" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v "ScheduledInstallDay" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v "ScheduledInstallTime" /t REG_DWORD /d "3" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\PreviewBuilds" /v "AllowBuildPreview" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\PreviewBuilds" /v "EnableConfigFlighting" /t REG_DWORD /d "0" /f >nul 2>&1

rem Telemetría/privacidad (bloque único)
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v "AllowTelemetry" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v "DoNotShowFeedbackNotifications" /t REG_DWORD /d "1" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v "AllowDeviceNameInTelemetry" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection" /v "AllowTelemetry" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection" /v "MaxTelemetryAllowed" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v "ContentDeliveryAllowed" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v "SilentInstalledAppsEnabled" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v "PreInstalledAppsEnabled" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v "PreInstalledAppsEverEnabled" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v "OemPreInstalledAppsEnabled" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v "SubscribedContent-338388Enabled" /t REG_DWORD /d "0" /f >nul 2>&1
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v "SubscribedContent-338389Enabled" /t REG_DWORD /d "0" /f >nul 2>&