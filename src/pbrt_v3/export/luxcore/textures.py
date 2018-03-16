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

import bpy, math, mathutils, os, tempfile

from ...extensions_framework import util as efutil
from ...outputs.pbrtv3core_api import pypbrtv3core
from ...outputs.pbrtv3core_api import ToValidPBRTv3CoreName
from ...export import matrix_to_list
from ...export import get_expanded_file_name
from ...export.volumes import SmokeCache

from .utils import convert_texture_channel


class TextureExporter(object):
    def __init__(self, pbrtv3core_exporter, blender_scene, texture):
        self.pbrtv3core_exporter = pbrtv3core_exporter
        self.blender_scene = blender_scene
        self.texture = texture

        self.properties = pypbrtv3core.Properties()
        self.pbrtv3core_name = ''


    def convert(self, name=''):
        # Remove old properties
        self.properties = pypbrtv3core.Properties()

        self.__convert_texture(name)

        return self.properties


    def __convert_mapping(self, prefix, texture):
        # Note 2DMapping is used for: bilerp, checkerboard(dimension == 2), dots, imagemap, normalmap, uv, uvmask
        # Blender - image
        pbrtv3Mapping = getattr(texture.pbrtv3_texture, 'pbrtv3_tex_mapping')

        if pbrtv3Mapping.type == 'uv':
            self.properties.Set(pypbrtv3core.Property(prefix + '.mapping.type', 'uvmapping2d'))
            self.properties.Set(
                pypbrtv3core.Property(prefix + '.mapping.uvscale', [pbrtv3Mapping.uscale, pbrtv3Mapping.vscale * - 1.0]))

            if not pbrtv3Mapping.center_map:
                self.properties.Set(
                    pypbrtv3core.Property(prefix + '.mapping.uvdelta', [pbrtv3Mapping.udelta, pbrtv3Mapping.vdelta + 1.0]))
            else:
                self.properties.Set(pypbrtv3core.Property(prefix + '.mapping.uvdelta', [
                    pbrtv3Mapping.udelta + 0.5 * (1.0 - pbrtv3Mapping.uscale),
                    pbrtv3Mapping.vdelta * - 1.0 + 1.0 - (0.5 * (1.0 - pbrtv3Mapping.vscale))]))
        else:
            raise Exception('Unsupported mapping for texture: ' + texture.name)


    def __convert_transform(self, prefix, texture):
        # Note 3DMapping is used for: brick, checkerboard(dimension == 3), cloud', densitygrid,
        # exponential, fbm', marble', windy, wrinkled
        # BLENDER - CLOUDS,DISTORTED_NOISE,MAGIC,MARBLE, MUSGRAVE,STUCCI,VORONOI, WOOD
        pbrtv3Transform = getattr(texture.pbrtv3_texture, 'pbrtv3_tex_transform')

        if pbrtv3Transform.coordinates == 'uv':
            self.properties.Set(pypbrtv3core.Property(prefix + '.mapping.type', 'uvmapping3d'))
        elif pbrtv3Transform.coordinates == 'global':
            self.properties.Set(pypbrtv3core.Property(prefix + '.mapping.type', 'globalmapping3d'))
        elif pbrtv3Transform.coordinates == 'local':
            self.properties.Set(pypbrtv3core.Property(prefix + '.mapping.type', 'localmapping3d'))
        elif pbrtv3Transform.coordinates == 'smoke_domain':
            self.properties.Set(pypbrtv3core.Property(prefix + '.mapping.type', 'globalmapping3d'))            
        else:
            raise Exception('Unsupported mapping "%s" for texture "%s"' % (pbrtv3Transform.coordinates, texture.name))

        if pbrtv3Transform.coordinates == 'smoke_domain':
            #For correct densitygrid texture transformation use smoke domain bounding box
            tex = texture.pbrtv3_texture.pbrtv3_tex_densitygrid
            obj = bpy.context.scene.objects[tex.domain_object]
            
            pbrtv3Scale = obj.dimensions
            pbrtv3Translate = obj.matrix_world * mathutils.Vector([v for v in obj.bound_box[0]])
            pbrtv3Rotate = obj.rotation_euler
        else:
            pbrtv3Translate = getattr(texture.pbrtv3_texture.pbrtv3_tex_transform, 'translate')
            pbrtv3Scale = getattr(texture.pbrtv3_texture.pbrtv3_tex_transform, 'scale')
            pbrtv3Rotate = getattr(texture.pbrtv3_texture.pbrtv3_tex_transform, 'rotate')

        # create a location matrix
        tex_loc = mathutils.Matrix.Translation((pbrtv3Translate))

        # create an identitiy matrix
        tex_sca = mathutils.Matrix()
        tex_sca[0][0] = pbrtv3Scale[0]  # X
        tex_sca[1][1] = pbrtv3Scale[1]  # Y
        tex_sca[2][2] = pbrtv3Scale[2]  # Z

        # create a rotation matrix
        tex_rot0 = mathutils.Matrix.Rotation(math.radians(pbrtv3Rotate[0]), 4, 'X')
        tex_rot1 = mathutils.Matrix.Rotation(math.radians(pbrtv3Rotate[1]), 4, 'Y')
        tex_rot2 = mathutils.Matrix.Rotation(math.radians(pbrtv3Rotate[2]), 4, 'Z')
        tex_rot = tex_rot0 * tex_rot1 * tex_rot2

        # combine transformations
        f_matrix = matrix_to_list(tex_loc * tex_rot * tex_sca, apply_worldscale=True, invert=True)

        self.properties.Set(pypbrtv3core.Property(prefix + '.mapping.transformation', f_matrix))


    def __convert_colorramp(self):
        if self.texture.use_color_ramp:
            ramp = self.texture.color_ramp
            ramp_pbrtv3core_name = self.pbrtv3core_name + '_colorramp'
            ramp_prefix = 'scene.textures.' + ramp_pbrtv3core_name

            self.properties.Set(pypbrtv3core.Property(ramp_prefix + '.type', 'band'))
            self.properties.Set(pypbrtv3core.Property(ramp_prefix + '.amount', self.pbrtv3core_name))
            self.properties.Set(pypbrtv3core.Property(ramp_prefix + '.offsets', len(ramp.elements)))

            if ramp.interpolation == 'CONSTANT':
                interpolation = 'none'
            elif ramp.interpolation == 'LINEAR':
                interpolation = 'linear'
            else:
                interpolation = 'cubic'

            self.properties.Set(pypbrtv3core.Property(ramp_prefix + '.interpolation', interpolation))

            for i in range(len(ramp.elements)):
                position = ramp.elements[i].position
                color = list(ramp.elements[i].color[:3])  # Ignore alpha
                self.properties.Set(pypbrtv3core.Property(ramp_prefix + '.offset%d' % i, position))
                self.properties.Set(pypbrtv3core.Property(ramp_prefix + '.value%d' % i, color))

            self.pbrtv3core_name = ramp_pbrtv3core_name


    def __generate_texture_name(self, name):
        if self.texture.library:
            name += '_' + self.texture.library.name

        self.pbrtv3core_name = ToValidPBRTv3CoreName(name)


    def __convert_texture(self, name=''):
        texture = self.texture

        texType = texture.pbrtv3_texture.type

        if name == '':
            self.__generate_texture_name(texture.name)
        else:
            self.__generate_texture_name(name)

        prefix = 'scene.textures.' + self.pbrtv3core_name

        if texType == 'BLENDER':
            bl_texType = getattr(texture, 'type')

            # ###################################################################
            # BLEND
            ####################################################################
            if bl_texType == 'BLEND':
                self.properties.Set(pypbrtv3core.Property(prefix + '.type', ['blender_blend']))
                self.properties.Set(pypbrtv3core.Property(prefix + '.progressiontype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'progression'))))
                self.properties.Set(pypbrtv3core.Property(prefix + '.direction',
                                             ''.join(str(i).lower() for i in getattr(texture, 'use_flip_axis'))))
            ####################################################################
            # CLOUDS
            ####################################################################
            elif bl_texType == 'CLOUDS':
                self.properties.Set(pypbrtv3core.Property(prefix + '.type', ['blender_clouds']))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisetype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_type'))))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisebasis',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_basis'))))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisedepth', [float(texture.noise_depth)]))
            ####################################################################
            # Distorted Noise
            ####################################################################
            elif bl_texType == 'DISTORTED_NOISE':
                self.properties.Set(pypbrtv3core.Property(prefix + '.type', ['blender_distortednoise']))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noise_distortion',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_distortion'))))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisebasis',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_basis'))))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.distortion', [float(texture.distortion)]))
            ####################################################################
            # IMAGE/MOVIE/SEQUENCE
            ####################################################################
            elif bl_texType == 'IMAGE' and texture.image and texture.image.source in ['GENERATED', 'FILE', 'SEQUENCE']:
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                tex_image = temp_file.name

                if texture.image.source == 'GENERATED':
                    texture.image.save_render(tex_image, self.blender_scene)

                if texture.image.source == 'FILE':
                    if texture.image.packed_file:
                        texture.image.save_render(tex_image, self.blender_scene)
                    else:
                        if texture.library is not None:
                            f_path = efutil.filesystem_path(
                                bpy.path.abspath(texture.image.filepath, texture.library.filepath))
                        else:
                            f_path = efutil.filesystem_path(texture.image.filepath)

                        if not os.path.exists(f_path):
                            raise Exception(
                                'Image referenced in blender texture %s doesn\'t exist: %s' % (texture.name, f_path))

                        tex_image = efutil.filesystem_path(f_path)

                if texture.image.source == 'SEQUENCE':
                    if texture.image.packed_file:
                        tex_image = 'pbrtv3blend_extracted_image_%s.%s' % (
                            bpy.path.clean_name(texture.name), self.blender_scene.render.image_settings.file_format)
                        tex_image = os.path.join(extract_path, tex_image)
                        texture.image.save_render(tex_image, self.blender_scene)
                    else:
                        # sequence params from blender
                        # remove tex_preview extension to avoid error
                        sequence = bpy.data.textures[(texture.name).replace('.001', '')].image_user
                        seqframes = sequence.frame_duration
                        seqoffset = sequence.frame_offset
                        seqstartframe = sequence.frame_start  # the global frame at which the imagesequence starts
                        seqcyclic = sequence.use_cyclic
                        currentframe = self.blender_scene.frame_current

                        if texture.library is not None:
                            f_path = efutil.filesystem_path(
                                bpy.path.abspath(texture.image.filepath, texture.library.filepath))
                        else:
                            f_path = efutil.filesystem_path(texture.image.filepath)

                        if currentframe < seqstartframe:
                            fnumber = 1 + seqoffset
                        else:
                            fnumber = currentframe - (seqstartframe - 1) + seqoffset

                        if fnumber > seqframes:
                            if not seqcyclic:
                                fnumber = seqframes
                            else:
                                fnumber = (currentframe - (seqstartframe - 1)) % seqframes
                                if fnumber == 0:
                                    fnumber = seqframes

                        import re

                        def get_seq_filename(number, f_path):
                            m = re.findall(r'(\d+)', f_path)
                            if len(m) == 0:
                                return 'ERR: Can\'t find pattern'

                            rightmost_number = m[len(m) - 1]
                            seq_length = len(rightmost_number)

                            nstr = '%i' % number
                            new_seq_number = nstr.zfill(seq_length)

                            return f_path.replace(rightmost_number, new_seq_number)

                        f_path = get_seq_filename(fnumber, f_path)

                        if not os.path.exists(f_path):
                            raise Exception(
                                'Image referenced in blender texture %s doesn\'t exist: %s' % (texture.name, f_path))
                        tex_image = efutil.filesystem_path(f_path)


                gamma = texture.pbrtv3_texture.pbrtv3_tex_imagesampling.gamma
                gain = texture.pbrtv3_texture.pbrtv3_tex_imagesampling.gain
                channel = texture.pbrtv3_texture.pbrtv3_tex_imagesampling.channel_pbrtv3core

                self.properties.Set(pypbrtv3core.Property(prefix + '.type', ['imagemap']))
                self.properties.Set(pypbrtv3core.Property(prefix + '.file', [tex_image]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.gamma', gamma))
                self.properties.Set(pypbrtv3core.Property(prefix + '.gain', gain))
                self.properties.Set(pypbrtv3core.Property(prefix + '.channel', channel))

                self.__convert_mapping(prefix, texture)
            ####################################################################
            # MAGIC
            ####################################################################
            elif bl_texType == 'MAGIC':
                self.properties.Set(pypbrtv3core.Property(prefix + '.type', ['blender_magic']))
                self.properties.Set(pypbrtv3core.Property(prefix + '.turbulence', [float(texture.turbulence)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisedepth', [float(texture.noise_depth)]))
            ####################################################################
            # MARBLE
            ####################################################################
            elif bl_texType == 'MARBLE':
                self.properties.Set(pypbrtv3core.Property(prefix + '.type', ['blender_marble']))
                self.properties.Set(pypbrtv3core.Property(prefix + '.marbletype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'marble_type'))))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisebasis',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_basis'))))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisebasis2',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_basis_2'))))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisedepth', [float(texture.noise_depth)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.turbulence', [float(texture.turbulence)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisetype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_type'))))
            ####################################################################
            # MUSGRAVE
            ####################################################################
            elif bl_texType == 'MUSGRAVE':
                self.properties.Set(pypbrtv3core.Property(prefix + '.type', ['blender_musgrave']))
                self.properties.Set(pypbrtv3core.Property(prefix + '.musgravetype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'musgrave_type'))))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisebasis',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_basis'))))
                self.properties.Set(pypbrtv3core.Property(prefix + '.dimension', [float(texture.dimension_max)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.intensity', [float(texture.noise_intensity)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.lacunarity', [float(texture.lacunarity)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.offset', [float(texture.offset)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.gain', [float(texture.gain)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.octaves', [float(texture.octaves)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.dimension', [float(texture.noise_scale)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
            # Not in blender:
            # self.properties.Set(pypbrtv3core.Property(prefix + '.noisetype', ''.join(str(i).lower() for i in getattr(texture, 'noise_type'))))
            ####################################################################
            # NOISE
            ####################################################################
            elif bl_texType == 'NOISE':
                self.properties.Set(pypbrtv3core.Property(prefix + '.type', ['blender_noise']))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisedepth', [float(texture.noise_depth)]))
            ####################################################################
            # STUCCI
            ####################################################################
            elif bl_texType == 'STUCCI':
                self.properties.Set(pypbrtv3core.Property(prefix + '.type', ['blender_stucci']))
                self.properties.Set(pypbrtv3core.Property(prefix + '.stuccitype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'stucci_type'))))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisebasis',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_basis'))))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisetype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_type'))))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.turbulence', [float(texture.turbulence)]))
            ####################################################################
            # VORONOI
            ####################################################################
            elif bl_texType == 'VORONOI':
                self.properties.Set(pypbrtv3core.Property(prefix + '.type', ['blender_voronoi']))
                self.properties.Set(pypbrtv3core.Property(prefix + '.dismetric',
                                             ''.join(str(i).lower() for i in getattr(texture, 'distance_metric'))))
                # Not yet in pbrtv3core:
                #self.properties.Set(pypbrtv3core.Property(prefix + '.colormode', ''.join(str(i).lower() for i in getattr(texture, 'color_mode'))))
                self.properties.Set(pypbrtv3core.Property(prefix + '.intensity', [float(texture.noise_intensity)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.exponent', [float(texture.minkovsky_exponent)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.w1', [float(texture.weight_1)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.w2', [float(texture.weight_2)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.w3', [float(texture.weight_3)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.w4', [float(texture.weight_4)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
            ####################################################################
            # WOOD
            ####################################################################
            elif bl_texType == 'WOOD':
                self.properties.Set(pypbrtv3core.Property(prefix + '.type', ['blender_wood']))
                self.properties.Set(pypbrtv3core.Property(prefix + '.woodtype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'wood_type'))))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisebasis2',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_basis_2'))))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisetype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_type'))))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.turbulence', [float(texture.turbulence)]))
            ####################################################################
            # Parameters shared by all blender textures
            ####################################################################
            if bl_texType != 'IMAGE':
                # bright/contrast are not supported by PBRTv3Core imagemaps
                self.properties.Set(pypbrtv3core.Property(prefix + '.bright', [float(texture.intensity)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.contrast', [float(texture.contrast)]))
                self.__convert_transform(prefix, texture)

            self.__convert_colorramp()
            return

        elif texType != 'BLENDER':
            pbrtv3Tex = getattr(texture.pbrtv3_texture, 'pbrtv3_tex_' + texType)

            ####################################################################
            # ADD/SUBTRACT
            ####################################################################
            if texType in ('add', 'subtract'):
                tex1 = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'tex1', pbrtv3Tex.variant)
                tex2 = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'tex2', pbrtv3Tex.variant)
                self.properties.Set(pypbrtv3core.Property(prefix + '.texture1', tex1))
                self.properties.Set(pypbrtv3core.Property(prefix + '.texture2', tex2))
            ####################################################################
            # BAND
            ####################################################################
            elif texType == 'band':
                if pbrtv3Tex.variant != 'fresnel':
                    amount = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'amount', 'float')
                    # Create all sub-texture definitions before the band texture definition
                    values = []
                    for i in range(pbrtv3Tex.noffsets):
                        values.append(convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'tex%s' % str(i + 1), pbrtv3Tex.variant))

                    self.properties.Set(pypbrtv3core.Property(prefix + '.amount', amount))
                    self.properties.Set(pypbrtv3core.Property(prefix + '.offsets', [(pbrtv3Tex.noffsets)]))

                    for i in range(pbrtv3Tex.noffsets):
                        self.properties.Set(pypbrtv3core.Property(prefix + '.offset%d' % i,
                                                     [float(getattr(pbrtv3Tex, 'offset%s%s' % (pbrtv3Tex.variant, str(i + 1))))]))

                        value = values[i]

                        if isinstance(value, str):
                            # PBRTv3Core currently does not support textured values, set color to black
                            print('WARNING: PBRTv3Core does not support textured values in the band texture, '
                                  'using black color instead (texture: "%s")' % texture.name)
                            value = [0] * 3

                        if len(value) == 1:
                            value = [value[0]] * 3

                        self.properties.Set(pypbrtv3core.Property(prefix + '.value%d' % i, value))
                        i += 1
                else:
                    print('WARNING: Unsupported variant %s for texture: %s' % (pbrtv3Tex.variant, texture.name))
            ####################################################################
            # BLACKBODY
            ####################################################################
            elif texType == 'blackbody':
                self.properties.Set(pypbrtv3core.Property(prefix + '.temperature', [float(pbrtv3Tex.temperature)]))
            ####################################################################
            # Brick
            ####################################################################
            elif texType == 'brick':
                bricktex = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'bricktex', pbrtv3Tex.variant)
                brickmodtex = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'brickmodtex', pbrtv3Tex.variant)
                mortartex = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'mortartex', pbrtv3Tex.variant)

                self.properties.Set(pypbrtv3core.Property(prefix + '.brickbond', [(pbrtv3Tex.brickbond)]))

                if texture.pbrtv3_texture.pbrtv3_tex_brick.brickbond in ('running', 'flemish'):
                    self.properties.Set(pypbrtv3core.Property(prefix + '.brickrun', [float(pbrtv3Tex.brickrun)]))

                self.properties.Set(pypbrtv3core.Property(prefix + '.mortarsize', [float(pbrtv3Tex.mortarsize)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.brickwidth', [float(pbrtv3Tex.brickwidth)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.brickdepth', [float(pbrtv3Tex.brickdepth)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.brickheight', [float(pbrtv3Tex.brickheight)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.bricktex', bricktex))
                self.properties.Set(pypbrtv3core.Property(prefix + '.brickmodtex', brickmodtex))
                self.properties.Set(pypbrtv3core.Property(prefix + '.mortartex', mortartex))
                self.__convert_transform(prefix, texture)
            ####################################################################
            # CHECKERBOARD
            ####################################################################
            elif texType == 'checkerboard':
                # self.properties.Set(pypbrtv3core.Property(prefix + '.aamode', [float(pbrtv3Tex.aamode)])) # not yet in pbrtv3core
                tex1 = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'tex1', 'float')
                tex2 = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'tex2', 'float')
                self.properties.Set(pypbrtv3core.Property(prefix + '.texture1', tex1))
                self.properties.Set(pypbrtv3core.Property(prefix + '.texture2', tex2))
                if texture.pbrtv3_texture.pbrtv3_tex_checkerboard.dimension == 2:
                    self.properties.Set(pypbrtv3core.Property(prefix + '.type', ['checkerboard2d']))
                    self.__convert_mapping(prefix, texture)
                else:
                    self.properties.Set(pypbrtv3core.Property(prefix + '.type', ['checkerboard3d']))
                    self.__convert_transform(prefix, texture)
            ####################################################################
            # CLOUD
            ####################################################################
            elif texType == 'cloud':
                self.properties.Set(pypbrtv3core.Property(prefix + '.radius', [float(pbrtv3Tex.radius)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noisescale', [float(pbrtv3Tex.noisescale)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.turbulence', [float(pbrtv3Tex.turbulence)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.sharpness', [float(pbrtv3Tex.sharpness)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.noiseoffset', [float(pbrtv3Tex.noiseoffset)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.spheres', [pbrtv3Tex.spheres]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.octaves', [pbrtv3Tex.octaves]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.omega', [float(pbrtv3Tex.omega)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.variability', [float(pbrtv3Tex.variability)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.baseflatness', [float(pbrtv3Tex.baseflatness)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.spheresize', [float(pbrtv3Tex.spheresize)]))
                self.__convert_transform(prefix, texture)
            ####################################################################
            # CONSTANT
            ####################################################################
            elif texType == 'constant':
                if pbrtv3Tex.variant == 'color':
                    self.properties.Set(pypbrtv3core.Property(prefix + '.type', ['constfloat3']))
                    self.properties.Set(pypbrtv3core.Property(prefix + '.value',
                                                 [pbrtv3Tex.colorvalue[0], pbrtv3Tex.colorvalue[1], pbrtv3Tex.colorvalue[2]]))
                elif pbrtv3Tex.variant == 'float':
                    self.properties.Set(pypbrtv3core.Property(prefix + '.type', ['constfloat1']))
                    self.properties.Set(pypbrtv3core.Property(prefix + '.value', [float(pbrtv3Tex.floatvalue)]))
                else:
                    print('WARNING: Unsupported variant %s for texture: %s' % (pbrtv3Tex.variant, texture.name))
            ####################################################################
            # DOTS
            ####################################################################
            elif texType == 'dots':
                inside = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'inside', 'float')
                outside = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'outside', 'float')
                self.properties.Set(pypbrtv3core.Property(prefix + '.inside', inside))
                self.properties.Set(pypbrtv3core.Property(prefix + '.outside', outside))
                self.__convert_mapping(prefix, texture)
            ####################################################################
            # FBM
            ####################################################################
            elif texType == 'fbm':
                self.properties.Set(pypbrtv3core.Property(prefix + '.octaves', [float(pbrtv3Tex.octaves)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.roughness', [float(pbrtv3Tex.roughness)]))
                self.__convert_transform(prefix, texture)
            ####################################################################
            # IMAGEMAP
            ####################################################################
            elif texType == 'imagemap':
                full_name, base_name = get_expanded_file_name(texture, pbrtv3Tex.filename)
                self.properties.Set(pypbrtv3core.Property(prefix + '.file', full_name))
                self.properties.Set(pypbrtv3core.Property(prefix + '.gamma', [float(pbrtv3Tex.gamma)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.gain', [float(pbrtv3Tex.gain)]))
                if pbrtv3Tex.variant == 'float':
                    self.properties.Set(pypbrtv3core.Property(prefix + '.channel', [(pbrtv3Tex.channel)]))
                self.__convert_mapping(prefix, texture)
            ####################################################################
            # LAMPSPECTRUM
            ####################################################################
            elif texType == 'lampspectrum':
                self.properties.Set(pypbrtv3core.Property(prefix + '.name', [pbrtv3Tex.preset]))
            ####################################################################
            # Normalmap
            ####################################################################
            elif texType == 'normalmap':
                full_name, base_name = get_expanded_file_name(texture, pbrtv3Tex.filename)
                self.properties.Set(pypbrtv3core.Property(prefix + '.file', full_name))
                self.__convert_mapping(prefix, texture)
            ####################################################################
            # Marble
            ####################################################################
            elif texType == 'marble':
                self.properties.Set(pypbrtv3core.Property(prefix + '.octaves', [float(pbrtv3Tex.octaves)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.roughness', [float(pbrtv3Tex.roughness)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.scale', [float(pbrtv3Tex.scale)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.variation', [float(pbrtv3Tex.variation)]))
                self.__convert_transform(prefix, texture)
            ####################################################################
            # Mix
            ####################################################################
            elif texType == 'mix':
                amount = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'amount', 'float')
                tex1 = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'tex1', pbrtv3Tex.variant)
                tex2 = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'tex2', pbrtv3Tex.variant)

                self.properties.Set(pypbrtv3core.Property(prefix + '.amount', amount))
                self.properties.Set(pypbrtv3core.Property(prefix + '.texture1', tex1))
                self.properties.Set(pypbrtv3core.Property(prefix + '.texture2', tex2))
            ####################################################################
            # Scale
            ####################################################################
            elif texType == 'scale':
                tex1 = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'tex1', pbrtv3Tex.variant)
                tex2 = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'tex2', pbrtv3Tex.variant)
                self.properties.Set(pypbrtv3core.Property(prefix + '.texture1', tex1))
                self.properties.Set(pypbrtv3core.Property(prefix + '.texture2', tex2))
            ####################################################################
            # UV
            ####################################################################
            elif texType == 'uv':
                self.__convert_mapping(prefix, texture)
            ####################################################################
            # WINDY
            ####################################################################
            elif texType == 'windy':
                self.__convert_transform(prefix, texture)
            ####################################################################
            # WRINKLED
            ####################################################################
            elif texType == 'wrinkled':
                self.properties.Set(pypbrtv3core.Property(prefix + '.octaves', [float(pbrtv3Tex.octaves)]))
                self.properties.Set(pypbrtv3core.Property(prefix + '.roughness', [float(pbrtv3Tex.roughness)]))
                self.__convert_transform(prefix, texture)
            ####################################################################
            # Vertex Colors
            ####################################################################
            elif texType in ['hitpointcolor', 'hitpointgrey', 'hitpointalpha']:
                pass
            ####################################################################
            # Fresnel color
            ####################################################################
            elif texType == 'fresnelcolor':
                self.properties.Set(pypbrtv3core.Property(prefix + '.kr', convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'Kr', 'color')))
            ####################################################################
            # Fresnel preset (name)
            ####################################################################
            elif texType == 'fresnelname':
                self.properties.Set(pypbrtv3core.Property(prefix + '.type', 'fresnelpreset'))
                self.properties.Set(pypbrtv3core.Property(prefix + '.name', pbrtv3Tex.name))
            ####################################################################
            # Fresnel sopra
            ####################################################################
            elif texType == 'sopra':
                self.properties.Set(pypbrtv3core.Property(prefix + '.type', 'fresnelsopra'))
                full_name, base_name = get_expanded_file_name(texture, pbrtv3Tex.filename)
                self.properties.Set(pypbrtv3core.Property(prefix + '.file', full_name))
            ####################################################################
            # Fresnel pbrtv3pop
            ####################################################################
            elif texType == 'pbrtv3pop':
                self.properties.Set(pypbrtv3core.Property(prefix + '.type', 'fresnelpbrtv3pop'))
                full_name, base_name = get_expanded_file_name(texture, pbrtv3Tex.filename)
                self.properties.Set(pypbrtv3core.Property(prefix + '.file', full_name))
            ####################################################################
            # Pointiness (hitpointalpha texture behind the scenes, just that it
            #            implicitly enables pointiness calculation on the mesh)
            ####################################################################
            elif texType == 'pointiness':
                self.properties.Set(pypbrtv3core.Property(prefix + '.type', 'hitpointalpha'))

                if pbrtv3Tex.curvature_mode == 'both':
                    name_abs = self.pbrtv3core_name + '_abs'
                    self.properties.Set(pypbrtv3core.Property('scene.textures.' + name_abs + '.type', 'abs'))
                    self.properties.Set(pypbrtv3core.Property('scene.textures.' + name_abs + '.texture', self.pbrtv3core_name))

                    self.pbrtv3core_name = name_abs

                elif pbrtv3Tex.curvature_mode == 'concave':
                    name_clamp = self.pbrtv3core_name + '_clamp'
                    self.properties.Set(pypbrtv3core.Property('scene.textures.' + name_clamp + '.type', 'clamp'))
                    self.properties.Set(pypbrtv3core.Property('scene.textures.' + name_clamp + '.texture', self.pbrtv3core_name))
                    self.properties.Set(pypbrtv3core.Property('scene.textures.' + name_clamp + '.min', 0.0))
                    self.properties.Set(pypbrtv3core.Property('scene.textures.' + name_clamp + '.max', 1.0))

                    self.pbrtv3core_name = name_clamp

                elif pbrtv3Tex.curvature_mode == 'convex':
                    name_flip = self.pbrtv3core_name + '_flip'
                    self.properties.Set(pypbrtv3core.Property('scene.textures.' + name_flip + '.type', 'scale'))
                    self.properties.Set(pypbrtv3core.Property('scene.textures.' + name_flip + '.texture1', self.pbrtv3core_name))
                    self.properties.Set(pypbrtv3core.Property('scene.textures.' + name_flip + '.texture2', -1.0))

                    name_clamp = self.pbrtv3core_name + '_clamp'
                    self.properties.Set(pypbrtv3core.Property('scene.textures.' + name_clamp + '.type', 'clamp'))
                    self.properties.Set(pypbrtv3core.Property('scene.textures.' + name_clamp + '.texture', name_flip))
                    self.properties.Set(pypbrtv3core.Property('scene.textures.' + name_clamp + '.min', 0.0))
                    self.properties.Set(pypbrtv3core.Property('scene.textures.' + name_clamp + '.max', 1.0))

                    self.pbrtv3core_name = name_clamp
            ####################################################################
            # Densitygrid
            ####################################################################
            elif texType == 'densitygrid':
                self.properties.Set(pypbrtv3core.Property(prefix + '.wrap', pbrtv3Tex.wrapping))

                if SmokeCache.needs_update(self.blender_scene, pbrtv3Tex.domain_object, pbrtv3Tex.source):
                    grid = SmokeCache.convert(self.blender_scene, pbrtv3Tex.domain_object, pbrtv3Tex.source)
                    self.properties.Set(pypbrtv3core.Property(prefix + '.data', grid[3]))
                    self.properties.Set(pypbrtv3core.Property(prefix + '.nx', int(grid[0])))
                    self.properties.Set(pypbrtv3core.Property(prefix + '.ny', int(grid[1])))
                    self.properties.Set(pypbrtv3core.Property(prefix + '.nz', int(grid[2])))

                self.__convert_transform(prefix, texture)
            ####################################################################
            # HSV
            ####################################################################
            elif texType == 'hsv':
                input = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'input', 'color')
                hue = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'hue', 'float')
                saturation = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'saturation', 'float')
                value = convert_texture_channel(self.pbrtv3core_exporter, self.properties, self.pbrtv3core_name, pbrtv3Tex, 'value', 'float')

                self.properties.Set(pypbrtv3core.Property(prefix + '.texture', input))
                self.properties.Set(pypbrtv3core.Property(prefix + '.hue', hue))
                self.properties.Set(pypbrtv3core.Property(prefix + '.saturation', saturation))
                self.properties.Set(pypbrtv3core.Property(prefix + '.value', value))
            ####################################################################
            # Fallback to exception
            ####################################################################
            else:
                raise Exception('Unknown type ' + texType + ' for texture: ' + texture.name)

            if texType not in ('normalmap', 'checkerboard', 'constant', 'fresnelname', 'pbrtv3pop', 'sopra', 'pointiness'):
                self.properties.Set(pypbrtv3core.Property(prefix + '.type', texType))

            self.__convert_colorramp()
            return

        raise Exception('Unknown texture type: ' + texture.name)