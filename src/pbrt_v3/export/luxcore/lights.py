# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 PBRTv3 Add-On
# --------------------------------------------------------------------------
#
# Authors:
# David Bucciarelli, Jens Verwiebe, Tom Bech, Simon Wendsche
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

import bpy, mathutils, math, os

from ...outputs.pbrtv3core_api import pypbrtv3core
from ...outputs.pbrtv3core_api import ToValidPBRTv3CoreName
from ...export import is_obj_visible
from ...export import get_worldscale
from ...export import matrix_to_list
from ...export import get_expanded_file_name

from .utils import is_lightgroup_opencl_compatible, convert_texture_channel, log_exception


class ExportedLight(object):
    def __init__(self, name, type):
        self.pbrtv3core_name = name
        self.type = type

    def __eq__(self, other):
        return self.pbrtv3core_name == other.pbrtv3core_name and self.type == other.type

    def __hash__(self):
        return hash(self.pbrtv3core_name) ^ hash(self.type)


class LightExporter(object):
    def __init__(self, pbrtv3core_exporter, blender_scene, blender_object, dupli_name_suffix=''):
        self.pbrtv3core_exporter = pbrtv3core_exporter
        self.blender_scene = blender_scene
        self.blender_object = blender_object
        self.dupli_name_suffix = dupli_name_suffix
        self.is_dupli = len(dupli_name_suffix) > 0

        self.properties = pypbrtv3core.Properties()
        self.pbrtv3core_name = ''
        self.exported_lights = set()


    def convert(self, pbrtv3core_scene, matrix=None):
        # Remove old properties
        self.properties = pypbrtv3core.Properties()

        old_exported_lights = self.exported_lights.copy()
        self.exported_lights = set()

        self.__convert_light(pbrtv3core_scene, matrix)

        # Remove old lights
        diff = old_exported_lights - self.exported_lights
        for exported_light in diff:
            if exported_light.type == 'AREA':
                # Area lights are meshlights and treated like objects
                pbrtv3core_scene.DeleteObject(exported_light.pbrtv3core_name)
            else:
                pbrtv3core_scene.DeleteLight(exported_light.pbrtv3core_name)

        return self.properties


    def __generate_light_name(self, name):
        if self.blender_object.library:
            name += '_' + self.blender_object.library.name

        if self.is_dupli:
            name += self.dupli_name_suffix

        self.pbrtv3core_name = ToValidPBRTv3CoreName(name)


    def __multiply_gain(self, main_gain, gain_r, gain_g, gain_b):
        return [main_gain * gain_r, main_gain * gain_g, main_gain * gain_b]


    def __convert_light(self, pbrtv3core_scene, matrix):
        # TODO: refactor this horrible... thing (although it's a bit better now)

        obj = self.blender_object
        self.__generate_light_name(obj.name)
        pbrtv3core_name = self.pbrtv3core_name
        light = obj.data
        energy = light.energy
        pbrtv3_lamp = getattr(light.pbrtv3_lamp, 'pbrtv3_lamp_%s' % light.type.lower())

        if not is_obj_visible(self.blender_scene, obj, self.is_dupli, self.pbrtv3core_exporter.is_viewport_render):
            return

        if matrix is None:
            matrix = obj.matrix_world

        # Get lightgroup ID
        lightgroup = light.pbrtv3_lamp.lightgroup
        lightgroup_id =  self.pbrtv3core_exporter.lightgroup_cache.get_id(lightgroup, self.blender_scene, self)

        # Don't set lightgroup for sun because it might be split into sun + sky (and not for AREA because it needs a helper mat)
        if lightgroup_id != -1 and light.type != 'SUN' and not (
                        light.type == 'AREA' and not light.pbrtv3_lamp.pbrtv3_lamp_laser.is_laser) and not (
                        self.blender_scene.pbrtv3_lightgroups.ignore) and (
                        is_lightgroup_opencl_compatible(self.pbrtv3core_exporter, lightgroup_id)):
            self.properties.Set(pypbrtv3core.Property('scene.lights.' + self.pbrtv3core_name + '.id', [lightgroup_id]))

        # Visibility settings for indirect rays (not for sun because it might be split into sun + sky,
        # and not for area light because it needs a different prefix (scene.materials.)
        if light.type != 'SUN' and not (light.type == 'AREA' and not light.pbrtv3_lamp.pbrtv3_lamp_laser.is_laser):
            self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.visibility.indirect.diffuse.enable',
                                                 light.pbrtv3_lamp.pbrtv3core_lamp.visibility_indirect_diffuse_enable))
            self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.visibility.indirect.glossy.enable',
                                                 light.pbrtv3_lamp.pbrtv3core_lamp.visibility_indirect_glossy_enable))
            self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.visibility.indirect.specular.enable',
                                                 light.pbrtv3_lamp.pbrtv3core_lamp.visibility_indirect_specular_enable))

        gain_r = light.pbrtv3_lamp.pbrtv3core_lamp.gain_r
        gain_g = light.pbrtv3_lamp.pbrtv3core_lamp.gain_g
        gain_b = light.pbrtv3_lamp.pbrtv3core_lamp.gain_b
        gain_spectrum = self.__multiply_gain(energy, gain_r, gain_g, gain_b)  # pbrtv3core gain is rgb

        # not for distant light,
        # not for area lamps (because these are meshlights and gain is controlled by material settings)
        if pbrtv3_lamp.L_color and not (
                        light.type == 'SUN' and pbrtv3_lamp.sunsky_type != 'distant') and not (
                        light.type == 'AREA' and not light.pbrtv3_lamp.pbrtv3_lamp_laser.is_laser):
            iesfile = light.pbrtv3_lamp.iesname
            iesfile, basename = get_expanded_file_name(light, iesfile)
            if os.path.exists(iesfile):
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.iesfile', iesfile))

            # Workaround for lights without color, multiply gain with color here
            if (light.type == 'HEMI' and (not pbrtv3_lamp.infinite_map or pbrtv3_lamp.hdri_multiply)) or light.type == 'SPOT':
                colorRaw = pbrtv3_lamp.L_color * energy
                gain_spectrum = self.__multiply_gain(energy, colorRaw[0], colorRaw[1], colorRaw[2])
            else:
                colorRaw = pbrtv3_lamp.L_color
                color = [colorRaw[0], colorRaw[1], colorRaw[2]]
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.color', color))

            self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.gain', gain_spectrum))

        samples = light.pbrtv3_lamp.pbrtv3core_lamp.samples
        if light.type != 'SUN' and not (light.type == 'AREA' and not light.pbrtv3_lamp.pbrtv3_lamp_laser.is_laser):
            self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.samples', [samples]))

        ####################################################################
        # Sun (includes sun, sky, distant)
        ####################################################################
        if light.type == 'SUN':
            invmatrix = matrix.inverted()
            sundir = [invmatrix[2][0], invmatrix[2][1], invmatrix[2][2]]

            sunsky_type = light.pbrtv3_lamp.pbrtv3_lamp_sun.sunsky_type
            legacy_sky = light.pbrtv3_lamp.pbrtv3_lamp_sun.legacy_sky

            if 'sun' in sunsky_type:
                name = pbrtv3core_name + '_sun'
                self.exported_lights.add(ExportedLight(name, 'SUN'))

                if not self.blender_scene.pbrtv3_lightgroups.ignore and is_lightgroup_opencl_compatible(self.pbrtv3core_exporter, lightgroup_id):
                    self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.id', [lightgroup_id]))

                turbidity = pbrtv3_lamp.turbidity

                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.type', ['sun']))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.turbidity', [turbidity]))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.dir', sundir))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.gain', gain_spectrum))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.samples', [samples]))

                relsize = pbrtv3_lamp.relsize
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.relsize', [relsize]))

                # Settings for indirect light visibility
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.visibility.indirect.diffuse.enable',
                                                     light.pbrtv3_lamp.pbrtv3core_lamp.visibility_indirect_diffuse_enable))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.visibility.indirect.glossy.enable',
                                                     light.pbrtv3_lamp.pbrtv3core_lamp.visibility_indirect_glossy_enable))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.visibility.indirect.specular.enable',
                                                     light.pbrtv3_lamp.pbrtv3core_lamp.visibility_indirect_specular_enable))

            if 'sky' in sunsky_type:
                name = pbrtv3core_name + '_sky'
                self.exported_lights.add(ExportedLight(name, 'SKY'))

                if not self.blender_scene.pbrtv3_lightgroups.ignore and is_lightgroup_opencl_compatible(self.pbrtv3core_exporter, lightgroup_id):
                    self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.id', [lightgroup_id]))

                turbidity = pbrtv3_lamp.turbidity
                groundcolor = list(pbrtv3_lamp.groundcolor)
                groundalbedo = groundcolor if pbrtv3_lamp.link_albedo_groundcolor else list(pbrtv3_lamp.groundalbedo)
                skyVersion = 'sky' if legacy_sky else 'sky2'

                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.type', [skyVersion]))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.turbidity', [turbidity]))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.groundalbedo', groundalbedo))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.dir', sundir))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.gain', gain_spectrum))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.samples', [samples]))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.ground.enable', pbrtv3_lamp.use_groundcolor))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.ground.color', groundcolor))

                # Settings for indirect light visibility
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.visibility.indirect.diffuse.enable',
                                                     light.pbrtv3_lamp.pbrtv3core_lamp.visibility_indirect_diffuse_enable))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.visibility.indirect.glossy.enable',
                                                     light.pbrtv3_lamp.pbrtv3core_lamp.visibility_indirect_glossy_enable))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + name + '.visibility.indirect.specular.enable',
                                                     light.pbrtv3_lamp.pbrtv3core_lamp.visibility_indirect_specular_enable))

            if sunsky_type == 'distant':
                self.exported_lights.add(ExportedLight(pbrtv3core_name, 'DISTANT'))

                if not self.blender_scene.pbrtv3_lightgroups.ignore and is_lightgroup_opencl_compatible(self.pbrtv3core_exporter, lightgroup_id):
                    self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.id', [lightgroup_id]))

                distant_dir = [-sundir[0], -sundir[1], -sundir[2]]

                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.type', ['distant']))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.direction', distant_dir))

                theta = math.degrees(pbrtv3_lamp.theta)
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.theta', [theta]))

                # Settings for indirect light visibility
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.visibility.indirect.diffuse.enable',
                                                     light.pbrtv3_lamp.pbrtv3core_lamp.visibility_indirect_diffuse_enable))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.visibility.indirect.glossy.enable',
                                                     light.pbrtv3_lamp.pbrtv3core_lamp.visibility_indirect_glossy_enable))
                self.properties.Set(
                    pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.visibility.indirect.specular.enable',
                                       light.pbrtv3_lamp.pbrtv3core_lamp.visibility_indirect_specular_enable))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.samples', [samples]))

        ####################################################################
        # Hemi (infinite)
        ####################################################################
        elif light.type == 'HEMI':
            self.exported_lights.add(ExportedLight(pbrtv3core_name, 'HEMI'))

            if pbrtv3_lamp.infinite_map:
                infinite_map_path_abs, basename = get_expanded_file_name(light, pbrtv3_lamp.infinite_map)
                upper_hemi = pbrtv3_lamp.sampleupperhemisphereonly

                if os.path.exists(infinite_map_path_abs):
                    self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.type', 'infinite'))
                    self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.file', infinite_map_path_abs))
                    self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.gamma', pbrtv3_lamp.gamma))
                    self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.sampleupperhemisphereonly', upper_hemi))

                else:
                    message = 'Imagemap "%s" of hemilight "%s" not found at path "%s"' % (basename, light.name, infinite_map_path_abs)
                    log_exception(self.pbrtv3core_exporter, message)
                    # Warning color
                    self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.type', 'constantinfinite'))
                    self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.color', [1, 0, 1]))
            else:
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.type', 'constantinfinite'))

            hemi_fix = mathutils.Matrix.Scale(1.0, 4)  # create new scale matrix 4x4
            hemi_fix[0][0] = -1.0  # mirror the hdri_map
            transform = matrix_to_list(hemi_fix * matrix.inverted(), apply_worldscale=True)
            self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.transformation', transform))

        ####################################################################
        # Point
        ####################################################################
        elif light.type == 'POINT':
            self.exported_lights.add(ExportedLight(pbrtv3core_name, 'POINT'))

            mapfile, basename = get_expanded_file_name(light, pbrtv3_lamp.mapname)
            valid_mapfile = pbrtv3_lamp.projector and os.path.exists(mapfile)

            if valid_mapfile or os.path.exists(iesfile):
                # Note: we need mappoint type for ies support, but the ies file is defined at the beginning of this file
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.type', 'mappoint'))

                if valid_mapfile:
                    mapfile, basename = get_expanded_file_name(light, pbrtv3_lamp.mapname)
                    self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.mapfile', mapfile))
            else:
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.type', 'point'))

            if pbrtv3_lamp.flipz:
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.flipz', pbrtv3_lamp.flipz))

            transform = matrix_to_list(matrix, apply_worldscale=True)
            self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.transformation', transform))
            self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.position', [0.0, 0.0, 0.0]))
            self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.power', pbrtv3_lamp.power))
            self.properties.Set(
                pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.efficency', pbrtv3_lamp.efficacy))

        ####################################################################
        # Spot (includes projector)
        ####################################################################
        elif light.type == 'SPOT':
            coneangle = math.degrees(light.spot_size) * 0.5
            conedeltaangle = math.degrees(light.spot_size * 0.5 * light.spot_blend)
            gamma = pbrtv3_lamp.gamma

            if pbrtv3_lamp.projector:
                self.exported_lights.add(ExportedLight(pbrtv3core_name, 'PROJECTION'))

                projector_map_path_abs, basename = get_expanded_file_name(light, pbrtv3_lamp.mapname)
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.type', 'projection'))
                self.properties.Set(
                    pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.mapfile', projector_map_path_abs))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.gamma', gamma))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.fov', coneangle * 2))
            else:
                self.exported_lights.add(ExportedLight(pbrtv3core_name, 'SPOT'))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.type', 'spot'))

            spot_fix = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'Z')  # match to pbrtv3
            transform = matrix_to_list(matrix * spot_fix, apply_worldscale=True)
            self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.transformation', transform))
            self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.position', [0.0, 0.0, 0.0]))
            self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.target', [0.0, 0.0, -1.0]))

            self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.coneangle', coneangle))
            self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.conedeltaangle', conedeltaangle))
            self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.power', pbrtv3_lamp.power))
            self.properties.Set(
                pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.efficency', pbrtv3_lamp.efficacy))

        ####################################################################
        # Area (includes laser)
        ####################################################################
        elif light.type == 'AREA':
            if light.pbrtv3_lamp.pbrtv3_lamp_laser.is_laser:
                self.exported_lights.add(ExportedLight(pbrtv3core_name, 'LASER'))
                # Laser lamp
                transform = matrix_to_list(matrix, apply_worldscale=True)
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.transformation', transform))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.position', [0.0, 0.0, 0.0]))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.type', 'laser'))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.target', [0.0, 0.0, -1.0]))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.radius', [light.size]))
                self.properties.Set(pypbrtv3core.Property('scene.lights.' + pbrtv3core_name + '.samples', [samples]))
            else:
                self.exported_lights.add(ExportedLight(pbrtv3core_name, 'AREA'))
                area = light.pbrtv3_lamp.pbrtv3_lamp_area
    
                # Area lamp workaround: create plane and add emitting material
                mat_name = pbrtv3core_name + '_helper_mat'
                # TODO: match brightness with API 1.x

                # Visibility for indirect rays
                self.properties.Set(pypbrtv3core.Property('scene.materials.' + mat_name + '.visibility.indirect.diffuse.enable',
                                                 light.pbrtv3_lamp.pbrtv3core_lamp.visibility_indirect_diffuse_enable))
                self.properties.Set(pypbrtv3core.Property('scene.materials.' + mat_name + '.visibility.indirect.glossy.enable',
                                                     light.pbrtv3_lamp.pbrtv3core_lamp.visibility_indirect_glossy_enable))
                self.properties.Set(pypbrtv3core.Property('scene.materials.' + mat_name + '.visibility.indirect.specular.enable',
                                                 light.pbrtv3_lamp.pbrtv3core_lamp.visibility_indirect_specular_enable))

                emission_color = list(area.L_color)
                # overwrite gain with a gain scaled by ws^2 to account for change in lamp area
                area_gain = energy * (get_worldscale(as_scalematrix=False) ** 2)
                area_gain = self.__multiply_gain(area_gain, gain_r, gain_g, gain_b)
    
                self.properties.Set(pypbrtv3core.Property('scene.materials.' + mat_name + '.type', ['matte']))
                self.properties.Set(pypbrtv3core.Property('scene.materials.' + mat_name + '.kd', [0.0, 0.0, 0.0]))

                self.properties.Set(pypbrtv3core.Property('scene.materials.' + mat_name + '.emission', emission_color))
                self.properties.Set(pypbrtv3core.Property('scene.materials.' + mat_name + '.emission.gain', area_gain))
                self.properties.Set(pypbrtv3core.Property('scene.materials.' + mat_name + '.emission.power', area.power))
                self.properties.Set(pypbrtv3core.Property('scene.materials.' + mat_name + '.emission.efficency', area.efficacy))
                self.properties.Set(pypbrtv3core.Property('scene.materials.' + mat_name + '.emission.samples', samples))
                self.properties.Set(pypbrtv3core.Property('scene.materials.' + mat_name + '.emission.theta', math.degrees(area.theta)))

                if not self.blender_scene.pbrtv3_lightgroups.ignore and is_lightgroup_opencl_compatible(self.pbrtv3core_exporter, lightgroup_id):
                    self.properties.Set(pypbrtv3core.Property('scene.materials.' + mat_name + '.emission.id', [lightgroup_id]))

                # Ies
                iesfile = light.pbrtv3_lamp.iesname
                iesfile, basename = get_expanded_file_name(light.pbrtv3_lamp, iesfile)
                if os.path.exists(iesfile):
                    self.properties.Set(pypbrtv3core.Property('scene.materials.' + mat_name + '.emission.iesfile', iesfile))

                # Opacity
                opacity = convert_texture_channel(self.pbrtv3core_exporter, self.properties, mat_name, area, 'opacity', 'float')

                if not (type(opacity) is list and opacity[0] == 1):
                    # Don't export the property when not necessary (opacity 1 means that the light is fully visible)
                    self.properties.Set(pypbrtv3core.Property('scene.materials.' + mat_name + '.transparency', opacity))
    
                # assign material to object
                self.properties.Set(pypbrtv3core.Property('scene.objects.' + pbrtv3core_name + '.material', [mat_name]))

                # copy transformation of area lamp object
                transform_matrix = obj.matrix_world.copy()
                scale_x = mathutils.Matrix.Scale(light.size / 2, 4, (1, 0, 0))
                if light.shape == 'RECTANGLE':
                    scale_y = mathutils.Matrix.Scale(light.size_y / 2, 4, (0, 1, 0))
                else:
                    # basically scale_x, but for the y axis (note the last tuple argument)
                    scale_y = mathutils.Matrix.Scale(light.size / 2, 4, (0, 1, 0))

                transform_matrix *= scale_x
                transform_matrix *= scale_y

                transform = matrix_to_list(transform_matrix, apply_worldscale=True)
                # Only use mesh transform for final renders (disables instancing which is needed for viewport render
                # so we can move the light object)
                mesh_transform = None if self.pbrtv3core_exporter.is_viewport_render else transform

                # add mesh
                mesh_name = 'Mesh-' + pbrtv3core_name
                if not pbrtv3core_scene.IsMeshDefined(mesh_name):
                    vertices = [
                        (1, 1, 0),
                        (1, -1, 0),
                        (-1, -1, 0),
                        (-1, 1, 0)
                    ]
                    faces = [
                        (0, 1, 2),
                        (2, 3, 0)
                    ]
                    pbrtv3core_scene.DefineMesh(mesh_name, vertices, faces, None, None, None, None, mesh_transform)
                # assign mesh to object
                self.properties.Set(pypbrtv3core.Property('scene.objects.' + pbrtv3core_name + '.ply', mesh_name))
                # Use instancing in viewport so we can move the light
                if self.pbrtv3core_exporter.is_viewport_render:
                    self.properties.Set(pypbrtv3core.Property('scene.objects.' + pbrtv3core_name + '.transformation', transform))
    
        else:
            raise Exception('Unknown lighttype ' + light.type + ' for light: ' + obj.name)