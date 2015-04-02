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

from ...extensions_framework import util as efutil
from ...outputs.luxcore_api import pyluxcore
from ...outputs.luxcore_api import ToValidLuxCoreName

from . import convert_texture_channel


# TODO: port texture stuff to new interface


class TextureExporter(object):
    def __init__(self, luxcore_exporter, blender_scene, texture):
        self.luxcore_exporter = luxcore_exporter
        self.blender_scene = blender_scene
        self.texture = texture

        self.properties = pyluxcore.Properties()
        self.luxcore_name = ''


    def convert(self):
        # Remove old properties
        self.properties = pyluxcore.Properties()

        # Debug test
        self.properties.Set(pyluxcore.Property('scene.textures.test_tex.type', 'blender_clouds'))
        self.luxcore_name = 'test_tex'

        #self.luxcore_texture_name = self.ConvertTexture(self.texture)

        return self.properties


    def ConvertMapping(self, prefix, texture):
        # Note 2DMapping is used for: bilerp, checkerboard(dimension == 2), dots, imagemap, normalmap, uv, uvmask
        # Blender - image
        luxMapping = getattr(texture.luxrender_texture, 'luxrender_tex_mapping')

        if luxMapping.type == 'uv':
            self.scnProps.Set(pyluxcore.Property(prefix + '.mapping.type', ['uvmapping2d']))
            self.scnProps.Set(
                pyluxcore.Property(prefix + '.mapping.uvscale', [luxMapping.uscale, luxMapping.vscale * - 1.0]))

            if not luxMapping.center_map:
                self.scnProps.Set(
                    pyluxcore.Property(prefix + '.mapping.uvdelta', [luxMapping.udelta, luxMapping.vdelta + 1.0]))
            else:
                self.scnProps.Set(pyluxcore.Property(prefix + '.mapping.uvdelta', [
                    luxMapping.udelta + 0.5 * (1.0 - luxMapping.uscale),
                    luxMapping.vdelta * - 1.0 + 1.0 - (0.5 * (1.0 - luxMapping.vscale))]))
        else:
            raise Exception('Unsupported mapping for texture: ' + texture.name)


    def ConvertTransform(self, prefix, texture):
        # Note 3DMapping is used for: brick, checkerboard(dimension == 3), cloud', densitygrid,
        # exponential, fbm', marble', windy, wrinkled
        # BLENDER - CLOUDS,DISTORTED_NOISE,MAGIC,MARBLE, MUSGRAVE,STUCCI,VORONOI, WOOD
        luxTransform = getattr(texture.luxrender_texture, 'luxrender_tex_transform')

        if luxTransform.coordinates == 'uv':
            self.scnProps.Set(pyluxcore.Property(prefix + '.mapping.type', ['uvmapping3d']))
        elif luxTransform.coordinates == 'global':
            self.scnProps.Set(pyluxcore.Property(prefix + '.mapping.type', ['globalmapping3d']))
        else:
            raise Exception('Unsupported mapping for texture: ' + texture.name)

        luxTranslate = getattr(texture.luxrender_texture.luxrender_tex_transform, 'translate')
        luxScale = getattr(texture.luxrender_texture.luxrender_tex_transform, 'scale')
        luxRotate = getattr(texture.luxrender_texture.luxrender_tex_transform, 'rotate')

        # create a location matrix
        tex_loc = mathutils.Matrix.Translation((luxTranslate))

        # create an identitiy matrix
        tex_sca = mathutils.Matrix()
        tex_sca[0][0] = luxScale[0]  # X
        tex_sca[1][1] = luxScale[1]  # Y
        tex_sca[2][2] = luxScale[2]  # Z

        # create a rotation matrix
        tex_rot0 = mathutils.Matrix.Rotation(math.radians(luxRotate[0]), 4, 'X')
        tex_rot1 = mathutils.Matrix.Rotation(math.radians(luxRotate[1]), 4, 'Y')
        tex_rot2 = mathutils.Matrix.Rotation(math.radians(luxRotate[2]), 4, 'Z')
        tex_rot = tex_rot0 * tex_rot1 * tex_rot2

        # combine transformations
        f_matrix = matrix_to_list(tex_loc * tex_rot * tex_sca, apply_worldscale=True, invert=True)

        self.scnProps.Set(pyluxcore.Property(prefix + '.mapping.transformation', f_matrix))


    def ConvertColorRamp(self, texture, texName):
        """
        :param texture: Blender texture
        :param texName: luxcore name of child texture
        :return: texturename to be used in the parent slot (either the original texture or the band texture)
        """
        if texture.use_color_ramp:
            ramp = texture.color_ramp
            ramp_luxcore_name = texName + '_colorramp'
            ramp_prefix = 'scene.textures.' + ramp_luxcore_name

            self.scnProps.Set(pyluxcore.Property(ramp_prefix + '.type', 'band'))
            self.scnProps.Set(pyluxcore.Property(ramp_prefix + '.amount', texName))
            self.scnProps.Set(pyluxcore.Property(ramp_prefix + '.offsets', len(ramp.elements)))

            for i in range(len(ramp.elements)):
                position = ramp.elements[i].position
                color = list(ramp.elements[i].color[:3])  # Ignore alpha
                self.scnProps.Set(pyluxcore.Property(ramp_prefix + '.offset%d' % i, position))
                self.scnProps.Set(pyluxcore.Property(ramp_prefix + '.value%d' % i, color))

            return ramp_luxcore_name
        else:
            return texName


    def ConvertTexture(self, texture, luxcore_name=''):
        """
        :param texture: Blender texture (from bpy.data.textures)
        :param luxcore_name: optional target luxcore name to use for the texture (no check for duplicate!)
        :return: luxcore name of the exported texture
        """

        texType = texture.luxrender_texture.type
        texName = ToValidLuxCoreName(texture.name) if luxcore_name == '' else luxcore_name
        prefix = 'scene.textures.' + texName

        props = pyluxcore.Properties()

        if texType == 'BLENDER':
            bl_texType = getattr(texture, 'type')

            # ###################################################################
            # BLEND
            ####################################################################
            if bl_texType == 'BLEND':
                props.Set(pyluxcore.Property(prefix + '.type', ['blender_blend']))
                props.Set(pyluxcore.Property(prefix + '.progressiontype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'progression'))))
                props.Set(pyluxcore.Property(prefix + '.direction',
                                             ''.join(str(i).lower() for i in getattr(texture, 'use_flip_axis'))))
            ####################################################################
            # CLOUDS
            ####################################################################
            elif bl_texType == 'CLOUDS':
                props.Set(pyluxcore.Property(prefix + '.type', ['blender_clouds']))
                props.Set(pyluxcore.Property(prefix + '.noisetype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_type'))))
                props.Set(pyluxcore.Property(prefix + '.noisebasis',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_basis'))))
                props.Set(pyluxcore.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
                props.Set(pyluxcore.Property(prefix + '.noisedepth', [float(texture.noise_depth)]))
            ####################################################################
            # Distorted Noise
            ####################################################################
            elif bl_texType == 'DISTORTED_NOISE':
                props.Set(pyluxcore.Property(prefix + '.type', ['blender_distortednoise']))
                props.Set(pyluxcore.Property(prefix + '.noise_distortion',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_distortion'))))
                props.Set(pyluxcore.Property(prefix + '.noisebasis',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_basis'))))
                props.Set(pyluxcore.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
                props.Set(pyluxcore.Property(prefix + '.distortion', [float(texture.distortion)]))
            ####################################################################
            # IMAGE/MOVIE/SEQUENCE
            ####################################################################
            elif bl_texType == 'IMAGE' and texture.image and texture.image.source in ['GENERATED', 'FILE', 'SEQUENCE']:
                extract_path = os.path.join(
                    efutil.scene_filename(),
                    bpy.path.clean_name(self.blScene.name),
                    '%05d' % self.blScene.frame_current
                )

                if texture.image.source == 'GENERATED':
                    tex_image = 'luxblend_baked_image_%s.%s' % (
                        bpy.path.clean_name(texture.name), self.blScene.render.image_settings.file_format)
                    tex_image = os.path.join(extract_path, tex_image)
                    texture.image.save_render(tex_image, self.blScene)

                if texture.image.source == 'FILE':
                    if texture.image.packed_file:
                        tex_image = 'luxblend_extracted_image_%s.%s' % (
                            bpy.path.clean_name(texture.name), self.blScene.render.image_settings.file_format)
                        tex_image = os.path.join(extract_path, tex_image)
                        texture.image.save_render(tex_image, self.blScene)
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
                        tex_image = 'luxblend_extracted_image_%s.%s' % (
                            bpy.path.clean_name(texture.name), self.blScene.render.image_settings.file_format)
                        tex_image = os.path.join(extract_path, tex_image)
                        texture.image.save_render(tex_image, self.blScene)
                    else:
                        # sequence params from blender
                        # remove tex_preview extension to avoid error
                        sequence = bpy.data.textures[(texture.name).replace('.001', '')].image_user
                        seqframes = sequence.frame_duration
                        seqoffset = sequence.frame_offset
                        seqstartframe = sequence.frame_start  # the global frame at which the imagesequence starts
                        seqcyclic = sequence.use_cyclic
                        currentframe = self.blScene.frame_current

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

                props.Set(pyluxcore.Property(prefix + '.type', ['imagemap']))
                props.Set(pyluxcore.Property(prefix + '.file', [tex_image]))
                props.Set(
                    pyluxcore.Property(prefix + '.gamma', [texture.luxrender_texture.luxrender_tex_imagesampling.gamma]))
                props.Set(
                    pyluxcore.Property(prefix + '.gain', [texture.luxrender_texture.luxrender_tex_imagesampling.gain]))

                # if texture.image.use_alpha:
                #    props.Set(pyluxcore.Property(prefix + '.channel', [texture.luxrender_texture.luxrender_tex_imagesampling.channel]))

                self.ConvertMapping(prefix, texture)
            ####################################################################
            # MAGIC
            ####################################################################
            elif bl_texType == 'MAGIC':
                props.Set(pyluxcore.Property(prefix + '.type', ['blender_magic']))
                props.Set(pyluxcore.Property(prefix + '.turbulence', [float(texture.turbulence)]))
                props.Set(pyluxcore.Property(prefix + '.noisedepth', [float(texture.noise_depth)]))
            ####################################################################
            # MARBLE
            ####################################################################
            elif bl_texType == 'MARBLE':
                props.Set(pyluxcore.Property(prefix + '.type', ['blender_marble']))
                props.Set(pyluxcore.Property(prefix + '.marbletype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'marble_type'))))
                props.Set(pyluxcore.Property(prefix + '.noisebasis',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_basis'))))
                props.Set(pyluxcore.Property(prefix + '.noisebasis2',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_basis_2'))))
                props.Set(pyluxcore.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
                props.Set(pyluxcore.Property(prefix + '.noisedepth', [float(texture.noise_depth)]))
                props.Set(pyluxcore.Property(prefix + '.turbulence', [float(texture.turbulence)]))
                props.Set(pyluxcore.Property(prefix + '.noisetype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_type'))))
            ####################################################################
            # MUSGRAVE
            ####################################################################
            elif bl_texType == 'MUSGRAVE':
                props.Set(pyluxcore.Property(prefix + '.type', ['blender_musgrave']))
                props.Set(pyluxcore.Property(prefix + '.musgravetype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'musgrave_type'))))
                props.Set(pyluxcore.Property(prefix + '.noisebasis',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_basis'))))
                props.Set(pyluxcore.Property(prefix + '.dimension', [float(texture.dimension_max)]))
                props.Set(pyluxcore.Property(prefix + '.intensity', [float(texture.noise_intensity)]))
                props.Set(pyluxcore.Property(prefix + '.lacunarity', [float(texture.lacunarity)]))
                props.Set(pyluxcore.Property(prefix + '.offset', [float(texture.offset)]))
                props.Set(pyluxcore.Property(prefix + '.gain', [float(texture.gain)]))
                props.Set(pyluxcore.Property(prefix + '.octaves', [float(texture.octaves)]))
                props.Set(pyluxcore.Property(prefix + '.dimension', [float(texture.noise_scale)]))
                props.Set(pyluxcore.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
            # Not in blender:
            # props.Set(pyluxcore.Property(prefix + '.noisetype', ''.join(str(i).lower() for i in getattr(texture, 'noise_type'))))
            ####################################################################
            # NOISE
            ####################################################################
            elif bl_texType == 'NOISE':
                props.Set(pyluxcore.Property(prefix + '.type', ['blender_noise']))
                props.Set(pyluxcore.Property(prefix + '.noisedepth', [float(texture.noise_depth)]))
            ####################################################################
            # STUCCI
            ####################################################################
            elif bl_texType == 'STUCCI':
                props.Set(pyluxcore.Property(prefix + '.type', ['blender_stucci']))
                props.Set(pyluxcore.Property(prefix + '.stuccitype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'stucci_type'))))
                props.Set(pyluxcore.Property(prefix + '.noisebasis',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_basis'))))
                props.Set(pyluxcore.Property(prefix + '.noisetype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_type'))))
                props.Set(pyluxcore.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
                props.Set(pyluxcore.Property(prefix + '.turbulence', [float(texture.turbulence)]))
            ####################################################################
            # VORONOI
            ####################################################################
            elif bl_texType == 'VORONOI':
                props.Set(pyluxcore.Property(prefix + '.type', ['blender_voronoi']))
                props.Set(pyluxcore.Property(prefix + '.dismetric',
                                             ''.join(str(i).lower() for i in getattr(texture, 'distance_metric'))))
                # Not yet in luxcore:
                #props.Set(pyluxcore.Property(prefix + '.colormode', ''.join(str(i).lower() for i in getattr(texture, 'color_mode'))))
                props.Set(pyluxcore.Property(prefix + '.intensity', [float(texture.noise_intensity)]))
                props.Set(pyluxcore.Property(prefix + '.exponent', [float(texture.minkovsky_exponent)]))
                props.Set(pyluxcore.Property(prefix + '.w1', [float(texture.weight_1)]))
                props.Set(pyluxcore.Property(prefix + '.w2', [float(texture.weight_2)]))
                props.Set(pyluxcore.Property(prefix + '.w3', [float(texture.weight_3)]))
                props.Set(pyluxcore.Property(prefix + '.w4', [float(texture.weight_4)]))
                props.Set(pyluxcore.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
            ####################################################################
            # WOOD
            ####################################################################
            elif bl_texType == 'WOOD':
                props.Set(pyluxcore.Property(prefix + '.type', ['blender_wood']))
                props.Set(pyluxcore.Property(prefix + '.woodtype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'wood_type'))))
                props.Set(pyluxcore.Property(prefix + '.noisebasis2',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_basis_2'))))
                props.Set(pyluxcore.Property(prefix + '.noisetype',
                                             ''.join(str(i).lower() for i in getattr(texture, 'noise_type'))))
                props.Set(pyluxcore.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
                props.Set(pyluxcore.Property(prefix + '.turbulence', [float(texture.turbulence)]))
            ####################################################################
            # Pararameters shared by all blender textures
            ####################################################################
            props.Set(pyluxcore.Property(prefix + '.bright', [float(texture.intensity)]))
            props.Set(pyluxcore.Property(prefix + '.contrast', [float(texture.contrast)]))
            if bl_texType != 'IMAGE':
                self.ConvertTransform(prefix, texture)

            self.scnProps.Set(props)
            self.texturesCache.add(texName)
            return self.ConvertColorRamp(texture, texName)

        elif texType != 'BLENDER':
            luxTex = getattr(texture.luxrender_texture, 'luxrender_tex_' + texType)

            ####################################################################
            # ADD/SUBTRACT
            ####################################################################
            if texType in ('add', 'subtract'):
                props.Set(
                    pyluxcore.Property(prefix + '.texture1', convert_texture_channel(self.luxcore_exporter, self.properties, luxTex, 'tex1', luxTex.variant)))
                props.Set(
                    pyluxcore.Property(prefix + '.texture2', convert_texture_channel(self.luxcore_exporter, self.properties, luxTex, 'tex2', luxTex.variant)))
            ####################################################################
            # BAND
            ####################################################################
            elif texType == 'band':
                props.Set(pyluxcore.Property(prefix + '.amount', convert_texture_channel(self.luxcore_exporter, self.properties, luxTex, 'amount', 'float')))
                props.Set(pyluxcore.Property(prefix + '.offsets', [(luxTex.noffsets)]))

                if luxTex.variant != 'fresnel':
                    for i in range(0, luxTex.noffsets):
                        props.Set(pyluxcore.Property(prefix + '.offset%d' % i,
                                                     [float(getattr(luxTex, 'offset%s%s' % (luxTex.variant, str(i + 1))))]))

                        spectrum = convert_texture_channel(self.luxcore_exporter, self.properties, luxTex, 'tex%s' % str(i + 1), luxTex.variant).split(' ')
                        if len(spectrum) == 3:
                            value = spectrum
                        else:
                            value = [spectrum[0]] * 3

                        props.Set(pyluxcore.Property(prefix + '.value%d' % i, value))
                        i += 1
                else:
                    LuxLog('WARNING: Unsupported variant %s for texture: %s' % (luxTex.variant, texture.name))
            ####################################################################
            # BLACKBODY
            ####################################################################
            elif texType == 'blackbody':
                props.Set(pyluxcore.Property(prefix + '.temperature', [float(luxTex.temperature)]))
            ####################################################################
            # Brick
            ####################################################################
            elif texType == 'brick':
                props.Set(pyluxcore.Property(prefix + '.variant', [(luxTex.variant)]))
                props.Set(pyluxcore.Property(prefix + '.brickbond', [(luxTex.brickbond)]))

                if texture.luxrender_texture.luxrender_tex_brick.brickbond in ('running', 'flemish'):
                    props.Set(pyluxcore.Property(prefix + '.brickrun', [float(luxTex.brickrun)]))

                props.Set(pyluxcore.Property(prefix + '.mortarsize', [float(luxTex.mortarsize)]))
                props.Set(pyluxcore.Property(prefix + '.brickwidth', [float(luxTex.brickwidth)]))
                props.Set(pyluxcore.Property(prefix + '.brickdepth', [float(luxTex.brickdepth)]))
                props.Set(pyluxcore.Property(prefix + '.brickheight', [float(luxTex.brickheight)]))
                props.Set(pyluxcore.Property(prefix + '.bricktex',
                                             convert_texture_channel(self.luxcore_exporter, self.properties, luxTex, 'bricktex', luxTex.variant)))
                props.Set(pyluxcore.Property(prefix + '.brickmodtex',
                                             convert_texture_channel(self.luxcore_exporter, self.properties, luxTex, 'brickmodtex', luxTex.variant)))
                props.Set(pyluxcore.Property(prefix + '.mortartex',
                                             convert_texture_channel(self.luxcore_exporter, self.properties, luxTex, 'mortartex', luxTex.variant)))
                self.ConvertTransform(prefix, texture)
            ####################################################################
            # CHECKERBOARD
            ####################################################################
            elif texType == 'checkerboard':
                # props.Set(pyluxcore.Property(prefix + '.aamode', [float(luxTex.aamode)])) # not yet in luxcore
                props.Set(
                    pyluxcore.Property(prefix + '.texture1', convert_texture_channel(self.luxcore_exporter, self.properties, luxTex, 'tex1', 'float')))
                props.Set(
                    pyluxcore.Property(prefix + '.texture2', convert_texture_channel(self.luxcore_exporter, self.properties, luxTex, 'tex2', 'float')))
                if texture.luxrender_texture.luxrender_tex_checkerboard.dimension == 2:
                    props.Set(pyluxcore.Property(prefix + '.type', ['checkerboard2d']))
                    self.ConvertMapping(prefix, texture)
                else:
                    props.Set(pyluxcore.Property(prefix + '.type', ['checkerboard3d']))
                    self.ConvertTransform(prefix, texture)
            ####################################################################
            # CLOUD
            ####################################################################
            # elif texType == 'cloud':
            # props.Set(pyluxcore.Property(prefix + '.radius', [float(luxTex.radius)]))
            #     props.Set(pyluxcore.Property(prefix + '.noisescale', [float(luxTex.noisescale)]))
            #     props.Set(pyluxcore.Property(prefix + '.turbulence', [float(luxTex.turbulence)]))
            #     props.Set(pyluxcore.Property(prefix + '.sharpness', [float(luxTex.sharpness)]))
            #     props.Set(pyluxcore.Property(prefix + '.noiseoffset', [float(luxTex.noiseoffset)]))
            #     props.Set(pyluxcore.Property(prefix + '.spheres', [luxTex.spheres]))
            #     props.Set(pyluxcore.Property(prefix + '.octaves', [luxTex.octaves)])
            #     props.Set(pyluxcore.Property(prefix + '.omega', [float(luxTex.omega)]))
            #     props.Set(pyluxcore.Property(prefix + '.variability', [float(luxTex.variability)]))
            #     props.Set(pyluxcore.Property(prefix + '.baseflatness', [float(luxTex.baseflatness)]))
            #     props.Set(pyluxcore.Property(prefix + '.spheresize', [float(luxTex.spheresize)]))
            #     self.ConvertTransform(prefix, texture)
            ####################################################################
            # CONSTANT
            ####################################################################
            elif texType == 'constant':
                if luxTex.variant == 'color':
                    props.Set(pyluxcore.Property(prefix + '.type', ['constfloat3']))
                    props.Set(pyluxcore.Property(prefix + '.value',
                                                 [luxTex.colorvalue[0], luxTex.colorvalue[1], luxTex.colorvalue[2]]))
                elif luxTex.variant == 'float':
                    props.Set(pyluxcore.Property(prefix + '.type', ['constfloat1']))
                    props.Set(pyluxcore.Property(prefix + '.value', [float(luxTex.floatvalue)]))
                else:
                    LuxLog('WARNING: Unsupported variant %s for texture: %s' % (luxTex.variant, texture.name))
            ####################################################################
            # DOTS
            ####################################################################
            elif texType == 'dots':
                props.Set(pyluxcore.Property(prefix + '.inside', convert_texture_channel(self.luxcore_exporter, self.properties, luxTex, 'inside', 'float')))
                props.Set(pyluxcore.Property(prefix + '.outside', convert_texture_channel(self.luxcore_exporter, self.properties, luxTex, 'outside', 'float')))
                self.ConvertMapping(prefix, texture)
            ####################################################################
            # FBM
            ####################################################################
            elif texType == 'fbm':
                props.Set(pyluxcore.Property(prefix + '.octaves', [float(luxTex.octaves)]))
                props.Set(pyluxcore.Property(prefix + '.roughness', [float(luxTex.roughness)]))
                self.ConvertTransform(prefix, texture)
            ####################################################################
            # IMAGEMAP
            ####################################################################
            elif texType == 'imagemap':
                full_name, base_name = get_expanded_file_name(texture, luxTex.filename)
                props.Set(pyluxcore.Property(prefix + '.file', [full_name]))
                props.Set(pyluxcore.Property(prefix + '.gamma', [float(luxTex.gamma)]))
                props.Set(pyluxcore.Property(prefix + '.gain', [float(luxTex.gain)]))
                if luxTex.variant == 'float':
                    props.Set(pyluxcore.Property(prefix + '.channel', [(luxTex.channel)]))
                self.ConvertMapping(prefix, texture)
            ####################################################################
            # LAMPSPECTRUM
            ####################################################################
            elif texType == 'lampspectrum':
                props.Set(pyluxcore.Property(prefix + '.name', [luxTex.preset]))
            ####################################################################
            # Normalmap
            ####################################################################
            elif texType == 'normalmap':
                full_name, base_name = get_expanded_file_name(texture, luxTex.filename)
                props.Set(pyluxcore.Property(prefix + '.file', [full_name]))
                self.ConvertMapping(prefix, texture)
            ####################################################################
            # Marble
            ####################################################################
            elif texType == 'marble':
                props.Set(pyluxcore.Property(prefix + '.octaves', [float(luxTex.octaves)]))
                props.Set(pyluxcore.Property(prefix + '.roughness', [float(luxTex.roughness)]))
                props.Set(pyluxcore.Property(prefix + '.scale', [float(luxTex.scale)]))
                props.Set(pyluxcore.Property(prefix + '.variation', [float(luxTex.variation)]))
                self.ConvertTransform(prefix, texture)
            ####################################################################
            # Mix
            ####################################################################
            elif texType == 'mix':
                props.Set(pyluxcore.Property(prefix + '.amount', convert_texture_channel(self.luxcore_exporter, self.properties, luxTex, 'amount', 'float')))
                props.Set(
                    pyluxcore.Property(prefix + '.texture1', convert_texture_channel(self.luxcore_exporter, self.properties, luxTex, 'tex1', luxTex.variant)))
                props.Set(
                    pyluxcore.Property(prefix + '.texture2', convert_texture_channel(self.luxcore_exporter, self.properties, luxTex, 'tex2', luxTex.variant)))
            ####################################################################
            # Scale
            ####################################################################
            elif texType == 'scale':
                props.Set(pyluxcore.Property(prefix + '.variant', [(luxTex.variant)]))
                props.Set(
                    pyluxcore.Property(prefix + '.texture1', convert_texture_channel(self.luxcore_exporter, self.properties, luxTex, 'tex1', luxTex.variant)))
                props.Set(
                    pyluxcore.Property(prefix + '.texture2', convert_texture_channel(self.luxcore_exporter, self.properties, luxTex, 'tex2', luxTex.variant)))
            ####################################################################
            # UV
            ####################################################################
            elif texType == 'uv':
                self.ConvertMapping(prefix, texture)
            ####################################################################
            # WINDY
            ####################################################################
            elif texType == 'windy':
                self.ConvertTransform(prefix, texture)
            ####################################################################
            # WRINKLED
            ####################################################################
            elif texType == 'wrinkled':
                props.Set(pyluxcore.Property(prefix + '.octaves', [float(luxTex.octaves)]))
                props.Set(pyluxcore.Property(prefix + '.roughness', [float(luxTex.roughness)]))
                self.ConvertTransform(prefix, texture)
            ####################################################################
            # Vertex Colors
            ####################################################################
            elif texType in ['hitpointcolor', 'hitpointgrey', 'hitpointalpha']:
                pass
            ####################################################################
            # Fresnel color
            ####################################################################
            elif texType == 'fresnelcolor':
                props.Set(pyluxcore.Property(prefix + '.kr', convert_texture_channel(self.luxcore_exporter, self.properties, luxTex, 'Kr', 'color')))
            ####################################################################
            # Fresnel preset (name)
            ####################################################################
            elif texType == 'fresnelname':
                props.Set(pyluxcore.Property(prefix + '.type', 'fresnelpreset'))
                props.Set(pyluxcore.Property(prefix + '.name', luxTex.name))
            ####################################################################
            # Fresnel sopra
            ####################################################################
            elif texType == 'sopra':
                props.Set(pyluxcore.Property(prefix + '.type', 'fresnelsopra'))
                full_name, base_name = get_expanded_file_name(texture, luxTex.filename)
                props.Set(pyluxcore.Property(prefix + '.file', full_name))
            ####################################################################
            # Fresnel luxpop
            ####################################################################
            elif texType == 'luxpop':
                props.Set(pyluxcore.Property(prefix + '.type', 'fresnelluxpop'))
                full_name, base_name = get_expanded_file_name(texture, luxTex.filename)
                props.Set(pyluxcore.Property(prefix + '.file', full_name))
            ####################################################################
            # Pointiness (hitpointalpha texture behind the scenes, just that it
            #            implicitly enables pointiness calculation on the mesh)
            ####################################################################
            elif texType == 'pointiness':
                props.Set(pyluxcore.Property(prefix + '.type', 'hitpointalpha'))
            ####################################################################
            # Fallback to exception
            ####################################################################
            else:
                raise Exception('Unknown type ' + texType + ' for texture: ' + texture.name)

            if texType not in ('normalmap', 'checkerboard', 'constant', 'fresnelname', 'luxpop', 'sopra', 'pointiness'):
                props.Set(pyluxcore.Property(prefix + '.type', texType))

            self.scnProps.Set(props)
            self.texturesCache.add(texName)
            return self.ConvertColorRamp(texture, texName)

        raise Exception('Unknown texture type: ' + texture.name)