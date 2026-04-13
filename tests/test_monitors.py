import win32api
try:
    monitors = win32api.EnumDisplayMonitors()
    for m in monitors:
        print(m)
except Exception as e:
    print(e)
