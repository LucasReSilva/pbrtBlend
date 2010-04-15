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
import math

import bpy

from luxrender.properties import dbo
from luxrender.export.camerafilm import resolution

# TODO: adapt values written to d based on simple/advanced views

# TODO: check parameter completeness against Lux API

class luxrender_camera(bpy.types.IDPropertyGroup):
    '''
    Storage class for LuxRender Camera settings.
    This class will be instantiated within a Blender camera
    object.
    '''
    
    def screenwindow(self, xr, yr, cam):
        '''
        xr            float
        yr            float
        cam           bpy.types.camera
        
        Calculate LuxRender camera's screenwindow parameter
        
        Returns list[4]
        '''
        
        shiftX = cam.shift_x
        shiftY = cam.shift_x
        
        # TODO:
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
                
        return sw
    
    def api_output(self, scene):
        '''
        scene            bpy.types.scene
        
        Format this class's members into a LuxRender ParamSet
        
        Returns dict
        '''
        
        cam = scene.camera.data
        xr, yr = resolution(scene)
        
        d = {
            'fov':              math.degrees(scene.camera.data.angle),
            'screenwindow':     self.screenwindow(xr, yr, cam),
            'autofocus':        False,
            'shutteropen':      0.0,
            'shutterclose':     self.exposure
        }
        
        if self.use_dof:
            d['lensradius'] = (cam.lens / 1000.0) / ( 2.0 * self.fstop )
        
        if self.autofocus:
            d['autofocus'] = True
        else:
            if cam.dof_object is not None:
                d['focaldistance'] = (scene.camera.location - cam.dof_object.location).length
            elif cam.dof_distance > 0:
                d['focaldistance'] = cam.dof_distance
            
        if self.use_clipping:
            d['hither'] = cam.clip_start,
            d['yon']    = cam.clip_end,
        
        out = self.type, list(d.items())
        dbo('CAMERA', out)
        return out

class luxrender_tonemapping(bpy.types.IDPropertyGroup):
    '''
    Storage class for LuxRender ToneMapping settings.
    This class will be instantiated within a Blender scene
    object.
    '''
    
    def api_output(self, scene):
        '''
        scene            bpy.types.scene
        
        Format this class's members into a LuxRender ParamSet
        
        Returns dict
        '''
        
        cam = scene.camera.data
        
        d = {}
        
        d['tonemapkernel']              = self.type
        
        if self.type == 'reinhard':
            d['reinhard_prescale']      = self.reinhard_prescale
            d['reinhard_postscale']     = self.reinhard_postscale
            d['reinhard_burn']          = self.reinhard_burn
            
        if self.type == 'linear':
            d['linear_sensitivity']     = cam.luxrender_camera.sensitivity
            d['linear_exposure']        = cam.luxrender_camera.exposure
            d['linear_fstop']           = cam.luxrender_camera.fstop
            d['linear_gamma']           = self.linear_gamma
        
        out = self.type, list(d.items())
        dbo('TONEMAPPING', out)
        return out
