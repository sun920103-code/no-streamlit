"""Quick test: can we reach Wind and download index quotes?"""
import os, sys

# Wind DLL paths
wind_dll_path = r"D:\Wind\x64"
wind_bin_path = r"D:\Wind\bin"
if os.path.exists(wind_dll_path) and hasattr(os, 'add_dll_directory'):
    os.add_dll_directory(wind_dll_path)
if os.path.exists(wind_bin_path) and hasattr(os, 'add_dll_directory'):
    os.add_dll_directory(wind_bin_path)
os.environ['PATH'] = wind_dll_path + ';' + wind_bin_path + ';' + os.environ.get('PATH', '')

try:
    from WindPy import w
    print("[1] WindPy imported OK")
except ImportError as e:
    print(f"[FAIL] Cannot import WindPy: {e}")
    sys.exit(1)

status = w.start()
print(f"[2] w.start() => ErrorCode={status.ErrorCode}")
if status.ErrorCode != 0:
    print("[FAIL] Wind cannot start")
    sys.exit(1)

codes = ["000001.SH","000300.SH","399001.SZ","399006.SZ","000905.SH","000852.SH","HSI.HI"]
print(f"[3] Calling w.wss with {len(codes)} codes...")

data = w.wss(codes, "close,pct_chg", "PriceAdj=F")
print(f"[4] ErrorCode={data.ErrorCode}")
print(f"    Fields={data.Fields}")
print(f"    Codes={data.Codes}")
print(f"    Data length={len(data.Data) if data.Data else 0}")

if data.ErrorCode == 0 and data.Data:
    for j, code in enumerate(codes):
        close_val = data.Data[0][j] if len(data.Data) > 0 and j < len(data.Data[0]) else None
        pct_val = data.Data[1][j] if len(data.Data) > 1 and j < len(data.Data[1]) else None
        print(f"    {code}: close={close_val}, pct_chg={pct_val}")
else:
    print(f"    Raw Data={data.Data}")

w.stop()
print("[5] Done - Wind API test complete")
