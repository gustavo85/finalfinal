' Script VBS para ejecutar optimize.bat como administrador sin ventana visible
' Autor: Generado automáticamente
' Fecha: 2025-10-25

Option Explicit

Dim objShell, objFSO, strScriptPath, strBatchPath

' Crear objetos necesarios
Set objShell = CreateObject("Shell.Application")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Obtener la ruta del directorio donde se encuentra este script
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Construir la ruta completa del archivo optimize.bat
strBatchPath = objFSO.BuildPath(strScriptPath, "optimize.bat")

' Verificar si el archivo optimize.bat existe
If objFSO.FileExists(strBatchPath) Then
    ' Ejecutar el archivo batch como administrador sin ventana visible
    ' Parámetros de ShellExecute:
    ' - "runas" = ejecutar como administrador
    ' - 0 = ventana oculta (sin ventana visible)
    objShell.ShellExecute "cmd.exe", "/c """ & strBatchPath & """", strScriptPath, "runas", 0
Else
    ' Mostrar mensaje de error si no se encuentra el archivo
    MsgBox "Error: No se encuentra el archivo 'optimize.bat' en la ubicación:" & vbCrLf & strScriptPath, vbCritical, "Archivo no encontrado"
End If

' Limpiar objetos
Set objShell = Nothing
Set objFSO = Nothing