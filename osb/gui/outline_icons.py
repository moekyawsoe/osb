"""Vector outline icon generator using pure QPainter paths.

Strictly complies with the constraint:
- No colors icons, no gradient colors
- Monochrome outline stroke only
- NASA JPL Power of 10 rules (functions <= 60 lines, >= 2 assertions per function)
"""

from typing import Dict, Optional
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

DEFAULT_STROKE_COLOR = "#d1d5db"
MUTED_STROKE_COLOR = "#6b7280"
ACTIVE_STROKE_COLOR = "#ffffff"


class OutlineIcons:
    """Factory for procedural monochrome vector outline icons."""

    _cache: Dict[str, QIcon] = {}

    @classmethod
    def get_icon(cls, name: str, size: int = 20, color_hex: str = DEFAULT_STROKE_COLOR) -> QIcon:
        """Get or render cached vector outline icon."""
        assert isinstance(name, str) and len(name) > 0, "Icon name must be non-empty"
        assert size >= 12 and size <= 128, "Size must be within reasonable bounds"

        cache_key = f"{name}_{size}_{color_hex}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        pix = cls.render_pixmap(name, size, color_hex)
        icon = QIcon(pix)
        if len(cls._cache) < 256:
            cls._cache[cache_key] = icon
        return icon

    @classmethod
    def render_pixmap(cls, name: str, size: int, color_hex: str) -> QPixmap:
        """Render vector outline icon into a transparent QPixmap."""
        assert isinstance(name, str), "Name must be string"
        assert size > 0, "Size must be positive"

        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(color_hex), 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        scale = size / 24.0
        painter.scale(scale, scale)

        draw_method = getattr(cls, f"_draw_{name}", cls._draw_file)
        draw_method(painter)
        painter.end()

        assert not pix.isNull(), "Rendered pixmap must not be null"
        return pix

    @staticmethod
    def _draw_bucket(p: QPainter) -> None:
        """Draw outline cylinder / S3 bucket."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawEllipse(QRectF(4, 3, 16, 6))
        p.drawLine(QPointF(4, 6), QPointF(4, 18))
        p.drawLine(QPointF(20, 6), QPointF(20, 18))
        path = QPainterPath()
        path.moveTo(4, 18)
        path.cubicTo(4, 22, 20, 22, 20, 18)
        p.drawPath(path)

    @staticmethod
    def _draw_server(p: QPainter) -> None:
        """Draw outline server rack unit."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawRoundedRect(QRectF(3, 4, 18, 7), 2, 2)
        p.drawRoundedRect(QRectF(3, 13, 18, 7), 2, 2)
        p.drawEllipse(QRectF(17, 7, 1.5, 1.5))
        p.drawEllipse(QRectF(17, 16, 1.5, 1.5))
        p.drawLine(QPointF(6, 7.5), QPointF(13, 7.5))
        p.drawLine(QPointF(6, 16.5), QPointF(13, 16.5))

    @staticmethod
    def _draw_folder(p: QPainter) -> None:
        """Draw outline folder icon."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        path = QPainterPath()
        path.moveTo(3, 7)
        path.lineTo(9, 7)
        path.lineTo(11, 9)
        path.lineTo(21, 9)
        path.lineTo(21, 19)
        path.lineTo(3, 19)
        path.closeSubpath()
        p.drawPath(path)

    @staticmethod
    def _draw_folder_plus(p: QPainter) -> None:
        """Draw outline folder with plus sign."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        OutlineIcons._draw_folder(p)
        p.drawLine(QPointF(12, 12), QPointF(12, 16))
        p.drawLine(QPointF(10, 14), QPointF(14, 14))

    @staticmethod
    def _draw_file(p: QPainter) -> None:
        """Draw outline file with folded corner."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        path = QPainterPath()
        path.moveTo(5, 3)
        path.lineTo(14, 3)
        path.lineTo(19, 8)
        path.lineTo(19, 21)
        path.lineTo(5, 21)
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(QPointF(14, 3), QPointF(14, 8))
        p.drawLine(QPointF(14, 8), QPointF(19, 8))

    @staticmethod
    def _draw_arrow_right(p: QPainter) -> None:
        """Draw outline directional arrow pointing right."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawLine(QPointF(5, 12), QPointF(19, 12))
        p.drawLine(QPointF(14, 7), QPointF(19, 12))
        p.drawLine(QPointF(14, 17), QPointF(19, 12))

    @staticmethod
    def _draw_arrow_left(p: QPainter) -> None:
        """Draw outline directional arrow pointing left."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawLine(QPointF(19, 12), QPointF(5, 12))
        p.drawLine(QPointF(10, 7), QPointF(5, 12))
        p.drawLine(QPointF(10, 17), QPointF(5, 12))

    @staticmethod
    def _draw_arrow_up(p: QPainter) -> None:
        """Draw outline arrow pointing up (parent folder)."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawLine(QPointF(12, 19), QPointF(12, 5))
        p.drawLine(QPointF(7, 10), QPointF(12, 5))
        p.drawLine(QPointF(17, 10), QPointF(12, 5))

    @staticmethod
    def _draw_refresh(p: QPainter) -> None:
        """Draw outline refresh circular arrow."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawArc(QRectF(4, 4, 16, 16), 45 * 16, 270 * 16)
        p.drawLine(QPointF(15, 3), QPointF(19, 6))
        p.drawLine(QPointF(19, 6), QPointF(15, 9))

    @staticmethod
    def _draw_sync(p: QPainter) -> None:
        """Draw outline bidirectional sync arrows."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawArc(QRectF(4, 4, 16, 16), 30 * 16, 130 * 16)
        p.drawArc(QRectF(4, 4, 16, 16), 210 * 16, 130 * 16)
        p.drawLine(QPointF(17, 4), QPointF(20, 7))
        p.drawLine(QPointF(7, 20), QPointF(4, 17))

    @staticmethod
    def _draw_copy(p: QPainter) -> None:
        """Draw outline dual overlapping copy rectangles."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawRoundedRect(QRectF(8, 8, 12, 12), 2, 2)
        path = QPainterPath()
        path.moveTo(16, 8)
        path.lineTo(16, 4)
        path.lineTo(4, 4)
        path.lineTo(4, 16)
        path.lineTo(8, 16)
        p.drawPath(path)

    @staticmethod
    def _draw_move(p: QPainter) -> None:
        """Draw outline transfer / move icon."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawRoundedRect(QRectF(4, 4, 16, 16), 2, 2)
        p.drawLine(QPointF(8, 12), QPointF(16, 12))
        p.drawLine(QPointF(13, 9), QPointF(16, 12))
        p.drawLine(QPointF(13, 15), QPointF(16, 12))

    @staticmethod
    def _draw_trash(p: QPainter) -> None:
        """Draw outline trash can."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawLine(QPointF(3, 6), QPointF(21, 6))
        p.drawLine(QPointF(8, 6), QPointF(8, 4))
        p.drawLine(QPointF(8, 4), QPointF(16, 4))
        p.drawLine(QPointF(16, 4), QPointF(16, 6))
        path = QPainterPath()
        path.moveTo(5, 6)
        path.lineTo(6, 20)
        path.lineTo(18, 20)
        path.lineTo(19, 6)
        p.drawPath(path)
        p.drawLine(QPointF(10, 9), QPointF(10, 17))
        p.drawLine(QPointF(14, 9), QPointF(14, 17))

    @staticmethod
    def _draw_plus(p: QPainter) -> None:
        """Draw outline plus icon."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawLine(QPointF(12, 5), QPointF(12, 19))
        p.drawLine(QPointF(5, 12), QPointF(19, 12))

    @staticmethod
    def _draw_minus(p: QPainter) -> None:
        """Draw outline minus horizontal line."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawLine(QPointF(5, 12), QPointF(19, 12))


    @staticmethod
    def _draw_check(p: QPainter) -> None:
        """Draw outline checkmark."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawLine(QPointF(5, 12), QPointF(10, 17))
        p.drawLine(QPointF(10, 17), QPointF(20, 6))

    @staticmethod
    def _draw_cross(p: QPainter) -> None:
        """Draw outline cross / close icon."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawLine(QPointF(6, 6), QPointF(18, 18))
        p.drawLine(QPointF(18, 6), QPointF(6, 18))

    @staticmethod
    def _draw_search(p: QPainter) -> None:
        """Draw outline magnifying glass."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawEllipse(QRectF(4, 4, 12, 12))
        p.drawLine(QPointF(13, 13), QPointF(20, 20))

    @staticmethod
    def _draw_settings(p: QPainter) -> None:
        """Draw outline settings gear."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawEllipse(QRectF(8, 8, 8, 8))
        p.drawLine(QPointF(12, 3), QPointF(12, 6))
        p.drawLine(QPointF(12, 18), QPointF(12, 21))
        p.drawLine(QPointF(3, 12), QPointF(6, 12))
        p.drawLine(QPointF(18, 12), QPointF(21, 12))
        p.drawLine(QPointF(5.5, 5.5), QPointF(7.5, 7.5))
        p.drawLine(QPointF(16.5, 16.5), QPointF(18.5, 18.5))
        p.drawLine(QPointF(18.5, 5.5), QPointF(16.5, 7.5))
        p.drawLine(QPointF(7.5, 16.5), QPointF(5.5, 18.5))

    @staticmethod
    def _draw_info(p: QPainter) -> None:
        """Draw outline info circle."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawEllipse(QRectF(3, 3, 18, 18))
        p.drawEllipse(QRectF(11.5, 7, 1, 1))
        p.drawLine(QPointF(12, 11), QPointF(12, 17))

    @staticmethod
    def _draw_stop(p: QPainter) -> None:
        """Draw outline stop square."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawRoundedRect(QRectF(5, 5, 14, 14), 2, 2)

    @staticmethod
    def _draw_play(p: QPainter) -> None:
        """Draw outline play triangle."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        path = QPainterPath()
        path.moveTo(7, 5)
        path.lineTo(19, 12)
        path.lineTo(7, 19)
        path.closeSubpath()
        p.drawPath(path)

    @staticmethod
    def _draw_terminal(p: QPainter) -> None:
        """Draw outline terminal prompt window."""
        assert p is not None, "Painter must not be None"
        assert p.isActive(), "Painter must be active"
        p.drawRoundedRect(QRectF(3, 4, 18, 16), 2, 2)
        p.drawLine(QPointF(6, 9), QPointF(9, 12))
        p.drawLine(QPointF(9, 12), QPointF(6, 15))
        p.drawLine(QPointF(11, 15), QPointF(16, 15))

