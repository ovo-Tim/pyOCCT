import logging
import os
import sys

# import faulthandler; faulthandler.enable()

from OCCT.AIS import AIS_Shape
from OCCT.gp import gp_Pln, gp_Pnt, gp_Dir, gp_Vec, gp_Lin, gp
from OCCT.TopAbs import (
    TopAbs_FACE,
    TopAbs_EDGE,
    TopAbs_VERTEX,
    TopAbs_SHELL,
    TopAbs_SOLID,
)
from OCCT.Display import OCCViewer
from OCCT.Prs3d import  Prs3d_TypeOfHighlight_LocalDynamic, Prs3d_TypeOfHighlight_LocalSelected, Prs3d_TypeOfHighlight_Dynamic, Prs3d_TypeOfHighlight_Selected
from OCCT.Quantity import Quantity_NOC_LIGHTSEAGREEN, Quantity_NOC_LIGHTSKYBLUE, Quantity_Color
from OCCT.Geom import Geom_Line, Geom_Plane
from OCCT.GeomAPI import GeomAPI_IntCS

from qtpy import QtGui, QtWidgets, QtCore

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger(__name__)


class qtBaseViewer(QtWidgets.QWidget):
    """The base Qt Widget for an OCC viewer"""

    def __init__(self, parent=None):
        super(qtBaseViewer, self).__init__(parent)
        self._display = OCCViewer.Viewer3d()
        self._inited = False

        # # enable Mouse Tracking
        self.setMouseTracking(True)

        self.setAttribute(QtCore.Qt.WA_NativeWindow)
        self.setAttribute(QtCore.Qt.WA_PaintOnScreen)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground)

        self.setAutoFillBackground(False)

        self.setContentsMargins(0,0,0,0)


class qtViewer3d(qtBaseViewer):

    # emit signal when selection is changed
    # is a list of TopoDS_*
    HAVE_PYQT_SIGNAL = False
    if hasattr(QtCore, "pyqtSignal"):  # PyQt
        sig_topods_selected = QtCore.pyqtSignal(list)
        HAVE_PYQT_SIGNAL = True
    elif hasattr(QtCore, "Signal"):  # PySide2
        sig_topods_selected = QtCore.Signal(list)
        HAVE_PYQT_SIGNAL = True

    def __init__(self, *kargs):
        super().__init__()

        self.setObjectName("qt_viewer_3d")

        self.setAttribute(QtCore.Qt.WA_DontCreateNativeAncestors)
        
        self._drawbox = False
        self._zoom_area = False
        self._select_area = False
        self._inited = False
        self._leftisdown = False
        self._middleisdown = False
        self._rightisdown = False
        self._selection = None
        self._drawtext = True
        self._qApp = QtWidgets.QApplication.instance()
        self._key_map = {}
        self._current_cursor = "arrow"
        self._available_cursors = {}

        self.mouse_pos = [0,0]
        self.zoom_at_cursor = True
        self.zoom_speed = 0.1
        
        self._select_solid = False

        self.InitDriver()
        self.set_highlight()

        self.mouse_3d_pos = [0,0,0]

        self.grid_snap = 0 # Set 0 to disable 
        self.activity_plane: gp_Pln = gp_Pln(gp_Pnt(0,0,0),gp_Dir(0,0,1))

    def select_solid(self):
        if len(self._display.selected_shapes) and not self._select_solid:
            # print(1)
            self._display.SetSelectionMode(TopAbs_SOLID)
            self._select_solid = True
        else:
            self._select_solid = False
            self._display.Context.Activate(AIS_Shape.SelectionMode_(TopAbs_FACE), True) 
            self._display.Context.Activate(AIS_Shape.SelectionMode_(TopAbs_EDGE), True) 
            self._display.Context.Activate(AIS_Shape.SelectionMode_(TopAbs_VERTEX), True) 

    @property
    def qApp(self):
        # reference to QApplication instance
        return self._qApp

    @qApp.setter
    def qApp(self, value):
        self._qApp = value

    def InitDriver(self):
        self._display.Create(window_handle=int(self.winId()), parent=self)
        # background gradient
        self._display.SetModeShaded()
        self._inited = True
        # dict mapping keys to functions
        self._key_map = {
            ord("W"): self._display.SetModeWireFrame,
            ord("S"): self._display.SetModeShaded,
            ord("A"): self._display.EnableAntiAliasing,
            ord("B"): self._display.DisableAntiAliasing,
            ord("H"): self._display.SetModeHLR,
            ord("F"): self._display.FitAll,
            ord("G"): self.select_solid,
        }
        self.createCursors()

    def createCursors(self):
        module_pth = os.path.abspath(os.path.dirname(__file__))
        icon_pth = os.path.join(module_pth, "icons")

        _CURSOR_PIX_ROT = QtGui.QPixmap(os.path.join(icon_pth, "cursor-rotate.png"))
        _CURSOR_PIX_PAN = QtGui.QPixmap(os.path.join(icon_pth, "cursor-pan.png"))
        _CURSOR_PIX_ZOOM = QtGui.QPixmap(os.path.join(icon_pth, "cursor-magnify.png"))
        _CURSOR_PIX_ZOOM_AREA = QtGui.QPixmap(
            os.path.join(icon_pth, "cursor-magnify-area.png")
        )

        self._available_cursors = {
            "arrow": QtGui.QCursor(QtCore.Qt.ArrowCursor),  # default
            "pan": QtGui.QCursor(_CURSOR_PIX_PAN),
            "rotate": QtGui.QCursor(_CURSOR_PIX_ROT),
            "zoom": QtGui.QCursor(_CURSOR_PIX_ZOOM),
            "zoom-area": QtGui.QCursor(_CURSOR_PIX_ZOOM_AREA),
        }

        self._current_cursor = "arrow"

    def keyPressEvent(self, event):
        super(qtViewer3d, self).keyPressEvent(event)
        code = event.key()
        if code in self._key_map:
            self._key_map[code]()
        elif code in range(256):
            log.info(
                'key: "%s"(code %i) not mapped to any function' % (chr(code), code)
            )
        else:
            log.info("key: code %i not mapped to any function" % code)

    def paintEvent(self, event):
        if not self._inited:
            self.InitDriver()

        self._display.View.MustBeResized()
        self._display.Repaint()
        if self._drawbox:
            painter = QtGui.QPainter(self)
            painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0), 2))
            rect = QtCore.QRect(*self._drawbox)
            painter.drawRect(rect)

    def wheelEvent(self, event):
        if self.zoom_at_cursor:
            self._display.View.StartZoomAtPoint(self.mouse_pos[0], self.mouse_pos[1])
            self._display.View.ZoomAtPoint(0, 0, int(event.angleDelta().y() * self.zoom_speed), 0)
        else:
            delta = event.angleDelta().y()
            if delta > 0:
                zoom_factor = 1.5
            else:
                zoom_factor = 0.75
            self._display.ZoomFactor(zoom_factor)

    @property
    def cursor(self):
        return self._current_cursor

    @cursor.setter
    def cursor(self, value):
        if not self._current_cursor == value:

            self._current_cursor = value
            cursor = self._available_cursors.get(value)

            if cursor:
                self.qApp.setOverrideCursor(cursor)
            else:
                self.qApp.restoreOverrideCursor()

    def mousePressEvent(self, event):
        self.setFocus()
        ev = event.pos()
        self.dragStartPosX = ev.x()
        self.dragStartPosY = ev.y()
        self._display.StartRotation(self.dragStartPosX, self.dragStartPosY)

    def mouseReleaseEvent(self, event):
        pt = event.pos()
        modifiers = event.modifiers()

        if event.button() == QtCore.Qt.LeftButton:
            self.select_solid()
            if self._select_area:
                [Xmin, Ymin, dx, dy] = self._drawbox
                self._display.SelectArea(Xmin, Ymin, Xmin + dx, Ymin + dy)
                self._select_area = False
            elif modifiers == QtCore.Qt.ShiftModifier:
                self._display.ShiftSelect(pt.x(), pt.y())
            else:
                # single select otherwise
                self._display.Select(pt.x(), pt.y())

                if self._display.selected_shapes is not None:
                    self.sig_topods_selected.emit(self._display.selected_shapes)

        elif event.button() == QtCore.Qt.RightButton:
            if self._zoom_area:
                [Xmin, Ymin, dx, dy] = self._drawbox
                self._display.ZoomArea(Xmin, Ymin, Xmin + dx, Ymin + dy)
                self._zoom_area = False

        self.cursor = "arrow"

    def DrawBox(self, event):
        tolerance = 2
        pt = event.pos()
        dx = pt.x() - self.dragStartPosX
        dy = pt.y() - self.dragStartPosY
        if abs(dx) <= tolerance and abs(dy) <= tolerance:
            return
        self._drawbox = [self.dragStartPosX, self.dragStartPosY, dx, dy]

    def mouseMoveEvent(self, evt):
        super().mouseMoveEvent(evt)
        try:
            pt = evt.pos()
            buttons = evt.buttons()
            modifiers = evt.modifiers()

            self.mouse_pos = [pt.x(), pt.y()]
            off_mouse_pos = pt.x(), pt.y()

            mouse_3d_pos = self.ConvertPos(*off_mouse_pos)
            if self.grid_snap:
                grid_pos = self._display.View.ConvertToGrid(*off_mouse_pos)
                for i in range(2):
                    lenth = self._display.View.Convert(abs(mouse_3d_pos[i] - grid_pos[i]))
                    if lenth < self.grid_snap:
                        self.mouse_3d_pos[i] = grid_pos[i]
                    else:
                        self.mouse_3d_pos[i] = mouse_3d_pos[i]
            else:
                self.mouse_3d_pos = mouse_3d_pos

            # ROTATE
            if buttons == QtCore.Qt.LeftButton and not modifiers == QtCore.Qt.ShiftModifier:
                self.cursor = "rotate"
                self._display.Rotation(pt.x(), pt.y())
                self._drawbox = False
            # DYNAMIC ZOOM
            elif (
                buttons == QtCore.Qt.RightButton
                and not modifiers == QtCore.Qt.ShiftModifier
            ):
                self.cursor = "zoom"
                self._display.Repaint()
                self._display.DynamicZoom(
                    abs(self.dragStartPosX),
                    abs(self.dragStartPosY),
                    abs(pt.x()),
                    abs(pt.y()),
                )
                self.dragStartPosX = pt.x()
                self.dragStartPosY = pt.y()
                self._drawbox = False
            # PAN
            elif buttons == QtCore.Qt.MiddleButton:
                dx = pt.x() - self.dragStartPosX
                dy = pt.y() - self.dragStartPosY
                self.dragStartPosX = pt.x()
                self.dragStartPosY = pt.y()
                self.cursor = "pan"
                self._display.Pan(dx, -dy)
                self._drawbox = False
            # DRAW BOX
            # ZOOM WINDOW
            elif buttons == QtCore.Qt.RightButton and modifiers == QtCore.Qt.ShiftModifier:
                self._zoom_area = True
                self.cursor = "zoom-area"
                self.DrawBox(evt)
                self.update()
            # SELECT AREA
            elif buttons == QtCore.Qt.LeftButton and modifiers == QtCore.Qt.ShiftModifier:
                self._select_area = True
                self.DrawBox(evt)
                self.update()
            else:
                self._drawbox = False
                
                self._display.MoveTo(*off_mouse_pos) # Change by potato-pythonocc forum.qt.io/topic/147605/get-incorrect-widget-size-by-window-handle
                self.cursor = "arrow"
        except Exception as e:
            logging.error(e)

    def set_highlight(self, 
                        select_color = Quantity_Color(Quantity_NOC_LIGHTSEAGREEN),
                        select_DisplayMode = 1,
                        select_transparency = 0.5,
                        dynamic_color = Quantity_Color(Quantity_NOC_LIGHTSKYBLUE),
                        dynamic_DisplayMode = 1,
                        dynamic_transparency = 0.35
                      ):
        '''
        Sets the highlight styles for the local select, select, local dynamic, and dynamic features of the display context.

        Parameters:
            select_color (Quantity_Color): The color for the local select and select styles. Default is Quantity_Color(Quantity_NOC_LIGHTSEAGREEN).
            select_DisplayMode (int): The display mode for the local select and select styles. Default is 1.
            select_transparency (float): The transparency for the local select and select styles. Default is 0.5.
            dynamic_color (Quantity_Color): The color for the local dynamic and dynamic styles. Default is Quantity_Color(Quantity_NOC_LIGHTSKYBLUE).
            dynamic_DisplayMode (int): The display mode for the local dynamic and dynamic styles. Default is 1.
            dynamic_transparency (float): The transparency for the local dynamic and dynamic styles. Default is 0.35.
        '''
        self.LocalSelect_style = self._display.Context.HighlightStyle(Prs3d_TypeOfHighlight_LocalSelected)
        self.LocalSelect_style.SetColor(select_color)
        self.LocalSelect_style.SetDisplayMode(select_DisplayMode)
        self.LocalSelect_style.SetTransparency(select_transparency)

        self.select_style = self._display.Context.HighlightStyle(Prs3d_TypeOfHighlight_Selected)
        self.select_style.SetColor(select_color)
        self.select_style.SetDisplayMode(select_DisplayMode)
        self.select_style.SetTransparency(select_transparency)

        self.LocalDynamic_style = self._display.Context.HighlightStyle(Prs3d_TypeOfHighlight_LocalDynamic)
        self.LocalDynamic_style.SetColor(dynamic_color)
        self.LocalDynamic_style.SetDisplayMode(dynamic_DisplayMode)
        self.LocalDynamic_style.SetTransparency(dynamic_transparency)

        self.Dynamic_style = self._display.Context.HighlightStyle(Prs3d_TypeOfHighlight_Dynamic)
        self.Dynamic_style.SetColor(dynamic_color)
        self.Dynamic_style.SetDisplayMode(dynamic_DisplayMode)
        self.Dynamic_style.SetTransparency(dynamic_transparency)

    def ConvertPos(self, x:int, y:int, PlaneOfTheView:gp_Pln = None):
        """
        Converts the given x and y coordinates to a 3D coordinate in the view.

        Args:
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            PlaneOfTheView (gp_Pln, optional): The plane of the view. Defaults to None.

        Returns:
            tuple: A tuple containing the x, y, and z coordinates of the converted point.

        Raises:
            Exception: If an error occurs during the conversion.

        Example:
            >>> ConvertPos(100, 200)
            (1.0, 2.0, 3.0)
        """

        try:
            X,Y,Z,VX,VY,VZ = self._display.View.ConvertWithProj(x, y, 0, 0, 0, 0, 0, 0)
            P1 = gp_Pnt()
            Vp2 = gp_Vec()
            P1.SetCoord(X, Y, Z)
            Vp2.SetCoord(VX,VY,VZ)
            gpLin = gp_Lin(P1, gp_Dir(Vp2))
            aCurve = Geom_Line(gpLin)

            if PlaneOfTheView is None:
                PlaneOfTheView = Geom_Plane(self.activity_plane)
            CS = GeomAPI_IntCS(aCurve, PlaneOfTheView)
            if CS.IsDone():
                point = CS.Point(1)
                return point.X(), point.Y(), point.Z()
            
        except Exception as e:
            logging.error("Error in ConvertPos: " + str(e))
            return 0,0,0

if __name__ == "__main__":
    import sys
    from qtpy import QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    main_widget = qtViewer3d()
    main_widget.show()
    sys.exit(app.exec_())