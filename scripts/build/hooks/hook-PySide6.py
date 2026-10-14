# Collect Qt plugins for frozen builds.

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

datas = collect_data_files("PySide6", includes=["**/Qt/plugins/**"])
binaries = collect_dynamic_libs("PySide6")
