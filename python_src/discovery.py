import win32gui

def enum_windows_callback(hwnd, list):
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if title:
            list.append((hwnd, title))

if __name__ == "__main__":
    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)
    for hwnd, title in windows:
        print(f"{hwnd}: {title}")
