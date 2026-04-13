import win32gui
try:
    # In some versions of pywin32, EnumDisplayMonitors is in win32api, 
    # but win32gui might have some monitor related functions.
    print(dir(win32gui))
except Exception as e:
    print(e)
