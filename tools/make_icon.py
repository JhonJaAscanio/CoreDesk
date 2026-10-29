"""Genera icon.ico (16-256 px) con el estilo de la aplicación: hexágono de neón cian/violeta con una "C"."""
import io
import math
import os
import sys

from PIL import Image
from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, QRectF, Qt
from PyQt6.QtGui import (QBrush, QColor, QFont, QGuiApplication, QImage, QLinearGradient, QPainter, QPainterPath, QPen,
                         QRadialGradient)

CYAN, VIOLET, BG, SURFACE = "#22D3EE", "#8B5CF6", "#060A13", "#0F1A33"


def hexagon(center, radius):
    path = QPainterPath()
    for i in range(6):
        angle = math.radians(60 * i - 90)
        point = QPointF(center.x() + radius * math.cos(angle), center.y() + radius * math.sin(angle))
        path.moveTo(point) if i == 0 else path.lineTo(point)
    path.closeSubpath()
    return path


def letter_path(size, center, pixel_size):
    font = QFont("Segoe UI")
    font.setPixelSize(int(pixel_size))
    font.setWeight(QFont.Weight.Black)
    path = QPainterPath()
    path.addText(0, 0, font, "C")
    rect = path.boundingRect()
    return path.translated(center.x() - rect.center().x(), center.y() - rect.center().y())


def gradient(x1, y1, x2, y2):
    g = QLinearGradient(x1, y1, x2, y2)
    g.setColorAt(0, QColor(CYAN))
    g.setColorAt(1, QColor(VIOLET))
    return g


def render(size):
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    p = QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    u = size / 256
    c = QPointF(size / 2, size / 2)

    if size < 48:
        # Tamaños pequeños: hexágono macizo y "C" oscura para que se lea bien
        p.fillPath(hexagon(c, size / 2 - 0.5), gradient(0, 0, size, size))
        p.fillPath(letter_path(size, QPointF(c.x(), c.y() + 0.5 * u), size * 0.56), QColor(BG))
        p.end()
        return image

    # Fondo: cuadrado redondeado oscuro con un leve degradado
    background = QPainterPath()
    background.addRoundedRect(QRectF(8 * u, 8 * u, 240 * u, 240 * u), 58 * u, 58 * u)
    bg = QLinearGradient(0, 0, 0, size)
    bg.setColorAt(0, QColor(SURFACE))
    bg.setColorAt(1, QColor(BG))
    p.fillPath(background, bg)
    p.setClipPath(background)

    # Resplandor central
    glow = QRadialGradient(c, 120 * u)
    glow.setColorAt(0, QColor(34, 211, 238, 70))
    glow.setColorAt(1, QColor(34, 211, 238, 0))
    p.fillRect(QRectF(0, 0, size, size), glow)

    # Anillo hexagonal de neón con halo
    ring = hexagon(c, 86 * u)
    for width, alpha in ((34, 18), (24, 35), (16, 60)):
        color = QColor(CYAN)
        color.setAlpha(alpha)
        p.setPen(QPen(color, width * u, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.drawPath(ring)
    p.setPen(QPen(QBrush(gradient(40 * u, 40 * u, 216 * u, 216 * u)), 10 * u, Qt.PenStyle.SolidLine,
                  Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.drawPath(ring)

    # Monograma "C" con degradado claro
    letter = letter_path(size, QPointF(c.x(), c.y() + 4 * u), 118 * u)
    shade = QLinearGradient(0, 70 * u, 0, 190 * u)
    shade.setColorAt(0, QColor("#F1F5FB"))
    shade.setColorAt(1, QColor("#7DE3F4"))
    p.fillPath(letter, shade)

    # Borde sutil del fondo
    p.setClipping(False)
    p.setPen(QPen(QColor(255, 255, 255, 28), 2 * u))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(background)
    p.end()
    return image


def to_pil(image):
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return Image.open(io.BytesIO(bytes(data))).convert("RGBA")


if __name__ == "__main__":
    out_ico, preview = sys.argv[1], sys.argv[2]
    app = QGuiApplication(sys.argv)
    sizes = [16, 20, 24, 32, 40, 48, 64, 96, 128, 256]
    frames = {s: to_pil(render(s)) for s in sizes}
    frames[256].save(out_ico, format="ICO", sizes=[(s, s) for s in sizes],
                     append_images=[frames[s] for s in sizes if s != 256], bitmap_format="png")
    # Vista previa de todos los tamaños sobre fondo claro y oscuro
    sheet = Image.new("RGBA", (sum(sizes) + 20 * len(sizes) + 20, 2 * 256 + 60), (255, 255, 255, 255))
    sheet.paste((6, 10, 19, 255), (0, 256 + 30, sheet.width, sheet.height))
    x = 20
    for s in sizes:
        for y0 in (10, 256 + 40):
            sheet.alpha_composite(frames[s], (x, y0 + (256 - s)))
        x += s + 20
    sheet.save(preview)
    print("ok", os.path.getsize(out_ico), "bytes")
