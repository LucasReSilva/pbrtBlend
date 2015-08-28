# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
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
# Blender Libs
import bpy, bl_operators

# LuxRender Libs
from .. import LuxRenderAddon


@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_add_material_nodetree(bpy.types.Operator):
    """"""
    bl_idname = "luxrender.add_material_nodetree"
    bl_label = "Use Material Nodes"
    bl_description = "Add a LuxRender node tree linked to this material"

    # idtype = StringProperty(name="ID Type", default="material")

    def execute(self, context):
        # idtype = self.properties.idtype
        idtype = 'material'
        context_data = {'material': context.material, 'lamp': context.lamp}
        idblock = context_data[idtype]

        nt = bpy.data.node_groups.new(idblock.name, type='luxrender_material_nodes')
        nt.use_fake_user = True
        idblock.luxrender_material.nodetree = nt.name

        ctx_vol = context.scene.luxrender_volumes
        ctx_mat = context.material.luxrender_material

        # Get the mat type set in editor, todo: find a more iterative way to get context
        node_type = 'luxrender_material_%s_node' % ctx_mat.type

        if ctx_mat.type == 'matte':
            editor_type = ctx_mat.luxrender_mat_matte
        if ctx_mat.type == 'mattetranslucent':
            editor_type = ctx_mat.luxrender_mat_mattetranslucent
        if ctx_mat.type == 'glossy':
            editor_type = ctx_mat.luxrender_mat_glossy
        if ctx_mat.type == 'glossycoating':
            editor_type = ctx_mat.luxrender_mat_glossycoating
        if ctx_mat.type == 'glossytranslucent':
            editor_type = ctx_mat.luxrender_mat_glossytranslucent
        if ctx_mat.type == 'glass':
            editor_type = ctx_mat.luxrender_mat_glass
        if ctx_mat.type == 'glass2':
            editor_type = ctx_mat.luxrender_mat_glass2
        if ctx_mat.type == 'roughglass':
            editor_type = ctx_mat.luxrender_mat_roughglass
        if ctx_mat.type == 'mirror':
            editor_type = ctx_mat.luxrender_mat_mirror
        if ctx_mat.type == 'carpaint':
            editor_type = ctx_mat.luxrender_mat_carpaint
        if ctx_mat.type == 'metal':
            editor_type = ctx_mat.luxrender_mat_metal
        if ctx_mat.type == 'metal2':
            editor_type = ctx_mat.luxrender_mat_metal2
        if ctx_mat.type == 'velvet':
            editor_type = ctx_mat.luxrender_mat_velvet
        if ctx_mat.type == 'cloth':
            editor_type = ctx_mat.luxrender_mat_cloth
        if ctx_mat.type == 'scatter':
            editor_type = ctx_mat.luxrender_mat_scatter
        if ctx_mat.type == 'mix':
            editor_type = ctx_mat.luxrender_mat_mix
        if ctx_mat.type == 'layered':
            editor_type = ctx_mat.luxrender_mat_layered

        # handling for not existent shinymetal node, just hack atm.
        if ctx_mat.type == 'shinymetal':
            editor_type = ctx_mat.luxrender_mat_metal2
            node_type = 'luxrender_material_metal2_node'

        if idtype == 'material':
            shader = nt.nodes.new(node_type)  # create also matnode from editor type
            shader.location = 200, 570
            sh_out = nt.nodes.new('luxrender_material_output_node')
            sh_out.location = 500, 400
            nt.links.new(shader.outputs[0], sh_out.inputs[0])

            # Get material settings ( color )
            if 'Absorption Color' in shader.inputs:
                shader.inputs['Absorption Color'].color = editor_type.Ka_color
            if 'Diffuse Color' in shader.inputs:
                shader.inputs['Diffuse Color'].color = editor_type.Kd_color
            if 'Reflection Color' in shader.inputs:
                shader.inputs['Reflection Color'].color = editor_type.Kr_color
            if 'Specular Color' in shader.inputs:
                shader.inputs['Specular Color'].color = editor_type.Ks_color
            if 'Specular Color 1' in shader.inputs:
                shader.inputs['Specular Color 1'].color = editor_type.Ks1_color
            if 'Specular Color 2' in shader.inputs:
                shader.inputs['Specular Color 2'].color = editor_type.Ks2_color
            if 'Specular Color 3' in shader.inputs:
                shader.inputs['Specular Color 3'].color = editor_type.Ks3_color
            if 'Transmission Color' in shader.inputs:
                shader.inputs['Transmission Color'].color = editor_type.Kt_color
            if 'Warp Diffuse Color' in shader.inputs:
                shader.inputs['Warp Diffuse Color'].color = editor_type.warp_Kd_color
            if 'Warp Specular Color' in shader.inputs:
                shader.inputs['Warp Specular Color'].color = editor_type.warp_Ks_color
            if 'Weft Diffuse Color' in shader.inputs:
                shader.inputs['Weft Diffuse Color'].color = editor_type.weft_Kd_color
            if 'Weft Specular Color' in shader.inputs:
                shader.inputs['Weft Specular Color'].color = editor_type.weft_Ks_color
            if 'Backface Absorption Color' in shader.inputs:
                shader.inputs['Backface Absorption Color'].color = editor_type.backface_Ka_color
            if 'Backface Specular Color' in shader.inputs:
                shader.inputs['Backface Specular Color'].color = editor_type.backface_Ks_color

            # Get various material settings ( float )
            if 'Mix Amount' in shader.inputs:
                shader.inputs['Mix Amount'].amount = editor_type.amount_floatvalue

            if 'Cauchy B' in shader.inputs:
                shader.inputs['Cauchy B'].cauchyb = editor_type.cauchyb_floatvalue

            if 'Film IOR' in shader.inputs:
                shader.inputs['Film IOR'].filmindex = editor_type.filmindex_floatvalue

            if 'Film Thickness (nm)' in shader.inputs:
                shader.inputs['Film Thickness (nm)'].film = editor_type.film_floatvalue

            if 'IOR' in shader.inputs and hasattr(shader.inputs['IOR'], 'index'):
                shader.inputs['IOR'].index = editor_type.index_floatvalue  # not fresnel IOR

            if 'U-Roughness' in shader.inputs:
                shader.inputs['U-Roughness'].uroughness = editor_type.uroughness_floatvalue

            if 'V-Roughness' in shader.inputs:
                shader.inputs['V-Roughness'].vroughness = editor_type.vroughness_floatvalue

            if 'Sigma' in shader.inputs:
                shader.inputs['Sigma'].sigma = editor_type.sigma_floatvalue

            # non-socket parameters ( bool )
            if hasattr(shader, 'use_ior'):
                shader.use_ior = editor_type.useior

            if hasattr(shader, 'multibounce'):
                shader.multibounce = editor_type.multibounce

            if hasattr(shader, 'use_anisotropy'):
                shader.use_anisotropy = editor_type.anisotropic

            if hasattr(shader, 'dispersion'):
                shader.dispersion = editor_type.dispersion

            if hasattr(shader, 'arch'):
                shader.arch = editor_type.architectural

            if hasattr(shader, 'advanced'):
                shader.advanced = editor_type.advanced

            # non-socket parameters ( other )
            # velvet
            if hasattr(shader, 'thickness'):
                shader.thickness = editor_type.thickness

            if hasattr(shader, 'p1'):
                shader.p1 = editor_type.p1

            if hasattr(shader, 'p2'):
                shader.p2 = editor_type.p2

            if hasattr(shader, 'p3'):
                shader.p3 = editor_type.p3

            # metal 1
            if hasattr(shader, 'metal_preset'):
                shader.metal_preset = editor_type.name

            if hasattr(shader, 'metal_nkfile'):
                shader.metal_nkfile = editor_type.filename

            # Get the volumes
            def get_vol_type(name):
                for vol in ctx_vol.volumes:
                    if vol.name == name:
                        volume_type = 'luxrender_volume_%s_node' % (vol.type)
                return volume_type

            if ctx_mat.Interior_volume:
                vol_node = get_vol_type(ctx_mat.Interior_volume)
                volume_int = nt.nodes.new(vol_node)
                volume_int.location = 200, 200
                nt.links.new(volume_int.outputs[0], sh_out.inputs[1])
                volume_int.inputs['IOR'].fresnel = ctx_vol.volumes[ctx_mat.Interior_volume].fresnel_fresnelvalue

            if ctx_mat.Exterior_volume:
                vol_node = get_vol_type(ctx_mat.Exterior_volume)
                volume_ext = nt.nodes.new(vol_node)
                volume_ext.location = 200, -50
                nt.links.new(volume_ext.outputs[0], sh_out.inputs[2])
                volume_ext.inputs['IOR'].fresnel = ctx_vol.volumes[ctx_mat.Exterior_volume].fresnel_fresnelvalue

        #else:
        #   nt.nodes.new('OutputLightShaderNode')

        return {'FINISHED'}


@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_add_volume_nodetree(bpy.types.Operator):
    """"""
    bl_idname = "luxrender.add_volume_nodetree"
    bl_label = "Use Volume Nodes"
    bl_description = "Add a LuxRender node tree linked to this volume"

    def execute(self, context):
        current_vol_ind = context.scene.luxrender_volumes.volumes_index
        current_vol = context.scene.luxrender_volumes.volumes[current_vol_ind]

        nt = bpy.data.node_groups.new(current_vol.name, type='luxrender_volume_nodes')
        nt.use_fake_user = True
        current_vol.nodetree = nt.name

        sh_out = nt.nodes.new('luxrender_volume_output_node')
        sh_out.location = 500, 400

        return {'FINISHED'}