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

def lookAt(scene):
    '''
    scene        bpy.types.scene
    
    Derive a list describing 3 points for a LuxRender LookAt statement
    
    Returns tuple(9) (floats)
    '''
    
    matrix = scene.camera.matrix
    pos = matrix[3]
    forwards = -matrix[2]
    target = pos + forwards
    up = matrix[1]
    return (pos[0], pos[1], pos[2], target[0], target[1], target[2], up[0], up[1], up[2])
    
def resolution(scene):
    '''
    scene        bpy.types.scene
    
    Calculate the output render resolution
    
    Returns tuple(2) (floats)
    '''
    
    xr = scene.render.resolution_x * scene.render.resolution_percentage / 100.0
    yr = scene.render.resolution_y * scene.render.resolution_percentage / 100.0
    
    return xr, yr

def film(scene):
    '''
    scene        bpy.types.scene
    
    Calculate type and parameters for LuxRender Film statement
    
    Returns tuple(2) (string, list) 
    '''
    
    xr, yr = resolution(scene)
    
    fs = {
        # Set resolution
        'xresolution':   int(xr),
        'yresolution':   int(yr),
        
        'filename':          'default',
        'write_exr':         False,
        'write_png':         True,
        'write_tga':         False,
        'write_resume_flm':  False,
        
        # TODO: add UI controls for update intervals, and sync with LuxTimerThread.KICK_PERIODs
        'displayinterval':   5,
        'writeinterval':     8,
    }
    
    if scene.luxrender_sampler.haltspp > 0:
        fs['haltspp'] = scene.luxrender_sampler.haltspp
    
    # update the film settings with tonemapper settings
    type, ts = scene.luxrender_tonemapping.api_output()
    fs.update(ts)
    
    return ('fleximage', list(fs.items()))
