"""生成「第一步」应用图标"""
import os, sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPainter, QPixmap, QColor, QPen, QBrush, QFont, QRadialGradient, QConicalGradient
from PySide6.QtCore import Qt, QPointF

app = QApplication(sys.argv)  # Required before QPixmap

dir_path = os.path.dirname(os.path.abspath(__file__))

# Create a 256x256 icon
size = 256
pix = QPixmap(size, size)
pix.fill(Qt.transparent)

p = QPainter(pix)
p.setRenderHint(QPainter.Antialiasing)

cx, cy = size / 2, size / 2
r = 110

# Background gradient (warm dark)
bg_grad = QRadialGradient(cx, cy, r * 1.3)
bg_grad.setColorAt(0, QColor("#2a2a2a"))
bg_grad.setColorAt(1, QColor("#1a1a1a"))
p.setBrush(QBrush(bg_grad))
p.setPen(Qt.NoPen)
p.drawEllipse(QPointF(cx, cy), r, r)

# Gold ring
ring_grad = QConicalGradient(cx, cy, -90)
ring_grad.setColorAt(0, QColor("#d4a853"))
ring_grad.setColorAt(0.4, QColor("#f0d080"))
ring_grad.setColorAt(0.7, QColor("#d4a853"))
ring_grad.setColorAt(1, QColor("#d4a853"))
p.setPen(QPen(QBrush(ring_grad), 8, Qt.SolidLine, Qt.RoundCap))
p.setBrush(Qt.NoBrush)
p.drawArc(pix.rect().adjusted(20, 20, -20, -20), 90 * 16, -300 * 16)

# "1" in center
font = QFont("Noto Serif SC", 100, QFont.Bold)
p.setFont(font)
p.setPen(QColor("#d4a853"))
p.drawText(pix.rect(), Qt.AlignCenter, "1")

# Small step marker
p.setPen(QPen(QColor("#d4a853"), 3))
p.drawLine(int(cx - 30), int(cy + 70), int(cx), int(cy + 85))
p.drawLine(int(cx), int(cy + 85), int(cx + 30), int(cy + 70))

p.end()

# Save as ico
icon_path = os.path.join(dir_path, "app.ico")
pix.save(icon_path, "ICO")
print(f"Icon saved: {icon_path}")
