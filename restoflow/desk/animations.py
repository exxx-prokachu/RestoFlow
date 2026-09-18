from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QTimer
from PyQt6.QtWidgets import QWidget

QWIDGETSIZE_MAX = 16777215


def fade_in(widget: QWidget, duration: int = 300, delay: int = 0) -> None:
    """Каскадное появление виджета через нативное свойство maximumHeight.
    Не использует QGraphicsOpacityEffect (нестабилен в ряде сборок PyQt6)."""
    widget.setVisible(False)
    widget.setMaximumHeight(0)

    def _show():
        widget.setVisible(True)
        target_h = max(widget.sizeHint().height(), 120)
        anim = QPropertyAnimation(widget, b"maximumHeight", widget)
        anim.setDuration(duration)
        anim.setStartValue(0)
        anim.setEndValue(target_h)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        widget._rf_anim = anim
        anim.finished.connect(lambda: widget.setMaximumHeight(QWIDGETSIZE_MAX))
        anim.start()

    QTimer.singleShot(delay, _show)


def clear_fade(widget: QWidget) -> None:
    """Безопасная остановка анимации перед удалением виджета (для канбана)."""
    anim = getattr(widget, "_rf_anim", None)
    if anim is not None:
        anim.stop()
        widget._rf_anim = None
    widget.setMaximumHeight(QWIDGETSIZE_MAX)


def fade_in_window(window: QWidget, duration: int = 450) -> None:
    """Плавное появление главного окна (нативное windowOpacity)."""
    window.setWindowOpacity(0.0)
    anim = QPropertyAnimation(window, b"windowOpacity", window)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    window._rf_win_anim = anim
    anim.finished.connect(lambda: window.setWindowOpacity(1.0))
    anim.start()