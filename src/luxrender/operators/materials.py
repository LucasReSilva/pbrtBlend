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
import json, math, os, mathutils

# LuxRender Libs
from .. import LuxRenderAddon
from ..outputs import LuxLog, LuxManager
from ..export import materials as export_materials


@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_load_material(bpy.types.Operator):
    bl_idname = 'luxrender.load_material'
    bl_label = 'Load material'
    bl_description = 'Load material from LBM2 file'

    filter_glob = bpy.props.StringProperty(default='*.lbm2', options={'HIDDEN'})
    use_filter = bpy.props.BoolProperty(default=True, options={'HIDDEN'})
    filename = bpy.props.StringProperty(name='Destination filename')
    directory = bpy.props.StringProperty(name='Destination directory')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        try:
            if not self.properties.filename or not self.properties.directory:
                raise Exception('No filename or directory given.')

            blender_mat = context.material
            luxrender_mat = context.material.luxrender_material

            fullpath = os.path.join(
                self.properties.directory,
                self.properties.filename
            )
            with open(fullpath, 'r') as lbm2_file:
                lbm2_data = json.load(lbm2_file)

            luxrender_mat.load_lbm2(context, lbm2_data, blender_mat, context.object)

            return {'FINISHED'}

        except Exception as err:
            self.report({'ERROR'}, 'Cannot load: %s' % err)
            return {'CANCELLED'}


@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_save_material(bpy.types.Operator):
    bl_idname = 'luxrender.save_material'
    bl_label = 'Save material'
    bl_description = 'Save material as LXM or LBM2 file'

    filter_glob = bpy.props.StringProperty(default='*.lbm2;*.lxm', options={'HIDDEN'})
    use_filter = bpy.props.BoolProperty(default=True, options={'HIDDEN'})
    filename = bpy.props.StringProperty(name='Destination filename')
    directory = bpy.props.StringProperty(name='Destination directory')

    material_file_type = bpy.props.EnumProperty(name="Exported file type",
                                                items=[('LBM2', 'LBM2', 'LBM2'), ('LXM', 'LXM', 'LXM')])

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        try:
            if not self.properties.filename or not self.properties.directory:
                raise Exception('No filename or directory given.')

            blender_mat = context.material
            luxrender_mat = context.material.luxrender_material

            LM = LuxManager("material_save", self.properties.material_file_type)
            LuxManager.SetActive(LM)
            LM.SetCurrentScene(context.scene)

            material_context = LM.lux_context

            fullpath = os.path.join(
                self.properties.directory,
                self.properties.filename
            )

            # Make sure the filename has the correct extension
            if not fullpath.lower().endswith('.%s' % self.properties.material_file_type.lower()):
                fullpath += '.%s' % self.properties.material_file_type.lower()

            export_materials.ExportedMaterials.clear()
            export_materials.ExportedTextures.clear()

            # This causes lb25 to embed all external data ...
            context.scene.luxrender_engine.is_saving_lbm2 = True

            # Include interior/exterior for this material
            for volume in context.scene.luxrender_volumes.volumes:
                if volume.name in [luxrender_mat.Interior_volume, luxrender_mat.Exterior_volume]:
                    material_context.makeNamedVolume(volume.name, *volume.api_output(material_context))

            cr = context.scene.luxrender_testing.clay_render
            context.scene.luxrender_testing.clay_render = False
            luxrender_mat.export(context.scene, material_context, blender_mat)
            context.scene.luxrender_testing.clay_render = cr

            material_context.set_material_name(blender_mat.name)
            material_context.update_material_metadata(
                interior=luxrender_mat.Interior_volume,
                exterior=luxrender_mat.Exterior_volume
            )

            material_context.write(fullpath)

            # .. and must be reset!
            context.scene.luxrender_engine.is_saving_lbm2 = False

            LM.reset()
            LuxManager.SetActive(None)

            self.report({'INFO'}, 'Material "%s" saved to %s' % (blender_mat.name, fullpath))
            return {'FINISHED'}

        except Exception as err:
            self.report({'ERROR'}, 'Cannot save: %s' % err)
            return {'CANCELLED'}


def material_converter(report, scene, blender_mat):
    try:
        luxrender_mat = blender_mat.luxrender_material

        # TODO - check values marked #ASV - Arbitrary Scale Value

        luxrender_mat.Interior_volume = ''
        luxrender_mat.Exterior_volume = ''

        luxrender_mat.reset(prnt=blender_mat)

        if blender_mat.raytrace_mirror.use and blender_mat.raytrace_mirror.reflect_factor >= 0.9:
            # for high mirror reflection values switch to mirror material
            luxrender_mat.set_type('mirror')
            lmm = luxrender_mat.luxrender_mat_mirror
            lmm.Kr_color = [i for i in blender_mat.mirror_color]
            luxmat = lmm
        elif blender_mat.specular_intensity < 0.01:
            # use matte as glossy mat with very low specular is not equal matte
            luxrender_mat.set_type('matte')
            lms = luxrender_mat.luxrender_mat_matte
            lms.Kd_color = [blender_mat.diffuse_intensity * i for i in blender_mat.diffuse_color]
            lms.sigma_floatvalue = 0.0
            luxmat = lms
        else:
            luxrender_mat.set_type('glossy')
            lmg = luxrender_mat.luxrender_mat_glossy
            lmg.multibounce = False
            lmg.useior = False
            lmg.Kd_color = [blender_mat.diffuse_intensity * i for i in blender_mat.diffuse_color]

            logHardness = math.log(blender_mat.specular_hardness)

            # fit based on empirical measurements
            # measurements based on intensity of 0.5, use linear scale for other intensities
            specular_scale = 2.0 * max(0.0128415 * logHardness ** 2 - 0.171266 * logHardness + 0.575631, 0.0)

            lmg.Ks_color = [min(specular_scale * blender_mat.specular_intensity * i, 0.25) for i in
                            blender_mat.specular_color]

            # fit based on empirical measurements
            roughness = min(max(0.757198 - 0.120395 * logHardness, 0.0), 1.0)

            lmg.uroughness_floatvalue = roughness
            lmg.vroughness_floatvalue = roughness
            lmg.uroughness_usefloattexture = lmg.vroughness_usefloattexture = False
            luxmat = lmg


        # Emission
        lme = blender_mat.luxrender_emission
        if blender_mat.emit > 0:
            lme.use_emission = True
            lme.L_color = [1.0, 1.0, 1.0]
            lme.gain = blender_mat.emit
        else:
            lme.use_emission = False

        # Transparency
        lmt = blender_mat.luxrender_transparency
        if blender_mat.use_transparency:
            lmt.transparent = True
            lmt.alpha_source = 'constant'
            lmt.alpha_value = blender_mat.alpha
        else:
            lmt.transparent = False

        # iterate textures and build mix stacks according to influences
        Kd_stack = []
        Ks_stack = []
        Lux_TexName = []
        bump_tex = None
        for tex_slot in blender_mat.texture_slots:
            if tex_slot is not None:
                if tex_slot.use and tex_slot.texture.type != 'NONE' and \
                                tex_slot.texture.luxrender_texture.type != 'BLENDER':
                    tex_slot.texture.luxrender_texture.type = 'BLENDER'

                    if tex_slot.use_map_color_diffuse:
                        dcf = tex_slot.diffuse_color_factor

                        if tex_slot.use_map_diffuse:
                            dcf *= tex_slot.diffuse_factor
                        Kd_stack.append((tex_slot.texture, dcf, tex_slot.color))

                    if tex_slot.use_map_color_spec:
                        scf = tex_slot.specular_color_factor

                        if tex_slot.use_map_specular:
                            scf *= tex_slot.specular_factor
                        Ks_stack.append((tex_slot.texture, scf))

                    if tex_slot.use_map_normal:
                        bump_tex = (tex_slot.texture, tex_slot.normal_factor)

        if luxrender_mat.type in ('matte', 'glossy'):
            # print(len(Kd_stack))
            if len(Kd_stack) == 1:
                tex = Kd_stack[0][0]
                dcf = Kd_stack[0][1]
                color = Kd_stack[0][2]
                variant = tex.luxrender_texture.get_paramset(scene, tex)[0]

                if variant == 'color':
                    # assign the texture directly
                    luxmat.Kd_usecolortexture = True
                    luxmat.Kd_colortexturename = tex.name
                    luxmat.Kd_color = [i * Kd_stack[0][1] for i in luxmat.Kd_color]
                    luxmat.Kd_multiplycolor = True
                else:
                    # TODO - insert mix texture
                    # check there are enough free empty texture slots !

                    if tex.use_color_ramp:
                        if len(Kd_stack) < 16:
                            mix_tex_slot = blender_mat.texture_slots.add()
                            color_tex_slot = blender_mat.texture_slots.add()
                            alpha_tex_slot = blender_mat.texture_slots.add()
                            mix_tex_slot.use = True
                            color_tex_slot.use = True
                            alpha_tex_slot.use = True

                            mix_tex = mix_tex_slot.texture = bpy.data.textures.new('Lux::%s' % tex.name, 'NONE')
                            color_tex = color_tex_slot.texture = bpy.data.textures.new('Lux::color:%s' % tex.name,
                                                                                       'NONE')
                            alpha_tex = alpha_tex_slot.texture = bpy.data.textures.new('Lux::alpha:%s' % tex.name,
                                                                                       'NONE')
                            mix_lux_tex = mix_tex.luxrender_texture
                            lux_tex = color_tex.luxrender_texture
                            alpha_lux_tex = alpha_tex.luxrender_texture

                            col_ramp = tex.color_ramp.elements
                            mix_lux_tex.type = 'mix'
                            lux_tex.type = 'band'
                            alpha_lux_tex.type = 'band'
                            mix_params = mix_lux_tex.luxrender_tex_mix
                            color_params = lux_tex.luxrender_tex_band
                            alpha_params = alpha_lux_tex.luxrender_tex_band

                            color_params.variant = 'color'
                            color_params.noffsets = len(col_ramp)
                            color_params.amount_usefloattexture = True
                            color_params.amount_floattexturename = tex.name
                            alpha_params.variant = 'float'
                            alpha_params.noffsets = len(col_ramp)
                            alpha_params.amount_usefloattexture = True
                            alpha_params.amount_floattexturename = tex.name
                            mix_params.variant = 'color'
                            mix_params.amount_usefloattexture = True
                            mix_params.amount_floattexturename = alpha_tex.name
                            mix_params.tex1_usecolortexture = False
                            mix_params.tex1_color = blender_mat.diffuse_color
                            mix_params.tex2_usecolortexture = True
                            mix_params.tex2_colortexturename = color_tex.name

                            for i in range(len(col_ramp)):
                                if hasattr(color_params, 'offsetcolor%d' % (i + 1)):
                                    setattr(color_params, 'offsetcolor%d' % (i + 1), col_ramp[i].position)
                                    setattr(alpha_params, 'offsetfloat%d' % (i + 1), col_ramp[i].position)
                                    setattr(color_params, 'tex%d_color' % (i + 1),
                                            (col_ramp[i].color[0], col_ramp[i].color[1], col_ramp[i].color[2]))
                                    setattr(alpha_params, 'tex%d_floatvalue' % (i + 1), col_ramp[i].color[3])

                            luxmat.Kd_usecolortexture = True
                            luxmat.Kd_colortexturename = mix_tex.name
                    pass
            elif len(Kd_stack) > 1:
                # TODO - set up a mix stack.
                # check there are enough free empty texture slots !
                if (len(Kd_stack) * 3 - 1) < 18:
                    for n in range(len(Kd_stack)):
                        tex = Kd_stack[n][0]
                        dcf = Kd_stack[n][1]
                        color = Kd_stack[n][2]

                        if tex.use_color_ramp:
                            # TODO: Implement band texture conversion
                            mix_tex_slot = blender_mat.texture_slots.add()
                            alpha_tex_slot = blender_mat.texture_slots.add()
                            color_tex_slot = blender_mat.texture_slots.add()
                            mix_tex_slot.use = True
                            color_tex_slot.use = True
                            alpha_tex_slot.use = True
                            mix_tex = mix_tex_slot.texture = bpy.data.textures.new('Lux::%s' % tex.name, 'NONE')
                            color_tex = color_tex_slot.texture = bpy.data.textures.new('Lux::color:%s' % tex.name,
                                                                                       'NONE')
                            alpha_tex = alpha_tex_slot.texture = bpy.data.textures.new('Lux::alpha:%s' % tex.name,
                                                                                       'NONE')

                            Lux_TexName.append(mix_tex.name)

                            mix_lux_tex = mix_tex.luxrender_texture
                            color_lux_tex = color_tex.luxrender_texture
                            alpha_lux_tex = alpha_tex.luxrender_texture

                            mix_params = mix_lux_tex.luxrender_tex_mix
                            mix_params.variant = 'color'
                            mix_params.amount_floatvalue = dcf
                            mix_params.amount_usefloattexture = True

                            col_ramp = tex.color_ramp.elements
                            mix_lux_tex.type = 'mix'
                            color_lux_tex.type = 'band'
                            alpha_lux_tex.type = 'band'

                            color_params = color_lux_tex.luxrender_tex_band
                            alpha_params = alpha_lux_tex.luxrender_tex_band

                            color_params.variant = 'color'
                            color_params.noffsets = len(col_ramp)
                            color_params.amount_usefloattexture = True
                            color_params.amount_floattexturename = tex.name

                            alpha_params.variant = 'float'
                            alpha_params.noffsets = len(col_ramp)
                            alpha_params.amount_usefloattexture = True
                            alpha_params.amount_floattexturename = tex.name

                            for i in range(len(col_ramp)):
                                if hasattr(color_params, 'offsetcolor%d' % (i + 1)):
                                    setattr(color_params, 'offsetcolor%d' % (i + 1), col_ramp[i].position)
                                    setattr(alpha_params, 'offsetfloat%d' % (i + 1), col_ramp[i].position)
                                    setattr(color_params, 'tex%d_color' % (i + 1),
                                            (col_ramp[i].color[0], col_ramp[i].color[1], col_ramp[i].color[2]))
                                    setattr(alpha_params, 'tex%d_floatvalue' % (i + 1), col_ramp[i].color[3])

                            mix_params.amount_floattexturename = alpha_tex.name
                            mix_params.amount_multiplyfloat = True
                            mix_params.tex2_usecolortexture = True
                            mix_params.tex2_colortexturename = color_tex.name

                            if n == 0:
                                mix_params.tex1_color = blender_mat.diffuse_color

                            else:
                                mix_params.tex1_usecolortexture = True
                                mix_params.tex1_colortexturename = Lux_TexName[n - 1]
                        else:
                            # Add mix texture for blender internal textures
                            mix_tex_slot = blender_mat.texture_slots.add()
                            mix_tex_slot.use = True
                            mix_tex = mix_tex_slot.texture = bpy.data.textures.new('Lux::%s' % tex.name, 'NONE')
                            Lux_TexName.append(mix_tex.name)
                            mix_lux_tex = mix_tex.luxrender_texture
                            mix_lux_tex.type = 'mix'
                            mix_params = mix_lux_tex.luxrender_tex_mix
                            mix_params.variant = 'color'
                            mix_params.amount_floatvalue = dcf
                            mix_params.amount_usefloattexture = True
                            mix_params.amount_floattexturename = tex.name
                            mix_params.amount_multiplyfloat = True
                            mix_params.tex2_color = color
                            if n == 0:
                                mix_params.tex1_color = blender_mat.diffuse_color
                            else:
                                mix_params.tex1_usecolortexture = True
                                mix_params.tex1_colortexturename = Lux_TexName[n - 1]

                    luxmat.Kd_usecolortexture = True
                    luxmat.Kd_colortexturename = mix_tex.name

                pass
                # else:
                #luxmat.Kd_usecolortexture = False

        if luxrender_mat.type in ('glossy'):
            if len(Ks_stack) == 1:
                tex = Ks_stack[0][0]
                variant = tex.luxrender_texture.get_paramset(scene, tex)[0]
                if variant == 'color':
                    # assign the texture directly
                    luxmat.Ks_usecolortexture = True
                    luxmat.Ks_colortexturename = tex.name
                    luxmat.Ks_color = [i * Ks_stack[0][1] for i in luxmat.Ks_color]
                    luxmat.Ks_multiplycolor = True
                else:
                    # TODO - insert mix texture
                    # check there are enough free empty texture slots !
                    pass
            elif len(Ks_stack) > 1:
                # TODO - set up a mix stack.
                # check there are enough free empty texture slots !
                pass
            else:
                luxmat.Ks_usecolortexture = False

        if bump_tex is not None:
            tex = bump_tex[0]
            variant = tex.luxrender_texture.get_paramset(scene, tex)[0]
            if variant == 'float':
                luxrender_mat.bumpmap_usefloattexture = True
                luxrender_mat.bumpmap_floattexturename = tex.name
                luxrender_mat.bumpmap_floatvalue = bump_tex[1] / 50.0  # ASV
                luxrender_mat.bumpmap_multiplyfloat = True
            else:
                # TODO - insert mix texture
                # check there are enough free empty texture slots !
                pass
        else:
            luxrender_mat.bumpmap_floatvalue = 0.0
            luxrender_mat.bumpmap_usefloattexture = False

        report({'INFO'}, 'Converted blender material "%s"' % blender_mat.name)
        return {'FINISHED'}
    except Exception as err:
        report({'ERROR'}, 'Cannot convert material: %s' % err)
        # print('Material conversion failed on line %d' % err.__traceback__.tb_lineno)
        return {'CANCELLED'}

def cycles_converter(report, blender_mat):
    def get_linked_node(socket):
        if socket.is_linked:
            return socket.links[0].from_node
        else:
            return None

    def copy_socket_properties(lux_node, socket_index, linked_node=None, default_value=None):
        if linked_node is not None:
            # Create the link
            lux_nodetree.links.new(linked_node.outputs[0], lux_node.inputs[socket_index])
        elif default_value is not None:
            # Set default value of the socket
            lux_node.inputs[socket_index].default_value = default_value

    def convert_socket(socket, lux_nodetree):
        if socket.is_linked:
            node = socket.links[0].from_node
            # Get from_socket information, for nodes with multiple outputs (e.g. image map with color and alpha)
            from_socket = socket.links[0].from_socket
        elif hasattr(socket, 'default_value'):
            return None, socket.default_value
        else:
            # Sockets like NodeSocketShader do not have a default value
            return None, None

        lux_node = None

        if node.type == 'OUTPUT_MATERIAL':
            pass # Output is exported before iterative export

        ### Materials ###
        elif node.type == 'BSDF_DIFFUSE':
            lux_node = lux_nodetree.nodes.new('luxrender_material_matte_node')

            # Color
            linked_node, default_value = convert_socket(node.inputs['Color'], lux_nodetree)
            # The default value of a Cycles color is always RGBA, but we only need RGB
            default_value = default_value[:3] if default_value is not None else None
            copy_socket_properties(lux_node, 0, linked_node, default_value)

        elif node.type == 'BSDF_GLOSSY':
            lux_node = lux_nodetree.nodes.new('luxrender_material_metal2_node')

            # Color
            linked_node, default_value = convert_socket(node.inputs['Color'], lux_nodetree)
            # The default value of a Cycles color is always RGBA, but we only need RGB
            default_value = default_value[:3] if default_value is not None else None
            copy_socket_properties(lux_node, 0, linked_node, default_value)

            # Roughness
            linked_node, default_value = convert_socket(node.inputs['Roughness'], lux_nodetree)
            copy_socket_properties(lux_node, 2, linked_node, default_value)

        elif node.type == 'MIX_SHADER':
            amount_node = get_linked_node(node.inputs['Fac'])
            mat1_node = get_linked_node((node.inputs[1]))
            mat2_node = get_linked_node((node.inputs[2]))

            if (amount_node and mat1_node and mat2_node) and (
                    amount_node.type in ('FRESNEL', 'LAYER_WEIGHT') and
                    mat1_node.type == 'BSDF_DIFFUSE' and mat2_node.type == 'BSDF_GLOSSY'):
                # Create a LuxRender glossy material
                lux_node = lux_nodetree.nodes.new('luxrender_material_glossy_node')

                # Diffuse Color (from BSDF_DIFFUSE)
                linked_node, default_value = convert_socket(mat1_node.inputs['Color'], lux_nodetree)
                # The default value of a Cycles color is always RGBA, but we only need RGB
                default_value = default_value[:3] if default_value is not None else None
                copy_socket_properties(lux_node, 0, linked_node, default_value)

                # Roughness (from BSDF_GLOSSY)
                linked_node, default_value = convert_socket(mat2_node.inputs['Roughness'], lux_nodetree)
                copy_socket_properties(lux_node, 6, linked_node, default_value)
            else:
                # "Normal" mix material, no special treatment
                lux_node = lux_nodetree.nodes.new('luxrender_material_mix_node')
                # Amount
                linked_node_amount, default_value_amount = convert_socket(node.inputs['Fac'], lux_nodetree)
                copy_socket_properties(lux_node, 0, linked_node_amount, default_value_amount)
                # Material 1
                linked_node_1, default_value_1 = convert_socket(node.inputs[1], lux_nodetree)
                copy_socket_properties(lux_node, 1, linked_node_1, default_value_1)
                # Material 2
                linked_node_2, default_value_2 = convert_socket(node.inputs[2], lux_nodetree)
                copy_socket_properties(lux_node, 2, linked_node_2, default_value_2)

        elif node.type == 'BSDF_TRANSPARENT':
            if node.inputs['Color'].default_value[:3] == (1, 1, 1):
                # In Lux, we ohly have the Null materials as an equivalent to a fully transparent material
                lux_node = lux_nodetree.nodes.new('luxrender_material_null_node')
            # TODO: find an approximation to Cycles' transparent material with non-white colors

        ### Textures ###
        elif node.type == 'TEX_IMAGE':
            lux_node = lux_nodetree.nodes.new('luxrender_texture_blender_image_map_node')

            # Selected Blender image
            lux_node.image = node.image.name

            # Gamma (from color space)
            lux_node.gamma = 2.2 if node.color_space == 'COLOR' else 1

            # Alpha handling (if alpha output of TEX_IMAGE is used)
            if from_socket.name == 'Alpha':
                lux_node.channel = 'alpha'

        else:
            # In case of an unkown node, do nothing
            print('WARNING: Unsupported node type %s' % node.type)
            return None, None

        if lux_node:
            # Copy properties shared by all nodes
            lux_node.location = node.location

        return lux_node, None

    try:
        # Create Lux nodetree
        lux_nodetree = bpy.data.node_groups.new(blender_mat.name, type='luxrender_material_nodes')
        lux_nodetree.use_fake_user = True
        blender_mat.luxrender_material.nodetree = lux_nodetree.name

        # Find active Cycles output node
        output = None

        for node in blender_mat.node_tree.nodes:
            if node.type == 'OUTPUT_MATERIAL' and node.is_active_output:
                output = node
                break

        # Convert surface socket
        first_surface_node, default_value = convert_socket(output.inputs['Surface'], lux_nodetree)

        # Create Lux output node
        lux_output = lux_nodetree.nodes.new('luxrender_material_output_node')
        lux_output.location = output.location
        # Connect Lux output to first converted node
        lux_nodetree.links.new(first_surface_node.outputs[0], lux_output.inputs[0])

        report({'INFO'}, 'Converted Cycles nodetree "%s"' % blender_mat.node_tree.name)
        return {'FINISHED'}
    except Exception as err:
        report({'ERROR'}, 'Cannot convert nodetree "%s": %s' % (blender_mat.node_tree.name, err))
        import traceback
        traceback.print_exc()
        return {'CANCELLED'}


@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_material_reset(bpy.types.Operator):
    bl_idname = 'luxrender.material_reset'
    bl_label = 'Reset material to defaults'

    def execute(self, context):
        if context.material and hasattr(context.material, 'luxrender_material'):
            context.material.luxrender_material.reset(prnt=context.material)
        return {'FINISHED'}


@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_convert_all_materials(bpy.types.Operator):
    bl_idname = 'luxrender.convert_all_materials'
    bl_label = 'Convert all Blender materials'

    def report_log(self, level, msg):
        LuxLog('Material conversion %s: %s' % (level, msg))

    def execute(self, context):
        for blender_mat in bpy.data.materials:
            # Don't convert materials from linked-in files
            if blender_mat.library is None:
                if blender_mat.node_tree:
                    if not (hasattr(blender_mat, 'luxrender_material') and blender_mat.luxrender_material.nodetree):
                        # Cycles nodetree available and no Lux nodetree yet
                        cycles_converter(self.report_log, blender_mat)
                else:
                    material_converter(self.report_log, context.scene, blender_mat)

        return {'FINISHED'}


@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_convert_material(bpy.types.Operator):
    bl_idname = 'luxrender.convert_material'
    bl_label = 'Convert selected Blender material'

    material_name = bpy.props.StringProperty(default='')

    def execute(self, context):
        if not self.properties.material_name:
            blender_mat = context.material
        else:
            blender_mat = bpy.data.materials[self.properties.material_name]

        if blender_mat.node_tree:
            # Cycles nodetree present
            cycles_converter(self.report, blender_mat)
        else:
            material_converter(self.report, context.scene, blender_mat)

        return {'FINISHED'}


@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_material_copy(bpy.types.Operator):
    bl_idname = 'luxrender.material_copy'
    bl_label = 'Copy'
    bl_description = 'Create a copy of the material (also copying the nodetree)'

    def execute(self, context):
        current_mat = context.active_object.active_material

        # Create a copy of the material
        new_mat = current_mat.copy()

        current_nodetree_name = current_mat.luxrender_material.nodetree

        if current_nodetree_name in bpy.data.node_groups:
            current_nodetree = bpy.data.node_groups[current_nodetree_name]
            # Create a copy of the nodetree as well
            new_nodetree = current_nodetree.copy()
            # Assign new nodetree to the new material
            new_mat.luxrender_material.nodetree = new_nodetree.name

        context.active_object.active_material = new_mat

        return {'FINISHED'}