# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 Exporter Framework - LuxRender Plug-in
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# ***** END GPL LICENCE BLOCK *****
#
from math import degrees

def lookAt(scene):
    matrix = scene.camera.matrix
    pos = matrix[3]
    forwards = -matrix[2]
    target = pos + forwards
    up = matrix[1]
    return (pos[0], pos[1], pos[2], target[0], target[1], target[2], up[0], up[1], up[2])
    
def resolution(scene):
    xr = scene.render.resolution_x * scene.render.resolution_percentage / 100.0
    yr = scene.render.resolution_y * scene.render.resolution_percentage / 100.0
    
    return xr, yr

def camera(scene):
    xr, yr = resolution(scene)
    
    # TODO:
    shiftX = 0.0
    shiftY = 0.0
    scale = 1.0
    
    aspect = xr/yr
    invaspect = 1.0/aspect
    
    if aspect > 1.0:
        sw = [
            ((2*shiftX)-1) * scale,
            ((2*shiftX)+1) * scale,
            ((2*shiftY)-invaspect) * scale,
            ((2*shiftY)+invaspect) * scale
        ]
    else:
        sw = [
            ((2*shiftX)-aspect) * scale,
            ((2*shiftX)+aspect) * scale,
            ((2*shiftY)-1) * scale,
            ((2*shiftY)+1) * scale
        ]
    
    fov = degrees(scene.camera.data.angle)
    
    cs = {
        'fov': fov,
        'screenwindow': sw
    }
    
    return ('perspective',  list(cs.items()))

def film(scene):
    xr, yr = resolution(scene)
    
    fs = {
        # Set resolution
        'xresolution':   int(xr),
        'yresolution':   int(yr),
        
        # write only default png file
        'filename':          'default-%05i' % scene.frame_current,
        'write_exr':         False,
        'write_png':         True,
        'write_tga':         False,
        'write_resume_flm':  False,
        'displayinterval':   5,
        'writeinterval':     8,
    }
    
    if scene.luxrender_sampler.haltspp > 0:
        fs['haltspp'] = scene.luxrender_sampler.haltspp
    
    return ('fleximage', list(fs.items()))
