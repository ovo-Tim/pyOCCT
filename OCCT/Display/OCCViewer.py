'''
This file was written by pyOCCT2. It is compatible with pythonOCC.
'''

import itertools, sys, os, math

from OCCT.V3d import V3d_View, V3d_Viewer, V3d_TypeOfOrientation
from OCCT.OpenGl import OpenGl_GraphicDriver
from OCCT.Aspect import Aspect_DisplayConnection
from OCCT.AIS import AIS_InteractiveContext

from OCCT.Aspect import Aspect_GFM_VER
import OCCT.AIS
from OCCT.AIS import (
    AIS_Shape,
    AIS_Shaded,
    AIS_TexturedShape,
    AIS_WireFrame,
    AIS_Shape,
)
from OCCT.gp import gp_Dir, gp_Pnt, gp_Pnt2d, gp_Vec
from OCCT.BRepBuilderAPI import (
    BRepBuilderAPI_MakeVertex,
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeEdge2d,
    BRepBuilderAPI_MakeFace,
)
from OCCT.TopAbs import (
    TopAbs_FACE,
    TopAbs_EDGE,
    TopAbs_VERTEX,
    TopAbs_SHELL,
    TopAbs_SOLID,
)
from OCCT.Geom import Geom_Curve, Geom_Surface
from OCCT.Geom2d import Geom2d_Curve
from OCCT.V3d import (
    V3d_ZBUFFER,
    V3d_Zpos,
    V3d_Zneg,
    V3d_Xpos,
    V3d_Xneg,
    V3d_Ypos,
    V3d_Yneg,
    V3d_XposYnegZpos,
)
from OCCT.Quantity import (
    Quantity_Color,
    Quantity_TOC_RGB,
    Quantity_NOC_WHITE,
    Quantity_NOC_BLACK,
    Quantity_NOC_BLUE1,
    Quantity_NOC_CYAN1,
    Quantity_NOC_RED,
    Quantity_NOC_GREEN,
    Quantity_NOC_ORANGE,
    Quantity_NOC_YELLOW,
)
from OCCT.Prs3d import Prs3d_Arrow, Prs3d_Text, Prs3d_TextAspect
from OCCT.Graphic3d import (
    Graphic3d_NOM_NEON_GNC,
    Graphic3d_NOT_ENV_CLOUDS,
    Graphic3d_TextureEnv,
    Graphic3d_Camera,
    Graphic3d_RM_RAYTRACING,
    Graphic3d_RM_RASTERIZATION,
    Graphic3d_StereoMode_QuadBuffer,
    Graphic3d_RenderingParams,
    Graphic3d_MaterialAspect,
    Graphic3d_TOSM_FRAGMENT,
    Graphic3d_Structure,
    Graphic3d_GraduatedTrihedron,
    Graphic3d_NameOfMaterial,
)
from OCCT.Aspect import Aspect_TOTP_RIGHT_LOWER, Aspect_FM_STRETCH, Aspect_FM_NONE

def rgb_color(r, g, b):
    return Quantity_Color(r, g, b, Quantity_TOC_RGB)


def get_color_from_name(color_name):
    """from the string 'WHITE', returns Quantity_Color
    WHITE.
    color_name is the color name, case insensitive.
    """
    enum_name = "Quantity_NOC_%s" % color_name.upper()
    if enum_name in globals():
        color_num = globals()[enum_name]
    elif enum_name + "1" in globals():
        color_num = globals()[enum_name + "1"]
        print("Many colors for color name %s, using first." % color_name)
    else:
        color_num = Quantity_NOC_WHITE
        print("Color name not defined. Use White by default")
    return Quantity_Color(color_num)

class Viewer3d():
    def __init__(self):
        self._parent = None  # the parent opengl GUI container

        self._inited = False
        self._local_context_opened = False

        # Display connection
        self.display_connect = Aspect_DisplayConnection()
        # Graphics driver
        self._graphics_driver = OpenGl_GraphicDriver(self.display_connect)
        # self.Context:OCCT.AIS = self.GetContext()

        # Create viewer and view
        self.Viewer = V3d_Viewer(self._graphics_driver)
        self.View = self.Viewer.CreateView()
        self.Context = AIS_InteractiveContext(self.Viewer)
        
        self.camera = self.View.Camera()
        self.struc_mgr = self.Viewer.StructureManager()

        self.default_drawer = None

        self.selected_shapes = []
        self._select_callbacks = []
        self._overlay_items = []

        self._window_handle = None

        # some thing we'll need later
        self.modes = itertools.cycle(
            # [TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX, TopAbs_SHELL, TopAbs_SOLID]
            [TopAbs_VERTEX, TopAbs_EDGE, TopAbs_FACE, TopAbs_SOLID]
        )
        self.lmodes = [TopAbs_VERTEX, TopAbs_EDGE, TopAbs_FACE]

    def get_parent(self):
        return self._parent

    def register_overlay_item(self, overlay_item):
        self._overlay_items.append(overlay_item)
        self.View.MustBeResized()
        self.View.Redraw()

    def register_select_callback(self, callback):
        """Adds a callback that will be called each time a shape s selected"""
        if not callable(callback):
            raise AssertionError("You must provide a callable to register the callback")
        self._select_callbacks.append(callback)

    def unregister_callback(self, callback):
        """Remove a callback from the callback list"""
        if not callback in self._select_callbacks:
            raise AssertionError("This callback is not registered")
        self._select_callbacks.remove(callback)

    def MoveTo(self, X, Y):
        self.Context.MoveTo(X, Y, self.View, True)

    def FitAll(self):
        self.View.ZFitAll()
        self.View.FitAll()

    def ConnectToWidget(self, hwnd: int):
        if sys.platform.startswith('win'):
            import ctypes
            from OCCT.WNT import WNT_Window

            ctypes.pythonapi.PyCapsule_New.restype = ctypes.py_object
            ctypes.pythonapi.PyCapsule_New.argtypes = [
                ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
            hwnd = ctypes.pythonapi.PyCapsule_New(hwnd, None, None)
            window = WNT_Window(hwnd)
        elif sys.platform.startswith('darwin'):
            from OCCT.Cocoa import Cocoa_Window

            window = Cocoa_Window(hwnd)
        elif sys.platform.startswith('linux'):
            from OCCT.Xw import Xw_Window

            window = Xw_Window(self.display_connect, hwnd)
        else:
            raise NotImplementedError('Support platform not found for visualization.')

        self.wind = window
        self.View.SetWindow(self.wind)

        # Map window
        if not self.wind.IsMapped():
            self.wind.Map()

        # AIS interactive context
        
        self.Context.SetAutomaticHilight(True)

        self.Viewer.SetDefaultLights()
        self.Viewer.SetLightOn()

        self.View.SetBackgroundColor(Quantity_TOC_RGB, 0.5, 0.5, 0.5)
        self.Context.SetDisplayMode(AIS_Shaded, True)

        self.default_drawer = self.Context.DefaultDrawer()
        self.default_drawer.SetFaceBoundaryDraw(True)

        self.View.TriedronDisplay(Aspect_TOTP_RIGHT_LOWER,
                                     Quantity_Color(Quantity_NOC_BLACK),
                                     0.08)
        self.View.SetProj(V3d_TypeOfOrientation.V3d_XposYposZpos)


    def Create(
        self,
        window_handle=None,
        parent=None,
        create_default_lights=True,
        draw_face_boundaries=True,
        phong_shading=True,
        display_glinfo=True,
    ):
        self._window_handle = window_handle
        self._parent = parent

        # if self._window_handle is None:
        #     self.InitOffscreen(640, 480)
        #     self._is_offscreen = True
        # else:
        #     self.Init(self._window_handle)
        #     self._is_offscreen = False

        self.ConnectToWidget(self._window_handle)

        # # display OpenGl Information
        # if display_glinfo:
        #     self.GlInfo()

        if create_default_lights:
            self.Viewer.SetDefaultLights()
            self.Viewer.SetLightOn()

        self.default_drawer = self.Context.DefaultDrawer()

        # draw black contour edges, like other famous CAD packages
        if draw_face_boundaries:
            self.default_drawer.SetFaceBoundaryDraw(True)

        # turn up tessellation defaults, which are too conversative...
        chord_dev = self.default_drawer.MaximalChordialDeviation() / 10.0
        self.default_drawer.SetMaximalChordialDeviation(chord_dev)

        if phong_shading:
            # gouraud shading by default, prefer phong instead
            self.View.SetShadingModel(Graphic3d_TOSM_FRAGMENT)

        # turn self._inited flag to True
        self._inited = True

    def OnResize(self):
        self.View.MustBeResized()

    def ResetView(self):
        self.View.Reset()

    def Repaint(self):
        self.Viewer.Redraw()

    def SetModeWireFrame(self):
        self.View.SetComputedMode(False)
        self.Context.SetDisplayMode(AIS_WireFrame, True)

    def SetModeShaded(self):
        self.View.SetComputedMode(False)
        self.Context.SetDisplayMode(AIS_Shaded, True)

    def SetModeHLR(self):
        self.View.SetComputedMode(True)

    def SetOrthographicProjection(self):
        self.camera.SetProjectionType(Graphic3d_Camera.Projection_Orthographic)

    def SetPerspectiveProjection(self):
        self.camera.SetProjectionType(Graphic3d_Camera.Projection_Perspective)

    def View_Top(self):
        self.View.SetProj(V3d_Zpos)

    def View_Bottom(self):
        self.View.SetProj(V3d_Zneg)

    def View_Left(self):
        self.View.SetProj(V3d_Xneg)

    def View_Right(self):
        self.View.SetProj(V3d_Xpos)

    def View_Front(self):
        self.View.SetProj(V3d_Yneg)

    def View_Rear(self):
        self.View.SetProj(V3d_Ypos)

    def View_Iso(self):
        self.View.SetProj(V3d_XposYnegZpos)

    def EnableTextureEnv(self, name_of_texture=Graphic3d_NOT_ENV_CLOUDS):
        """enable environment mapping. Possible modes are
        Graphic3d_NOT_ENV_CLOUDS
        Graphic3d_NOT_ENV_CV
        Graphic3d_NOT_ENV_MEDIT
        Graphic3d_NOT_ENV_PEARL
        Graphic3d_NOT_ENV_SKY1
        Graphic3d_NOT_ENV_SKY2
        Graphic3d_NOT_ENV_LINES
        Graphic3d_NOT_ENV_ROAD
        Graphic3d_NOT_ENV_UNKNOWN
        """
        texture_env = Graphic3d_TextureEnv(name_of_texture)
        self.View.SetTextureEnv(texture_env)
        self.View.Redraw()

    # def DisableTextureEnv(self):
    #     a_null_texture = Handle_Graphic3d_TextureEnv_Create()
    #     self.View.SetTextureEnv(
    #         a_null_texture
    #     )  # Passing null handle to clear the texture data
    #     self.View.Redraw()

    def SetRenderingParams(
        self,
        Method=Graphic3d_RM_RASTERIZATION,
        RaytracingDepth=3,
        IsShadowEnabled=True,
        IsReflectionEnabled=False,
        IsAntialiasingEnabled=False,
        IsTransparentShadowEnabled=False,
        StereoMode=Graphic3d_StereoMode_QuadBuffer,
        AnaglyphFilter=Graphic3d_RenderingParams.Anaglyph_RedCyan_Optimized,
        ToReverseStereo=False,
    ):
        """Default values are :
        Method=Graphic3d_RM_RASTERIZATION,
        RaytracingDepth=3,
        IsShadowEnabled=True,
        IsReflectionEnabled=False,
        IsAntialiasingEnabled=False,
        IsTransparentShadowEnabled=False,
        StereoMode=Graphic3d_StereoMode_QuadBuffer,
        AnaglyphFilter=Graphic3d_RenderingParams.Anaglyph_RedCyan_Optimized,
        ToReverseStereo=False)
        """
        self.ChangeRenderingParams(
            Method,
            RaytracingDepth,
            IsShadowEnabled,
            IsReflectionEnabled,
            IsAntialiasingEnabled,
            IsTransparentShadowEnabled,
            StereoMode,
            AnaglyphFilter,
            ToReverseStereo,
        )

    def SetRasterizationMode(self):
        """to enable rasterization mode, just call the SetRenderingParams
        with default values
        """
        self.SetRenderingParams()

    def SetRaytracingMode(self, depth=3):
        """enables the raytracing mode"""
        self.SetRenderingParams(
            Method=Graphic3d_RM_RAYTRACING,
            RaytracingDepth=depth,
            IsAntialiasingEnabled=True,
            IsShadowEnabled=True,
            IsReflectionEnabled=True,
            IsTransparentShadowEnabled=True,
        )

    def ExportToImage(self, image_filename):
        self.View.Dump(image_filename)

    def display_graduated_trihedron(self):
        a_trihedron_data = Graphic3d_GraduatedTrihedron()
        self.View.GraduatedTrihedronDisplay(a_trihedron_data)

    def display_triedron(self):
        """Show a black triedron in lower right corner"""
        self.View.TriedronDisplay(
            Aspect_TOTP_RIGHT_LOWER,
            Quantity_Color(Quantity_NOC_BLACK),
            0.1,
            V3d_ZBUFFER,
        )

    def hide_triedron(self):
        """Show a black triedron in lower right corner"""
        self.View.TriedronErase()

    def set_bg_gradient_color(self, color1, color2, fill_method=Aspect_GFM_VER):
        """set a bg vertical gradient color.
        color1 is [R1, G1, B1], each being bytes or an instance of Quantity_Color
        color2 is [R2, G2, B2], each being bytes or an instance of Quantity_Color
        fill_method is one of Aspect_GFM_VER value Aspect_GFM_NONE, Aspect_GFM_HOR,
        Aspect_GFM_VER, Aspect_GFM_DIAG1, Aspect_GFM_DIAG2, Aspect_GFM_CORNER1, Aspect_GFM_CORNER2,
        Aspect_GFM_CORNER3, Aspect_GFM_CORNER4
        """
        if isinstance(color1, list) and isinstance(color2, list):
            R1, G1, B1 = color1
            R2, G2, B2 = color2
            color1 = rgb_color(float(R1) / 255.0, float(G1) / 255.0, float(B1) / 255.0)
            color2 = rgb_color(float(R2) / 255.0, float(G2) / 255.0, float(B2) / 255.0)
        elif not isinstance(color1, Quantity_Color) and isinstance(
            color2, Quantity_Color
        ):
            raise AssertionError(
                "color1 and color2 mmust be either [R, G, B] lists or a Quantity_Color"
            )
        self.View.SetBgGradientColors(color1, color2, fill_method, True)

    def SetBackgroundImage(self, image_filename, stretch=True):
        """displays a background image (jpg, png etc.)"""
        if not os.path.isfile(image_filename):
            raise IOError("image file %s not found." % image_filename)
        if stretch:
            self.View.SetBackgroundImage(image_filename, Aspect_FM_STRETCH, True)
        else:
            self.View.SetBackgroundImage(image_filename, Aspect_FM_NONE, True)

    def DisplayVector(self, vec, pnt, update=False):
        """displays a vector as an arrow"""
        if self._inited:
            aStructure = Graphic3d_Structure(self.struc_mgr)

            pnt_as_vec = gp_Vec(pnt.X(), pnt.Y(), pnt.Z())
            start = pnt_as_vec + vec
            pnt_start = gp_Pnt(start.X(), start.Y(), start.Z())

            Prs3d_Arrow.Draw(
                aStructure.CurrentGroup(),
                pnt_start,
                gp_Dir(vec),
                math.radians(20),
                vec.Magnitude(),
            )
            aStructure.Display()
            # it would be more coherent if a AIS_InteractiveObject
            # would be returned
            if update:
                self.Repaint()
            return aStructure

    def DisplayMessage(
        self,
        point,
        text_to_write,
        height=14.0,
        message_color=(0.0, 0.0, 0.0),
        update=False,
    ):
        """
        :point: a gp_Pnt or gp_Pnt2d instance
        :text_to_write: a string
        :height: font height, 12 by defaults
        :message_color: triple with the range 0-1, default to black
        """
        aStructure = Graphic3d_Structure(self.struc_mgr)

        text_aspect = Prs3d_TextAspect()
        text_aspect.SetColor(rgb_color(*message_color))
        text_aspect.SetHeight(height)
        if isinstance(point, gp_Pnt2d):
            point = gp_Pnt(point.X(), point.Y(), 0)

        Prs3d_Text.Draw(aStructure.CurrentGroup(), text_aspect, text_to_write, point)
        aStructure.Display()
        # @TODO: it would be more coherent if a AIS_InteractiveObject
        # is be returned
        if update:
            self.Repaint()
        return aStructure

    def DisplayShape(
        self,
        shapes,
        material=None,
        texture=None,
        color=None,
        transparency=None,
        update=False,
    ):
        """display one or a set of displayable objects"""
        ais_shapes = []  # the list of all displayed shapes

        if issubclass(shapes.__class__, gp_Pnt):
            # if a gp_Pnt is passed, first convert to vertex
            vertex = BRepBuilderAPI_MakeVertex(shapes)
            shapes = [vertex.Shape()]
        elif isinstance(shapes, gp_Pnt2d):
            vertex = BRepBuilderAPI_MakeVertex(gp_Pnt(shapes.X(), shapes.Y(), 0))
            shapes = [vertex.Shape()]
        elif isinstance(shapes, Geom_Surface):
            bounds = True
            toldegen = 1e-6
            face = BRepBuilderAPI_MakeFace()
            face.Init(shapes, bounds, toldegen)
            face.Build()
            shapes = [face.Shape()]
        elif isinstance(shapes, Geom_Curve):
            edge = BRepBuilderAPI_MakeEdge(shapes)
            shapes = [edge.Shape()]
        elif isinstance(shapes, Geom2d_Curve):
            edge2d = BRepBuilderAPI_MakeEdge2d(shapes)
            shapes = [edge2d.Shape()]

        # if only one shapes, create a list with a single shape
        if not isinstance(shapes, list):
            shapes = [shapes]
        # build AIS_Shapes list
        for shape in shapes:
            if material and texture or not material and texture:
                shape_to_display = AIS_TexturedShape(shape)
                (
                    filename,
                    toScaleU,
                    toScaleV,
                    toRepeatU,
                    toRepeatV,
                    originU,
                    originV,
                ) = texture.GetProperties()
                shape_to_display.SetTextureFileName(filename)
                shape_to_display.SetTextureMapOn()
                shape_to_display.SetTextureScale(True, toScaleU, toScaleV)
                shape_to_display.SetTextureRepeat(True, toRepeatU, toRepeatV)
                shape_to_display.SetTextureOrigin(True, originU, originV)
                shape_to_display.SetDisplayMode(3)
            elif material:
                shape_to_display = AIS_Shape(shape)
                if isinstance(material, Graphic3d_NameOfMaterial):
                    shape_to_display.SetMaterial(Graphic3d_MaterialAspect(material))
                else:
                    shape_to_display.SetMaterial(material)
            else:
                # TODO: can we use .Set to attach all TopoDS_Shapes
                # to this AIS_Shape instance?
                if not isinstance(shape, AIS_Shape):
                    shape_to_display = AIS_Shape(shape)
                else:
                    shape_to_display = shape

            ais_shapes.append(shape_to_display)

        # if not SOLO:
        #     # computing graphic properties is expensive
        #     # if an iterable is found, so cluster all TopoDS_Shape under
        #     # an AIS_MultipleConnectedInteractive
        #     #shape_to_display = AIS_MultipleConnectedInteractive()
        #     for ais_shp in ais_shapes:
        #         # TODO : following line crashes with oce-0.18
        #         # why ? fix ?
        #         #shape_to_display.Connect(i)
        #         self.Context.Display(ais_shp, False)
        # set the graphic properties
        if material is None:
            # The default material is too shiny to show the object
            # color well, so I set it to something less reflective
            for shape_to_display in ais_shapes:
                shape_to_display.SetMaterial(
                    Graphic3d_MaterialAspect(Graphic3d_NOM_NEON_GNC)
                )
        if color:
            if isinstance(color, str):
                color = get_color_from_name(color)
            elif isinstance(color, int):
                color = Quantity_Color(color)
            for shp in ais_shapes:
                self.Context.SetColor(shp, color, False)
        if transparency:
            for shape_to_display in ais_shapes:
                shape_to_display.SetTransparency(transparency)
        # display the shapes
        for shape_to_display in ais_shapes:
            self.Context.Display(shape_to_display, False)
        if update:
            # especially this call takes up a lot of time...
            self.FitAll()
            self.Repaint()
        
        return ais_shapes

    def DisplayColoredShape(
        self,
        shapes,
        color="YELLOW",
        update=False,
    ):
        if isinstance(color, str):
            dict_color = {
                "WHITE": Quantity_NOC_WHITE,
                "BLUE": Quantity_NOC_BLUE1,
                "RED": Quantity_NOC_RED,
                "GREEN": Quantity_NOC_GREEN,
                "YELLOW": Quantity_NOC_YELLOW,
                "CYAN": Quantity_NOC_CYAN1,
                "BLACK": Quantity_NOC_BLACK,
                "ORANGE": Quantity_NOC_ORANGE,
            }
            clr = dict_color[color]
        elif isinstance(color, Quantity_Color):
            clr = color
        else:
            raise ValueError(
                'color should either be a string ( "BLUE" ) or a Quantity_Color(0.1, 0.8, 0.1) got %s'
                % color
            )

        return self.DisplayShape(shapes, color=clr, update=update)

    def EnableAntiAliasing(self):
        self.SetNbMsaaSample(4)

    def DisableAntiAliasing(self):
        self.SetNbMsaaSample(0)

    def EraseAll(self):
        self.Context.EraseAll(True)

    def Tumble(self, num_images, animation=True):
        self.View.Tumble(num_images, animation)

    def Pan(self, dx, dy):
        self.View.Pan(dx, dy)

    def SetSelectionMode(self, mode=None):
        self.Context.Deactivate()
        topo_level = next(self.modes)
        if mode is None:
            self.Context.Activate(AIS_Shape.SelectionMode(topo_level), True)
        else:
            self.Context.Activate(AIS_Shape.SelectionMode(mode), True)
        self.Context.UpdateSelected(True)

    def SetSelectionModeVertex(self):
        self.SetSelectionMode(TopAbs_VERTEX)

    def SetSelectionModeEdge(self):
        self.SetSelectionMode(TopAbs_EDGE)

    def SetSelectionModeFace(self):
        self.SetSelectionMode(TopAbs_FACE)

    def SetSelectionModeShape(self):
        self.Context.Deactivate()

    def SetSelectionModeNeutral(self):
        self.Context.Deactivate()

    def GetSelectedShapes(self):
        return self.selected_shapes

    def GetSelectedShape(self):
        return self.Context.SelectedShape()

    def SelectArea(self, Xmin, Ymin, Xmax, Ymax):
        self.Context.Select(Xmin, Ymin, Xmax, Ymax, self.View, True)
        self.Context.InitSelected()
        # reinit the selected_shapes list
        self.selected_shapes = []
        while self.Context.MoreSelected():
            if self.Context.HasSelectedShape():
                self.selected_shapes.append(self.Context.SelectedShape())
            self.Context.NextSelected()
        # callbacks
        for callback in self._select_callbacks:
            callback(self.selected_shapes, Xmin, Ymin, Xmax, Ymax)

    def Select(self, X, Y):
        self.Context.Select(True)
        self.Context.InitSelected()

        self.selected_shapes = []
        if self.Context.MoreSelected():
            if self.Context.HasSelectedShape():
                self.selected_shapes.append(self.Context.SelectedShape())
        # callbacks
        for callback in self._select_callbacks:
            callback(self.selected_shapes, X, Y)

    def ShiftSelect(self, X, Y):
        self.Context.ShiftSelect(True)
        self.Context.InitSelected()

        self.selected_shapes = []
        while self.Context.MoreSelected():
            if self.Context.HasSelectedShape():
                self.selected_shapes.append(self.Context.SelectedShape())
            self.Context.NextSelected()
        # highlight newly selected unhighlight those no longer selected
        self.Context.UpdateSelected(True)
        # callbacks
        for callback in self._select_callbacks:
            callback(self.selected_shapes, X, Y)

    def Rotation(self, X, Y):
        self.View.Rotation(X, Y)

    def DynamicZoom(self, X1, Y1, X2, Y2):
        self.View.Zoom(X1, Y1, X2, Y2)

    def ZoomFactor(self, zoom_factor):
        self.View.SetZoom(zoom_factor)

    def ZoomArea(self, X1, Y1, X2, Y2):
        self.View.WindowFit(X1, Y1, X2, Y2)

    def Zoom(self, X, Y):
        self.View.Zoom(X, Y)

    def StartRotation(self, X, Y):
        self.View.StartRotation(X, Y)