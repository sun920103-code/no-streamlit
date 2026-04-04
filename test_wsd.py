import os
import sys

wind_dll_path = r"D:\Wind\x64"
wind_bin_path = r"D:\Wind\bin"
if os.path.exists(wind_dll_path):
    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(wind_dll_path)
    if os.path.exists(wind_bin_path) and hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(wind_bin_path)
    os.environ['PATH'] = wind_dll_path + ';' + wind_bin_path + ';' + os.environ.get('PATH', '')

from WindPy import w
w.start()

print("Testing w.wsd for a fund history...")
res = w.wsd("000001.OF", "nav", "2026-03-25", "2026-04-01")
print(f"ErrorCode: {res.ErrorCode}")
if res.ErrorCode == 0:
    print(f"Rows: {len(res.Data[0])}")
    print(f"Data: {res.Data[0][:3]}")
else:
    print("Failed")
w.stop()
