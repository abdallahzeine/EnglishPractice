from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QRect
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QWidget


def fade_in(widget: QWidget, duration_ms: int = 250) -> QPropertyAnimation:
    """Fade a widget in via QGraphicsOpacityEffect.
    Caller must keep the returned animation alive until it finishes."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(duration_ms)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
    widget.show()
    animation.start()
    return animation


def slide_in(widget: QWidget, offset_px: int = 24, duration_ms: int = 250) -> QPropertyAnimation:
    """Slide a widget up into its current geometry.
    Caller must keep the returned animation alive until it finishes."""
    end = widget.geometry()
    start = QRect(end.x(), end.y() + offset_px, end.width(), end.height())
    animation = QPropertyAnimation(widget, b"geometry", widget)
    animation.setDuration(duration_ms)
    animation.setStartValue(start)
    animation.setEndValue(end)
    animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
    widget.show()
    animation.start()
    return animation
