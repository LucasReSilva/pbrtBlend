# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
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

import bpy

from ...outputs.luxcore_api import pyluxcore
from pyluxcore import Property
from ...outputs.luxcore_api import ToValidLuxCoreName
from ...export.materials import get_texture_from_scene
from ...export import get_expanded_file_name
from ...properties import find_node

from .utils import convert_texture_channel, get_elem_key, is_lightgroup_opencl_compatible
from .textures import TextureExporter


DEFAULT_MATTE = 'DEFAULT_MATTE'
DEFAULT_NULL = 'DEFAULT_NULL'


class MaterialExporter(object):
    def __init__(self, luxcore_exporter, blender_scene, material):
        self.luxcore_exporter = luxcore_exporter
        self.blender_scene = blender_scene
        self.material = material

        self.properties = pyluxcore.Properties()
        self.luxcore_name = ''


    def convert(self):
        # Remove old properties
        self.properties = pyluxcore.Properties()

        if self.material is None:
            self.__convert_default_matte()
        elif self.material.luxrender_material.nodetree:
            self.__convert_node_material()
        else:
            self.__convert_material()

        return self.properties


    def __convert_node_material(self):
        # Clay render handling
        if self.blender_scene.luxcore_translatorsettings.override_materials:
            self.__convert_default_matte()
            return

        self.__generate_material_name(self.material.name)

        output_node = find_node(self.material, 'luxrender_material_output_node')

        if output_node is None:
            self.__convert_default_matte()

        try:
            output_node.export_luxcore(self.material, self.properties, self.blender_scene, self.luxcore_exporter, self.luxcore_name)

            prefix = 'scene.materials.' + self.luxcore_name
            self.__set_material_volumes(prefix, output_node.interior_volume, output_node.exterior_volume)

            # LuxCore specific material settings
            lc_mat = self.material.luxcore_material

            if lc_mat.id != -1 and not self.luxcore_exporter.is_viewport_render:
                self.properties.Set(Property(prefix + '.id', [lc_mat.id]))
                if lc_mat.create_MATERIAL_ID_MASK and self.blender_scene.luxrender_channels.enable_aovs:
                    self.luxcore_exporter.config_exporter.convert_channel('MATERIAL_ID_MASK', lc_mat.id)
                if lc_mat.create_BY_MATERIAL_ID and self.blender_scene.luxrender_channels.enable_aovs:
                    self.luxcore_exporter.config_exporter.convert_channel('BY_MATERIAL_ID', lc_mat.id)
        except Exception as err:
            print('Node material export failed, skipping material: %s\n%s' % (self.material.name, err))
            self.luxcore_exporter.errors = True
            import traceback
            traceback.print_exc()
            self.__convert_default_matte()


    def __generate_material_name(self, name):
        if self.material.library:
            name += '_' + self.material.library.name

        # materials and volumes must not have the same names
        self.luxcore_name = ToValidLuxCoreName(name + '_mat')


    def __convert_default_matte(self):
        if self.luxcore_name == '':
            self.luxcore_name = DEFAULT_MATTE

        self.properties.Set(Property('scene.materials.' + self.luxcore_name + '.type', 'matte'))
        self.properties.Set(Property('scene.materials.' + self.luxcore_name + '.kd', [0.6, 0.6, 0.6]))


    def __convert_default_null(self):
        self.properties.Set(Property('scene.materials.' + DEFAULT_NULL + '.type', 'null'))


    def __set_material_volumes(self, prefix, interior, exterior):
        # This code checks if the volumes are set correctly so rendering does not fail when volumes are missing
        # from the scene. It is assumed that all volumes are already exported prior to material export.
        vol_cache = self.luxcore_exporter.volume_cache
        scene_volumes = {vol_exporter.volume.name: vol_exporter.luxcore_name for vol_exporter in vol_cache.values()}

        default_interior = self.blender_scene.luxrender_world.default_interior_volume
        default_exterior = self.blender_scene.luxrender_world.default_exterior_volume

        if interior in scene_volumes:
            self.properties.Set(Property(prefix + '.volume.interior', scene_volumes[interior]))
        elif default_interior in scene_volumes:
            self.properties.Set(Property(prefix + '.volume.interior', scene_volumes[default_interior]))

        if exterior in scene_volumes:
            self.properties.Set(Property(prefix + '.volume.exterior', scene_volumes[exterior]))
        elif default_exterior in scene_volumes:
            self.properties.Set(Property(prefix + '.volume.exterior', scene_volumes[default_exterior]))


    def __convert_material(self):
        """
        :param material: material to convert
        """
        try:
            material = self.material

            print('Converting material: %s' % material.name)

            self.__generate_material_name(material.name)

            lux_mat_type = material.luxrender_material.type
            lux_mat = getattr(material.luxrender_material, 'luxrender_mat_' + lux_mat_type)
            prefix = 'scene.materials.' + self.luxcore_name

            # Material override (clay render)
            translator_settings = self.blender_scene.luxcore_translatorsettings
            if translator_settings.override_materials:
                if material.luxrender_emission.use_emission:
                    if translator_settings.override_lights:
                        self.__convert_default_matte()
                        return
                elif lux_mat_type != 'mix':
                    if 'glass' in lux_mat_type:
                        if translator_settings.override_glass:
                            self.__convert_default_matte()
                            return
                    elif lux_mat_type == 'null':
                        if translator_settings.override_null:
                            self.__convert_default_matte()
                            return
                    else:
                        # all materials that are not glass, lights or null
                        self.__convert_default_matte()
                        return

            # ###################################################################
            # Matte and Roughmatte
            ####################################################################
            if lux_mat_type == 'matte':
                sigma = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'sigma', 'float')

                if sigma[0] == 0:
                    self.properties.Set(Property(prefix + '.type', ['matte']))
                    self.properties.Set(Property(prefix + '.kd', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Kd', 'color')))
                else:
                    self.properties.Set(Property(prefix + '.type', ['roughmatte']))
                    self.properties.Set(Property(prefix + '.kd', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Kd', 'color')))
                    self.properties.Set(Property(prefix + '.sigma', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'sigma', 'float')))

            ####################################################################
            # Mattetranslucent
            ####################################################################
            elif lux_mat_type == 'mattetranslucent':
                self.properties.Set(Property(prefix + '.type', ['mattetranslucent']))
                self.properties.Set(Property(prefix + '.kr', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Kr', 'color')))
                self.properties.Set(Property(prefix + '.kt', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Kt', 'color')))
                self.properties.Set(Property(prefix + '.sigma', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'sigma', 'float')))

            ####################################################################
            # Metal (for keeping backwards compatibility, internally metal2)
            ####################################################################
            elif lux_mat_type == 'metal':
                fcol = self.luxcore_name + '_fcol'
                self.properties.Set(Property(prefix + '.type', ['metal2']))
                self.properties.Set(Property(prefix + '.fresnel', [fcol]))
                m_type = material.luxrender_material.luxrender_mat_metal.name

                if m_type != 'nk':
                    self.properties.Set(Property('scene.textures.' + fcol + '.type', ['fresnelpreset']))
                    self.properties.Set(
                        Property('scene.textures.' + fcol + '.name',
                                           material.luxrender_material.luxrender_mat_metal.name))

                elif m_type == 'nk':
                    full_name, base_name = get_expanded_file_name(material, lux_mat.filename)
                    self.properties.Set(Property('scene.textures.' + fcol + '.type', ['fresnelsopra']))
                    self.properties.Set(Property('scene.textures.' + fcol + '.file', full_name))

                u_roughness = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'uroughness', 'float')
                if lux_mat.anisotropic:
                    v_roughness = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'vroughness', 'float')
                else:
                    v_roughness = u_roughness

                self.properties.Set(Property(prefix + '.uroughness', u_roughness))
                self.properties.Set(Property(prefix + '.vroughness', v_roughness))

            ####################################################################
            # Metal2
            ####################################################################
            elif lux_mat_type == 'metal2':
                fcol = self.luxcore_name + '_fcol'
                m2_type = material.luxrender_material.luxrender_mat_metal2.metaltype

                if m2_type == 'preset':
                    self.properties.Set(Property('scene.textures.' + fcol + '.type', ['fresnelpreset']))
                    self.properties.Set(
                        Property('scene.textures.' + fcol + '.name',
                                           material.luxrender_material.luxrender_mat_metal2.preset))

                elif m2_type == 'fresnelcolor':
                    value = list(getattr(lux_mat, 'Kr_color'))

                    if getattr(lux_mat, 'Kr_usecolortexture'):
                        # The material attribute is textured, export the texture
                        texture_name = getattr(lux_mat, 'Kr_colortexturename')

                        if texture_name:
                            texture = get_texture_from_scene(self.luxcore_exporter.blender_scene, texture_name)

                            if texture:
                                self.luxcore_exporter.convert_texture(texture)
                                texture_exporter = self.luxcore_exporter.texture_cache[get_elem_key(texture)]

                                is_multiplied = getattr(lux_mat, 'Kr_multiplycolor')

                                if is_multiplied:
                                    scale_tex_name = self.luxcore_name + 'Krcolor' + fcol
                                    self.properties.Set(Property('scene.textures.' + scale_tex_name + '.type', 'scale'))
                                    self.properties.Set(Property('scene.textures.' + scale_tex_name + '.texture1', texture_exporter.luxcore_name))
                                    self.properties.Set(Property('scene.textures.' + scale_tex_name + '.texture2', value))
                                    value = scale_tex_name
                                else:
                                    value = texture_exporter.luxcore_name

                    self.properties.Set(Property('scene.textures.' + fcol + '.type', ['fresnelcolor']))
                    self.properties.Set(Property('scene.textures.' + fcol + '.kr', value))

                elif m2_type == 'nk':
                    full_name, base_name = get_expanded_file_name(material, lux_mat.filename)
                    self.properties.Set(Property('scene.textures.' + fcol + '.type', ['fresnelsopra']))
                    self.properties.Set(Property('scene.textures.' + fcol + '.file', full_name))

                elif m2_type == 'fresneltex':
                    texture_name = lux_mat.fresnel_fresneltexturename

                    if texture_name:
                        texture = get_texture_from_scene(self.blender_scene, texture_name)

                        if texture:
                            self.luxcore_exporter.convert_texture(texture)
                            texture_exporter = self.luxcore_exporter.texture_cache[get_elem_key(texture)]

                            fcol = texture_exporter.luxcore_name

                else:
                    print('WARNING: Not yet supported metal2 type: %s' % m2_type)

                self.properties.Set(Property(prefix + '.type', ['metal2']))
                self.properties.Set(Property(prefix + '.fresnel', [fcol]))

                u_roughness = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'uroughness', 'float')
                if lux_mat.anisotropic:
                    v_roughness = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'vroughness', 'float')
                else:
                    v_roughness = u_roughness

                self.properties.Set(Property(prefix + '.uroughness', u_roughness))
                self.properties.Set(Property(prefix + '.vroughness', v_roughness))

            ####################################################################
            # Mirror
            ####################################################################
            elif lux_mat_type == 'mirror':
                self.properties.Set(Property(prefix + '.type', ['mirror']))
                self.properties.Set(Property(prefix + '.kr', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Kr', 'color')))

            ####################################################################
            # Glossy
            ####################################################################
            elif lux_mat_type == 'glossy':
                self.properties.Set(Property(prefix + '.type', ['glossy2']))
                self.properties.Set(Property(prefix + '.kd', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Kd', 'color')))

                if material.luxrender_material.luxrender_mat_glossy.useior:
                    self.properties.Set(
                        Property(prefix + '.index', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'index', 'float')))
                else:
                    self.properties.Set(Property(prefix + '.ks', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Ks', 'color')))

                self.properties.Set(Property(prefix + '.ka', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Ka', 'color')))
                self.properties.Set(Property(prefix + '.multibounce',
                                             material.luxrender_material.luxrender_mat_glossy.multibounce))
                self.properties.Set(Property(prefix + '.sigma', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'sigma', 'float')))
                self.properties.Set(Property(prefix + '.d', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'd', 'float')))

                u_roughness = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'uroughness', 'float')
                if lux_mat.anisotropic:
                    v_roughness = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'vroughness', 'float')
                else:
                    v_roughness = u_roughness

                self.properties.Set(Property(prefix + '.uroughness', u_roughness))
                self.properties.Set(Property(prefix + '.vroughness', v_roughness))

            ####################################################################
            # Glossycoating
            ####################################################################
            elif lux_mat_type == 'glossycoating':
                self.properties.Set(Property(prefix + '.type', ['glossycoating']))
                if not material.luxrender_material.luxrender_mat_glossycoating.basematerial_material:
                    self.__convert_default_matte()
                    return
                else:
                    try:
                        material_base_name = material.luxrender_material.luxrender_mat_glossycoating.basematerial_material

                        base = bpy.data.materials[material_base_name]
                        self.luxcore_exporter.convert_material(base)
                        base_exporter = self.luxcore_exporter.material_cache[get_elem_key(base)]
                        luxcore_base_name = base_exporter.luxcore_name

                        self.properties.Set(Property(prefix + '.base', [luxcore_base_name]))
                    except Exception as err:
                        print('WARNING: unable to convert base material %s\n%s' % (material.name, err))
                        self.luxcore_exporter.errors = True

                if material.luxrender_material.luxrender_mat_glossycoating.useior:
                    self.properties.Set(
                        Property(prefix + '.index', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'index', 'float')))
                else:
                    self.properties.Set(Property(prefix + '.ks', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Ks', 'color')))

                self.properties.Set(Property(prefix + '.ka', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Ka', 'color')))
                self.properties.Set(Property(prefix + '.multibounce',
                                             material.luxrender_material.luxrender_mat_glossycoating.multibounce))
                self.properties.Set(Property(prefix + '.d', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'd', 'float')))

                u_roughness = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'uroughness', 'float')
                if lux_mat.anisotropic:
                    v_roughness = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'vroughness', 'float')
                else:
                    v_roughness = u_roughness

                self.properties.Set(Property(prefix + '.uroughness', u_roughness))
                self.properties.Set(Property(prefix + '.vroughness', v_roughness))

            ####################################################################
            # Glossytranslucent
            ####################################################################
            elif lux_mat_type == 'glossytranslucent':
                self.properties.Set(Property(prefix + '.type', ['glossytranslucent']))
                self.properties.Set(Property(prefix + '.kt', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Kt', 'color')))
                self.properties.Set(Property(prefix + '.kd', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Kd', 'color')))

                if material.luxrender_material.luxrender_mat_glossytranslucent.useior:
                    self.properties.Set(Property(prefix + '.index', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'index', 'float')))
                else:
                    self.properties.Set(Property(prefix + '.ks', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Ks', 'color')))

                self.properties.Set(Property(prefix + '.ka', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Ka', 'color')))
                self.properties.Set(Property(prefix + '.multibounce',
                                             material.luxrender_material.luxrender_mat_glossytranslucent.multibounce))
                self.properties.Set(Property(prefix + '.d', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'd', 'float')))

                u_roughness = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'uroughness', 'float')
                if lux_mat.anisotropic:
                    v_roughness = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'vroughness', 'float')
                else:
                    v_roughness = u_roughness

                self.properties.Set(Property(prefix + '.uroughness', u_roughness))
                self.properties.Set(Property(prefix + '.vroughness', v_roughness))

                # Backface values
                if material.luxrender_material.luxrender_mat_glossytranslucent.two_sided:
                    if material.luxrender_material.luxrender_mat_glossytranslucent.bf_useior:
                        self.properties.Set(Property(prefix + '.index_bf',
                                                     convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'bf_index', 'float')))
                    else:
                        self.properties.Set(Property(prefix + '.ks_bf',
                                                     convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'backface_Ks', 'color')))

                    self.properties.Set(
                        Property(prefix + '.ka_bf', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'backface_Ka', 'color')))
                    self.properties.Set(Property(prefix + '.multibounce_bf',
                                                 material.luxrender_material.luxrender_mat_glossytranslucent.backface_multibounce))
                    self.properties.Set(Property(prefix + '.d_bf', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'bf_d', 'float')))
                    self.properties.Set(Property(prefix + '.uroughness_bf',
                                                 convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'bf_uroughness', 'float')))
                    self.properties.Set(Property(prefix + '.vroughness_bf',
                                                 convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'bf_vroughness', 'float')))

                    u_roughness_bf = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'bf_uroughness', 'float')
                    if lux_mat.bf_anisotropic:
                        v_roughness_bf = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'bf_vroughness', 'float')
                    else:
                        v_roughness_bf = u_roughness_bf

                    self.properties.Set(Property(prefix + '.uroughness_bf', u_roughness_bf))
                    self.properties.Set(Property(prefix + '.vroughness_bf', v_roughness_bf))

            ####################################################################
            # Glass
            ####################################################################
            elif lux_mat_type == 'glass':
                glassType = 'archglass' if material.luxrender_material.luxrender_mat_glass.architectural else 'glass'
                self.properties.Set(Property(prefix + '.type', [glassType]))
                self.properties.Set(Property(prefix + '.kr', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Kr', 'color')))
                self.properties.Set(Property(prefix + '.kt', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Kt', 'color')))
                self.properties.Set(Property(prefix + '.cauchyb', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'cauchyb', 'float')))
                self.properties.Set(Property(prefix + '.film', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'film', 'float')))
                self.properties.Set(Property(prefix + '.interiorior', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'index', 'float')))

            ####################################################################
            # Glass2
            ####################################################################
            elif lux_mat_type == 'glass2':
                glassType = 'archglass' if material.luxrender_material.luxrender_mat_glass2.architectural else 'glass'
                self.properties.Set(Property(prefix + '.type', [glassType]))
                self.properties.Set(Property(prefix + '.kr', '1.0 1.0 1.0'))
                self.properties.Set(Property(prefix + '.kt', '1.0 1.0 1.0'))

            ####################################################################
            # Roughlass
            ####################################################################
            elif lux_mat_type == 'roughglass':
                self.properties.Set(Property(prefix + '.type', ['roughglass']))
                self.properties.Set(Property(prefix + '.kr', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Kr', 'color')))
                self.properties.Set(Property(prefix + '.kt', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Kt', 'color')))
                self.properties.Set(Property(prefix + '.cauchyb', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'cauchyb', 'float')))
                self.properties.Set(Property(prefix + '.interiorior', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'index', 'float')))

                u_roughness = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'uroughness', 'float')
                if lux_mat.anisotropic:
                    v_roughness = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'vroughness', 'float')
                else:
                    v_roughness = u_roughness

                self.properties.Set(Property(prefix + '.uroughness', u_roughness))
                self.properties.Set(Property(prefix + '.vroughness', v_roughness))

            ####################################################################
            # Cloth
            ####################################################################
            elif lux_mat_type == 'cloth':
                self.properties.Set(Property(prefix + '.type', ['cloth']))
                self.properties.Set(
                    Property(prefix + '.preset', material.luxrender_material.luxrender_mat_cloth.presetname))
                self.properties.Set(Property(prefix + '.warp_kd', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'warp_Kd', 'color')))
                self.properties.Set(Property(prefix + '.warp_ks', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'warp_Ks', 'color')))
                self.properties.Set(Property(prefix + '.weft_kd', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'weft_Kd', 'color')))
                self.properties.Set(Property(prefix + '.weft_ks', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'weft_Ks', 'color')))
                self.properties.Set(
                    Property(prefix + '.repeat_u', material.luxrender_material.luxrender_mat_cloth.repeat_u))
                self.properties.Set(
                    Property(prefix + '.repeat_v', material.luxrender_material.luxrender_mat_cloth.repeat_v))

            ####################################################################
            # Carpaint
            ####################################################################
            elif lux_mat_type == 'carpaint':
                self.properties.Set(Property(prefix + '.type', ['carpaint']))
                self.properties.Set(
                    Property(prefix + '.preset', material.luxrender_material.luxrender_mat_carpaint.name))
                self.properties.Set(Property(prefix + '.kd', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Kd', 'color')))
                self.properties.Set(Property(prefix + '.ka', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Ka', 'color')))
                self.properties.Set(Property(prefix + '.ks1', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Ks1', 'color')))
                self.properties.Set(Property(prefix + '.ks2', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Ks2', 'color')))
                self.properties.Set(Property(prefix + '.ks3', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Ks3', 'color')))
                self.properties.Set(Property(prefix + '.d', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'd', 'float')))
                self.properties.Set(Property(prefix + '.m1',
                                             material.luxrender_material.luxrender_mat_carpaint.M1_floatvalue))
                self.properties.Set(Property(prefix + '.m2',
                                             material.luxrender_material.luxrender_mat_carpaint.M2_floatvalue))
                self.properties.Set(Property(prefix + '.m3',
                                             material.luxrender_material.luxrender_mat_carpaint.M3_floatvalue))
                self.properties.Set(Property(prefix + '.r1',
                                             material.luxrender_material.luxrender_mat_carpaint.R1_floatvalue))
                self.properties.Set(Property(prefix + '.r2',
                                             material.luxrender_material.luxrender_mat_carpaint.R2_floatvalue))
                self.properties.Set(Property(prefix + '.r3',
                                             material.luxrender_material.luxrender_mat_carpaint.R3_floatvalue))

            ####################################################################
            # Velvet
            ####################################################################
            elif lux_mat_type == 'velvet':
                self.properties.Set(Property(prefix + '.type', ['velvet']))
                self.properties.Set(Property(prefix + '.kd', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'Kd', 'color')))
                self.properties.Set(Property(prefix + '.thickness',
                                             material.luxrender_material.luxrender_mat_velvet.thickness))
                self.properties.Set(Property(prefix + '.p1', material.luxrender_material.luxrender_mat_velvet.p1))
                self.properties.Set(Property(prefix + '.p2', material.luxrender_material.luxrender_mat_velvet.p2))
                self.properties.Set(Property(prefix + '.p3', material.luxrender_material.luxrender_mat_velvet.p3))

            ####################################################################
            # Null
            ####################################################################
            elif lux_mat_type == 'null':
                self.properties.Set(Property(prefix + '.type', ['null']))

            ####################################################################
            # Mix
            ####################################################################
            elif lux_mat_type == 'mix':
                if (not material.luxrender_material.luxrender_mat_mix.namedmaterial1_material or
                        not material.luxrender_material.luxrender_mat_mix.namedmaterial2_material):
                    self.__convert_default_matte()
                    return
                else:
                    try:
                        mat1_name = material.luxrender_material.luxrender_mat_mix.namedmaterial1_material
                        mat2_name = material.luxrender_material.luxrender_mat_mix.namedmaterial2_material

                        mat1 = bpy.data.materials[mat1_name]
                        mat2 = bpy.data.materials[mat2_name]

                        self.luxcore_exporter.convert_material(mat1)
                        self.luxcore_exporter.convert_material(mat2)

                        mat1_luxcore_name = self.luxcore_exporter.material_cache[get_elem_key(mat1)].luxcore_name
                        mat2_luxcore_name = self.luxcore_exporter.material_cache[get_elem_key(mat2)].luxcore_name

                        self.properties.Set(Property(prefix + '.type', ['mix']))
                        self.properties.Set(Property(prefix + '.material1', mat1_luxcore_name))
                        self.properties.Set(Property(prefix + '.material2', mat2_luxcore_name))
                        self.properties.Set(Property(prefix + '.amount', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, lux_mat, 'amount', 'float')))
                    except Exception as err:
                        print('WARNING: unable to convert mix material %s\n%s' % (material.name, err))
                        self.luxcore_exporter.errors = True
                        import traceback
                        traceback.print_exc()
                        self.__convert_default_matte()
                        return

            ####################################################################
            # Fallback
            ####################################################################
            else:
                self.__convert_default_matte()
                return

            ####################################################################
            # Common settings for all material types
            ####################################################################
            if not translator_settings.override_materials:
                # Bump mapping
                if material.luxrender_material.bumpmap_usefloattexture:
                    self.properties.Set(Property(prefix + '.bumptex',
                                                 convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, material.luxrender_material, 'bumpmap',
                                                                            'float')))

                # Normal mapping (make sure a texture is selected)
                if material.luxrender_material.normalmap_usefloattexture and material.luxrender_material.normalmap_floattexturename:
                    normalmap = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name,
                                                        material.luxrender_material, 'normalmap', 'float')
                    # We have to set normalmap gamma to 1
                    self.properties.Set(Property('scene.textures.' + normalmap + '.gamma', 1))

                    self.properties.Set(Property(prefix + '.normaltex', normalmap))

                # Interior/exterior volumes
                interior = self.material.luxrender_material.Interior_volume
                exterior = self.material.luxrender_material.Exterior_volume
                self.__set_material_volumes(prefix, interior, exterior)

            # coating for all materials
            if hasattr(material, 'luxrender_coating') and material.luxrender_coating.use_coating:
                name_coating = self.luxcore_name + '_coated'
                luxMat_coated = material.luxrender_coating
                prefix += '_coated'
                self.properties.Set(Property(prefix + '.type', ['glossycoating']))
                self.properties.Set(Property(prefix + '.base', [self.luxcore_name]))
                self.properties.Set(Property(prefix + '.kd', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, luxMat_coated, 'Ks', 'color')))

                if material.luxrender_coating.useior:
                    self.properties.Set(
                        Property(prefix + '.index', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, luxMat_coated, 'index', 'float')))
                else:
                    self.properties.Set(Property(prefix + '.ks', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, luxMat_coated, 'Ks', 'color')))

                self.properties.Set(Property(prefix + '.ka', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, luxMat_coated, 'Ka', 'color')))
                self.properties.Set(Property(prefix + '.multibounce',
                                             material.luxrender_coating.multibounce))
                self.properties.Set(Property(prefix + '.d', convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, luxMat_coated, 'd', 'float')))

                u_roughness = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, luxMat_coated, 'uroughness', 'float')
                if luxMat_coated.anisotropic:
                    v_roughness = convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, luxMat_coated, 'vroughness', 'float')
                else:
                    v_roughness = u_roughness

                self.properties.Set(Property(prefix + '.uroughness', u_roughness))
                self.properties.Set(Property(prefix + '.vroughness', v_roughness))

                self.luxcore_name = name_coating

            # LuxCore specific material settings
            lc_mat = material.luxcore_material

            self.properties.Set(Property(prefix + '.shadowcatcher.enable', lc_mat.is_shadow_catcher))

            # Material group
            materialgroup_name = lc_mat.materialgroup
            if materialgroup_name in self.blender_scene.luxrender_materialgroups.materialgroups:
                mg = self.blender_scene.luxrender_materialgroups.materialgroups[materialgroup_name]

                self.properties.Set(Property(prefix + '.id', mg.id))
                if mg.create_MATERIAL_ID_MASK and self.blender_scene.luxrender_channels.enable_aovs:
                    self.luxcore_exporter.config_exporter.convert_channel('MATERIAL_ID_MASK', mg.id)
                if mg.create_BY_MATERIAL_ID and self.blender_scene.luxrender_channels.enable_aovs:
                    self.luxcore_exporter.config_exporter.convert_channel('BY_MATERIAL_ID', mg.id)

            self.properties.Set(Property(prefix + '.samples', [lc_mat.samples]))

            if material.luxrender_emission.use_emission:
                self.properties.Set(Property(prefix + '.emission.samples', [lc_mat.emission_samples]))

            self.properties.Set(Property(prefix + '.visibility.indirect.diffuse.enable',
                                         lc_mat.visibility_indirect_diffuse_enable))
            self.properties.Set(Property(prefix + '.visibility.indirect.glossy.enable',
                                         lc_mat.visibility_indirect_glossy_enable))
            self.properties.Set(Property(prefix + '.visibility.indirect.specular.enable',
                                         lc_mat.visibility_indirect_specular_enable))

            if not (translator_settings.override_materials and translator_settings.override_lights):
                # LuxRender emission
                if material.luxrender_emission.use_emission:
                    emit_enabled = self.blender_scene.luxrender_lightgroups.is_enabled(material.luxrender_emission.lightgroup)
                    emit_enabled &= (material.luxrender_emission.L_color.v * material.luxrender_emission.gain) > 0.0
                    if emit_enabled:
                        self.properties.Set(Property(prefix + '.emission',
                                                     convert_texture_channel(self.luxcore_exporter, self.properties, self.luxcore_name, material.luxrender_emission, 'L', 'color')))

                        self.properties.Set(Property(prefix + '.emission.power', material.luxrender_emission.power))
                        self.properties.Set(Property(prefix + '.emission.efficency', material.luxrender_emission.efficacy))

                        lightgroup = material.luxrender_emission.lightgroup
                        lightgroup_id = self.luxcore_exporter.lightgroup_cache.get_id(lightgroup, self.blender_scene, self)

                        if not self.blender_scene.luxrender_lightgroups.ignore and is_lightgroup_opencl_compatible(self.luxcore_exporter, lightgroup_id):
                            self.properties.Set(Property(prefix + '.emission.id', [lightgroup_id]))

                        gain = material.luxrender_emission.gain
                        self.properties.Set(Property(prefix + '.emission.gain', [gain] * 3))

            # alpha transparency
            if hasattr(material, 'luxrender_transparency') and material.luxrender_transparency.transparent:
                use_alpha_transparency = True

                alpha = 0.0

                self.__convert_default_null()

                sourceMap = {
                    'carpaint': 'Kd',
                    'glass': 'Kr',
                    'glossy': 'Kd',
                    'glossytranslucent': 'Kd',
                    'matte': 'Kd',
                    'mattetranslucent': 'Kr',
                    'mirror': 'Kr',
                    'roughglass': 'Kr',
                    'scatter': 'Kd',
                    'shinymetal': 'Kr',
                    'velvet': 'Kd',
                    'metal2': 'Kr',
                }

                alpha_source = material.luxrender_transparency.alpha_source

                if alpha_source == 'texture':
                    if hasattr(material.luxrender_transparency, 'alpha_floattexturename'):
                        texture_name = material.luxrender_transparency.alpha_floattexturename

                        if texture_name in bpy.data.textures:
                            texture = bpy.data.textures[texture_name]

                            alpha_tex_exporter = TextureExporter(self.luxcore_exporter, self.blender_scene, texture)
                            alpha_tex_exporter.convert(texture_name + material.name + '_alpha')
                            alpha = alpha_tex_exporter.luxcore_name

                            self.properties.Set(alpha_tex_exporter.properties)
                            # Note: the channel (rgb/alpha/mean/...) is set in the texture

                            if material.luxrender_transparency.inverse:
                                inverter_name = alpha + '_inverter'
                                inverter_prefix = 'scene.textures.' + inverter_name

                                self.properties.Set(Property(inverter_prefix + '.type', 'mix'))
                                self.properties.Set(Property(inverter_prefix + '.amount', alpha))
                                self.properties.Set(Property(inverter_prefix + '.texture1', 1.0))
                                self.properties.Set(Property(inverter_prefix + '.texture2', 0.0))

                                alpha = inverter_name
                        else:
                            use_alpha_transparency = False

                elif alpha_source == 'constant':
                    alpha = material.luxrender_transparency.alpha_value

                # diffusealpha, diffusemean, diffuseintensity
                elif (material.luxrender_material.type in sourceMap
                      and getattr(lux_mat, '%s_usecolortexture' % sourceMap[material.luxrender_material.type])):
                    # Get base texture name
                    texture_name = getattr(lux_mat, '%s_colortexturename' % sourceMap[material.luxrender_material.type])

                    if texture_name in bpy.data.textures:
                        # Get blender texture
                        texture = bpy.data.textures[texture_name]
                        # Export texture, get luxcore texture name
                        alpha_tex_exporter = TextureExporter(self.luxcore_exporter, self.blender_scene, texture)
                        alpha_tex_exporter.convert(texture_name + material.name + '_alpha')
                        alpha = alpha_tex_exporter.luxcore_name

                        self.properties.Set(alpha_tex_exporter.properties)

                        channelMap = {
                            'diffusealpha': 'alpha',
                            'diffusemean': 'mean',
                            'diffuseintensity': 'colored_mean',
                        }
                        self.properties.Set(Property('scene.textures.' + alpha + '.channel', [channelMap[alpha_source]]))
                    else:
                        use_alpha_transparency = False
                else:
                    print(
                    'WARNING: alpha transparency not supported for material type %s' % material.luxrender_material.type)
                    use_alpha_transparency = False

                if use_alpha_transparency:
                    self.properties.Set(Property(prefix + '.transparency', alpha))
        except Exception as err:
            print('Material export failed, skipping material: %s\n%s' % (self.material.name, err))
            self.luxcore_exporter.errors = True
            import traceback
            traceback.print_exc()
            self.__convert_default_matte()