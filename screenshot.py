"""生成「第一步」预览截图"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from app import FirstStepApp, THEMES, apply_theme, _current_theme

app = QApplication(sys.argv)
app.setApplicationName("第一步")

# Start with warm gold theme
win = FirstStepApp()

# Give it time to render, then save screenshots
def capture():
    # Save dark theme
    pix = win.grab()
    pix.save(os.path.join(os.path.dirname(__file__), "preview_warm.png"))
    print("暖金截图已保存: preview_warm.png")

    # Switch to light theme
    names = list(THEMES.keys())
    win.cycle_theme()  # switches to 日初
    QTimer.singleShot(300, capture_light)

def capture_light():
    pix = win.grab()
    pix.save(os.path.join(os.path.dirname(__file__), "preview_light.png"))
    print("日初截图已保存: preview_light.png")
    app.quit()

QTimer.singleShot(500, capture)
app.exec()
