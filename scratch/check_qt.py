import sys
try:
    from PyQt5 import QtCore, QtWidgets
    print(f"PyQt5 version: {QtCore.PYQT_VERSION_STR}")
    print(f"Qt version: {QtCore.QT_VERSION_STR}")
    print("PyQt5 imported successfully!")
except ImportError as e:
    print(f"Failed to import PyQt5: {e}")
    print("sys.path:")
    for p in sys.path:
        print(f"  {p}")
