"""
Build script for compiling Gaming Optimizer with Nuitka
This script creates a standalone Windows executable with all dependencies included.

Usage:
    python build_nuitka.py

Requirements:
    - Nuitka installed: pip install nuitka
    - Visual Studio Build Tools or MinGW64 installed
"""

import subprocess
import sys
import os

def build_with_nuitka():
    """Build the Gaming Optimizer using Nuitka"""
    
    # Main entry point
    main_script = "GUI.py"
    
    # Nuitka compilation command
    nuitka_cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",  # Create standalone executable
        "--onefile",  # Single file output
        "--windows-disable-console",  # No console window
        "--enable-plugin=tk-inter",  # Include tkinter
        "--windows-icon-from-ico=1.ico",  # Application icon
        "--company-name=GamingOptimizer",
        "--product-name=Gaming Optimizer",
        "--file-version=7.4.0",
        "--product-version=7.4.0",
        "--file-description=Advanced Gaming Optimization Tool",
        
        # Include all necessary modules
        "--include-package=psutil",
        "--include-package=win32api",
        "--include-package=win32con",
        "--include-package=win32gui",
        "--include-package=win32process",
        "--include-module=pystray",
        "--include-module=PIL",
        
        # Include data files
        "--include-data-file=1.ico=1.ico",
        "--include-data-files=*.pow=./",  # Power plans
        "--include-data-files=*.bat=./",  # Batch scripts
        "--include-data-files=*.vbs=./",  # VBS scripts
        "--include-data-files=*.reg=./",  # Registry files
        
        # Include Python files as resources (for subprocess execution)
        "--include-data-file=modoagresivo.py=modoagresivo.py",
        "--include-data-file=modonormal.py=modonormal.py",
        "--include-data-file=modojuego.py=modojuego.py",
        "--include-data-file=LIMPIEZA.py=LIMPIEZA.py",
        "--include-data-file=DISCOS.py=DISCOS.py",
        "--include-data-file=RECUPERA.py=RECUPERA.py",
        "--include-data-file=COPIA.py=COPIA.py",
        "--include-data-file=entradas.py=entradas.py",
        
        # Output directory
        "--output-dir=dist",
        
        # Optimization flags
        "--lto=yes",  # Link Time Optimization
        "--assume-yes-for-downloads",
        
        main_script
    ]
    
    print("=" * 70)
    print("Building Gaming Optimizer with Nuitka...")
    print("=" * 70)
    print(f"Main script: {main_script}")
    print("This may take several minutes...\n")
    
    try:
        # Run Nuitka compilation
        result = subprocess.run(nuitka_cmd, check=True)
        
        print("\n" + "=" * 70)
        print("✓ Build completed successfully!")
        print("=" * 70)
        print(f"Executable created in: dist/")
        print("\nNote: First run may take longer as Windows Defender scans the new executable.")
        return 0
        
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 70)
        print("✗ Build failed!")
        print("=" * 70)
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Nuitka is installed: pip install nuitka")
        print("2. Install Visual Studio Build Tools or MinGW64")
        print("3. Check that all dependencies are installed: pip install -r requirements.txt")
        return 1
    except FileNotFoundError:
        print("\n" + "=" * 70)
        print("✗ Nuitka not found!")
        print("=" * 70)
        print("Please install Nuitka: pip install nuitka")
        return 1

def check_requirements():
    """Check if all requirements are met"""
    print("Checking requirements...")
    
    # Check if main script exists
    if not os.path.exists("GUI.py"):
        print("✗ Error: GUI.py not found in current directory")
        return False
    
    # Check if icon exists
    if not os.path.exists("1.ico"):
        print("⚠ Warning: 1.ico not found. Build will proceed without custom icon.")
    
    # Try to import required modules
    try:
        import psutil
        import win32api
        import tkinter
        print("✓ Required Python modules are installed")
    except ImportError as e:
        print(f"✗ Error: Missing required module: {e}")
        print("Install requirements: pip install -r requirements.txt")
        return False
    
    # Check if Nuitka is installed
    try:
        import nuitka
        print(f"✓ Nuitka is installed (version: {nuitka.__version__})")
    except ImportError:
        print("✗ Error: Nuitka is not installed")
        print("Install Nuitka: pip install nuitka")
        return False
    
    print("✓ All requirements met\n")
    return True

if __name__ == "__main__":
    if not check_requirements():
        sys.exit(1)
    
    sys.exit(build_with_nuitka())
