# This file is part of pyOCCT which provides Python bindings to the OpenCASCADE
# geometry kernel.
#
# Copyright (C) 2016-2018 Laughlin Research, LLC
# Copyright (C) 2019-2020 Trevor Laughlin and pyOCCT contributors
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
from OCCT.Graphic3d import Graphic3d_NOM_ALUMINIUM
from OCCT.STEPControl import STEPControl_Reader

from OCCT.Display._QtViewer import ShapeViewerQt
from OCCT.AIS import AIS_Shape
from OCCT.TopAbs import TopAbs_SOLID

reader = STEPControl_Reader()
reader.ReadFile('./models/compressor.step')
reader.TransferRoots()
shape = reader.OneShape()

v = ShapeViewerQt()
v._the_view.my_context.Activate(AIS_Shape.SelectionMode_(TopAbs_SOLID), True)
v.display_shape(shape, rgb=(0.5, 0.5, 0.5), material=Graphic3d_NOM_ALUMINIUM)
v.start()
