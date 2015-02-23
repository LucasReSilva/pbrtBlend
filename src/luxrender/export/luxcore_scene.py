# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# David Bucciarelli
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
import bpy, os, time
from ..extensions_framework import util as efutil
from symbol import except_clause
import math
import mathutils

from ..outputs import LuxManager, LuxLog
from ..outputs.luxcore_api import pyluxcore
from ..outputs.luxcore_api import ToValidLuxCoreName
from ..export import get_worldscale, matrix_to_list
from ..export import is_obj_visible
from ..export import get_expanded_file_name
from ..export import ParamSet
from ..export.materials import get_texture_from_scene


class ExportedObjectData(object):
    lcObjName = ''
    lcMeshName = ''
    lcMaterialName = ''
    matIndex = 0
    lightType = ''

    def __init__(self, lcObjName, lcMeshName = '', lcMaterialName = '', matIndex = 0, lightType = ''):
        self.lcObjName = lcObjName
        self.lcMeshName = lcMeshName
        self.lcMaterialName = lcMaterialName
        self.matIndex = matIndex
        self.lightType = lightType

    def __str__(self):
        output = ('lcObjName: ' + self.lcObjName +
                  ',\nlcMeshName: ' + self.lcMeshName +
                  ',\nlcMaterialName: ' + self.lcMaterialName +
                  ',\nmatIndex: ' + str(self.matIndex) +
                  ',\nlightType: ' + self.lightType)
        return output

class ExportedObject(object):
    blender_object = None
    blender_data = None
    # split by material
    luxcore_data = []

    def __init__(self, obj, obj_data, luxcore_data):
        self.blender_object = obj
        self.blender_data = obj_data
        self.luxcore_data = luxcore_data

class ExportCache(object):
    cache = {}

    def __init__(self):
        self.cache = {}

    def add_obj(self, obj, luxcore_data):
        exported_object = ExportedObject(obj, obj.data, luxcore_data)
        self.cache[obj] = exported_object
        self.cache[obj.data] = exported_object

    def has_obj(self, obj):
        return obj in self.cache

    def has_obj_data(self, obj_data):
        return obj_data in self.cache

    def get_exported_object_key_obj(self, obj):
        try:
            return self.cache[obj]
        except KeyError:
            return None

    def get_exported_object_key_data(self, obj_data):
        try:
            return self.cache[obj_data]
        except KeyError:
            return None

class BlenderSceneConverter(object):
    scalers_count = 0
    # Amount of output channels (AOVs)
    outputCounter = 0
    material_id_mask_counter = 0
    by_material_id_counter = 0

    dupli_amount = 0
    dupli_number = 0

    export_cache = ExportCache()

    volumes_cache = {} # Structure: {volume.name : luxcore_name}
    lightgroups_cache = {} # Structure: {lightgroup_name : luxcore_ID}

    def __init__(self, blScene, lcSession=None, renderengine=None):
        LuxManager.SetCurrentScene(blScene)

        self.blScene = blScene
        self.renderengine = renderengine
        if lcSession is not None:
            self.lcScene = lcSession.GetRenderConfig().GetScene()
        else:
            imageScale = self.blScene.luxcore_scenesettings.imageScale
            self.lcScene = pyluxcore.Scene(imageScale)

        self.scnProps = pyluxcore.Properties()
        self.cfgProps = pyluxcore.Properties()

        self.materialsCache = set()
        self.texturesCache = set()

    @staticmethod
    def next_scale_value():
        BlenderSceneConverter.scalers_count += 1
        return BlenderSceneConverter.scalers_count

    @staticmethod
    def generate_material_name(rawMatName):
        # materials and volumes must not have the same names
        return ToValidLuxCoreName(rawMatName) + '-mat'

    @staticmethod
    def generate_volume_name(rawVolName):
        # materials and volumes must not have the same names
        return ToValidLuxCoreName(rawVolName) + '-vol'

    @staticmethod
    def clear():
        BlenderSceneConverter.scalers_count = 0

    @staticmethod
    def get_export_cache():
        return BlenderSceneConverter.export_cache

    @staticmethod
    def clear_export_cache():
        BlenderSceneConverter.export_cache = ExportCache()

    def createChannelOutputString(self, channelName, id=-1):
        """
        Sets configuration properties for LuxCore AOV output
        """

        # the OpenCL engines only support 1 MATERIAL_ID_MASK, 1 BY_MATERIAL_ID channel and 8 RADIANCE_GROUP channels
        engine = self.blScene.luxcore_enginesettings.renderengine_type
        is_ocl_engine = engine in ['BIASPATHOCL', 'PATHOCL']
        if is_ocl_engine:
            if channelName == 'MATERIAL_ID_MASK':
                if self.material_id_mask_counter == 0:
                    self.material_id_mask_counter += 1
                else:
                    # don't create the output channel
                    return

            elif channelName == 'BY_MATERIAL_ID':
                if self.by_material_id_counter == 0:
                    self.by_material_id_counter += 1
                else:
                    # don't create the output channel
                    return

        if channelName == 'RADIANCE_GROUP':
            if id > 7 and is_ocl_engine:
                # don't create the output channel
                LuxLog('WARNING: OpenCL engines support a maximum of 8 lightgroups! Skipping this lightgroup (ID: %d)'
                       % id)
                return

        self.outputCounter += 1

        # list of channels that don't use an HDR format
        LDR_channels = ['RGB_TONEMAPPED', 'RGBA_TONEMAPPED', 'ALPHA', 'MATERIAL_ID', 'DIRECT_SHADOW_MASK',
                        'INDIRECT_SHADOW_MASK', 'MATERIAL_ID_MASK']

        # channel type (e.g. 'film.outputs.1.type')
        outputStringType = 'film.outputs.' + str(self.outputCounter) + '.type'
        self.cfgProps.Set(pyluxcore.Property(outputStringType, [channelName]))

        # output filename (e.g. 'film.outputs.1.filename')
        suffix = ('.png' if (channelName in LDR_channels) else '.exr')
        outputStringFilename = 'film.outputs.' + str(self.outputCounter) + '.filename'
        filename = channelName + suffix if id == -1 else channelName + '_' + str(id) + suffix
        self.cfgProps.Set(pyluxcore.Property(outputStringFilename, [filename]))

        # output id
        if id != -1:
            outputStringId = 'film.outputs.' + str(self.outputCounter) + '.id'
            self.cfgProps.Set(pyluxcore.Property(outputStringId, [id]))

    def DefineBlenderMeshAccelerated(self, name, mesh):
        faces = mesh.tessfaces[0].as_pointer()
        vertices = mesh.vertices[0].as_pointer()

        uv_textures = mesh.tessface_uv_textures
        if len(uv_textures) > 0 and mesh.uv_textures.active and uv_textures.active.data:
            texCoords = uv_textures.active.data[0].as_pointer()
        else:
            texCoords = 0

        vertex_color = mesh.tessface_vertex_colors.active
        if vertex_color:
            vertexColors = vertex_color.data[0].as_pointer()
        else:
            vertexColors = 0

        return self.lcScene.DefineBlenderMesh(name, len(mesh.tessfaces), faces, len(mesh.vertices),
                                       vertices, texCoords, vertexColors)

    def DefineBlenderMeshDeprecated(self, name, mesh, ffaces_mats, index):
        uv_textures = mesh.tessface_uv_textures
        uv_layer = None
        if len(uv_textures) > 0:
            if uv_textures.active and uv_textures.active.data:
                uv_layer = uv_textures.active.data

        color_layer = mesh.tessface_vertex_colors.active.data if mesh.tessface_vertex_colors.active else None

        # Export data
        points = []
        normals = []
        uvs = []
        cols = []
        face_vert_indices = []  # List of face vert indices

        # Caches
        vert_vno_indices = {}  # Mapping of vert index to exported vert index for verts with vert normals
        vert_use_vno = set()  # Set of vert indices that use vert normals
        vert_index = 0  # Exported vert index

        for face in ffaces_mats[index]:
            fvi = []
            for j, vertex in enumerate(face.vertices):
                v = mesh.vertices[vertex]

                if color_layer:
                    if j == 0:
                        vert_col = color_layer[face.index].color1
                    elif j == 1:
                        vert_col = color_layer[face.index].color2
                    elif j == 2:
                        vert_col = color_layer[face.index].color3
                    elif j == 3:
                        vert_col = color_layer[face.index].color4
                    vert_col = tuple(vert_col[0:3])

                if face.use_smooth:
                    vert_data = (v.co[:], v.normal[:],
                                 uv_layer[face.index].uv[j][:] if uv_layer else tuple(),
                                 vert_col if color_layer else tuple())

                    if vert_data not in vert_use_vno:
                        vert_use_vno.add(vert_data)

                        points.append(vert_data[0])
                        normals.append(vert_data[1])
                        uvs.append(vert_data[2])
                        cols.append(vert_data[3])

                        vert_vno_indices[vert_data] = vert_index
                        fvi.append(vert_index)

                        vert_index += 1
                    else:
                        fvi.append(vert_vno_indices[vert_data])

                else:
                    # all face-vert-co-no are unique, we cannot
                    # cache them
                    points.append(v.co[:])
                    normals.append(face.normal[:])
                    if uv_layer:
                        uvs.append(uv_layer[face.index].uv[j][:])
                    if color_layer:
                        cols.append(vert_col)

                    fvi.append(vert_index)

                    vert_index += 1

            # For Lux, we need to triangulate quad faces
            face_vert_indices.append(tuple(fvi[0:3]))
            if len(fvi) == 4:
                face_vert_indices.append((fvi[0], fvi[2], fvi[3]))

        del vert_vno_indices
        del vert_use_vno

        self.lcScene.DefineMesh('Mesh-' + name, points, face_vert_indices, normals,
                                uvs if uv_layer else None, cols if color_layer else None, None)

    def GenerateMeshName(self, obj, matIndex = -1):
        indexString = ('%03d' % matIndex) if matIndex != -1 else ''
        mesh_name = '%s-%s%s' % (self.blScene.name, obj.data.name, indexString)

        return ToValidLuxCoreName(mesh_name)

    def CreateExportMesh(self, obj, apply_modifiers, preview):
        mode = 'PREVIEW' if preview else 'RENDER'
        mesh = obj.to_mesh(self.blScene, apply_modifiers, mode)

        mesh.update(calc_tessface = True)

        return mesh

    def ConvertObjectGeometry(self, obj, preview = False, update_mesh = True, is_dupli = False):
        try:
            mesh_definitions = []

            # check if the object should not/cannot be exported
            if (not is_obj_visible(self.blScene, obj, is_dupli = is_dupli) or
                        obj.type not in ['MESH', 'CURVE', 'SURFACE', 'META', 'FONT'] or
                        obj.data.luxrender_mesh.portal):
                return mesh_definitions

            #convert_blender_start = int(round(time.time() * 1000)) #### DEBUG

            # applying modifiers takes time, so don't do it if we won't update the mesh anyway
            if update_mesh:
                mesh = self.CreateExportMesh(obj, True, preview)
            else:
                mesh = self.CreateExportMesh(obj, False, preview)

            if mesh is None:
                LuxLog('Cannot create render/export object: %s' % obj.name)
                return mesh_definitions

            #print('blender obj.to_mesh took %dms' % (int(round(time.time() * 1000)) - convert_blender_start)) #### DEBUG
            #convert_lux_start = int(round(time.time() * 1000)) #### DEBUG

            if getattr(pyluxcore.Scene, 'DefineBlenderMesh', None) is not None:
                #LuxLog('Using c++ accelerated mesh export')
                if update_mesh:
                    lcMeshName = self.GenerateMeshName(obj)

                    meshInfoList = self.DefineBlenderMeshAccelerated(lcMeshName, mesh)
                    mesh_definitions.extend(meshInfoList)
                else:
                    number_of_mats = len(mesh.materials)
                    if number_of_mats > 0:
                        iterator_range = range(number_of_mats)
                    else:
                        iterator_range = [0]

                    for i in iterator_range:
                        lcMeshName = self.GenerateMeshName(obj, i)
                        mesh_definitions.append((lcMeshName, i))
            else:
                #LuxLog('Using classic python mesh export (c++ acceleration not available)')
                # Collate faces by mat index
                ffaces_mats = {}
                mesh_faces = mesh.tessfaces
                for f in mesh_faces:
                    mi = f.material_index

                    if mi not in ffaces_mats.keys():
                        ffaces_mats[mi] = []

                    ffaces_mats[mi].append(f)
                material_indices = ffaces_mats.keys()

                number_of_mats = len(mesh.materials)

                if number_of_mats > 0:
                    iterator_range = range(number_of_mats)
                else:
                    iterator_range = [0]

                for i in iterator_range:
                    try:
                        if i not in material_indices:
                            continue

                        lcMeshName = self.GenerateMeshName(obj, i)

                        if update_mesh:
                            self.DefineBlenderMeshDeprecated(lcMeshName, mesh, ffaces_mats, i)

                        mesh_definitions.append((lcMeshName, i))

                    except Exception as err:
                        LuxLog('Mesh export failed, skipping this mesh: %s\n' % err)
                        import traceback
                        traceback.print_exc()

                del ffaces_mats

            bpy.data.meshes.remove(mesh)

            #print('export took %dms' % (int(round(time.time() * 1000)) - convert_lux_start)) #### DEBUG

            return mesh_definitions

        except Exception as err:
            LuxLog('Mesh export failed, skipping mesh of object: %s\n' % err)
            import traceback
            traceback.print_exc()
            return []

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
        tex_sca0 = mathutils.Matrix.Scale((luxScale[0]), 4)
        tex_sca1 = mathutils.Matrix.Scale((luxScale[1]), 4)
        tex_sca2 = mathutils.Matrix.Scale((luxScale[2]), 4)
        tex_sca = tex_sca0 * tex_sca1 * tex_sca2

        # create a rotation matrix
        tex_rot0 = mathutils.Matrix.Rotation(math.radians(luxRotate[0]), 4, 'X')
        tex_rot1 = mathutils.Matrix.Rotation(math.radians(luxRotate[1]), 4, 'Y')
        tex_rot2 = mathutils.Matrix.Rotation(math.radians(luxRotate[2]), 4, 'Z')
        tex_rot = tex_rot0 * tex_rot1 * tex_rot2

        # combine transformations
        f_matrix = matrix_to_list(tex_loc * tex_sca * tex_rot)

        self.scnProps.Set(pyluxcore.Property(prefix + '.mapping.transformation', f_matrix))

    def ConvertTexture(self, texture, luxcore_name = ''):
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

                props.Set(pyluxcore.Property(prefix + '.file', [tex_image]))

                props.Set(pyluxcore.Property(prefix + '.gamma', [texture.luxrender_texture.luxrender_tex_imagesampling.gamma]))
                props.Set(pyluxcore.Property(prefix + '.gain', [texture.luxrender_texture.luxrender_tex_imagesampling.gain]))
                #props.Set(pyluxcore.Property(prefix + '.channel', [texture.luxrender_texture.luxrender_tex_imagesampling.channel]))

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
            # props.Set(pyluxcore.Property(prefix + '.noisetype', ''.join(str(i).lower() for i in getattr(texture, 'noise_type')))) # not in blender !
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
                # props.Set(pyluxcore.Property(prefix + '.colormode', ''.join(str(i).lower() for i in getattr(texture, 'color_mode')))) # not yet in luxcore
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
            return texName

        elif texType != 'BLENDER':
            luxTex = getattr(texture.luxrender_texture, 'luxrender_tex_' + texType)

            # ###################################################################
            # ADD
            ####################################################################
            if texType == 'add':
                props.Set(pyluxcore.Property(prefix + '.variant', [(luxTex.variant)]))
                if luxTex.variant == 'color':
                    props.Set(
                        pyluxcore.Property(prefix + '.texture1', self.ConvertMaterialChannel(luxTex, 'tex1', 'color')))
                    props.Set(
                        pyluxcore.Property(prefix + '.texture2', self.ConvertMaterialChannel(luxTex, 'tex2', 'color')))
                elif luxTex.variant == 'float':
                    props.Set(
                        pyluxcore.Property(prefix + '.texture1', self.ConvertMaterialChannel(luxTex, 'tex1', 'float')))
                    props.Set(
                        pyluxcore.Property(prefix + '.texture2', self.ConvertMaterialChannel(luxTex, 'tex2', 'float')))
            ####################################################################
            # BAND
            ####################################################################
            elif texType == 'band':
                props.Set(
                    pyluxcore.Property(prefix + '.amount', self.ConvertMaterialChannel(luxTex, 'amount', 'float')))
                props.Set(pyluxcore.Property(prefix + '.offsets', [(luxTex.noffsets)]))
                if luxTex.variant == 'color':
                    for i in range(0, luxTex.noffsets):
                        props.Set(pyluxcore.Property(prefix + '.offset%d' % i,
                                                     [float(getattr(luxTex, 'offsetcolor%s' % str(i + 1)))]))
                        spectrum = self.ConvertMaterialChannel(luxTex, 'tex%s' % str(i + 1), 'color').split(' ')
                        props.Set(pyluxcore.Property(prefix + '.value%d' % i,
                                                     [float(spectrum[0]), float(spectrum[1]), float(spectrum[2])]))
                        i += 1
                else:
                    LuxLog('WARNING: Unsupported variant %s for texture: %s' % (luxTex.variant, texture.name))
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

                if luxTex.variant == 'color':
                    props.Set(pyluxcore.Property(prefix + '.bricktex',
                                                 self.ConvertMaterialChannel(luxTex, 'bricktex', 'color')))
                    props.Set(pyluxcore.Property(prefix + '.brickmodtex',
                                                 self.ConvertMaterialChannel(luxTex, 'brickmodtex', 'color')))
                    props.Set(pyluxcore.Property(prefix + '.mortartex',
                                                 self.ConvertMaterialChannel(luxTex, 'mortartex', 'color')))
                else:
                    props.Set(pyluxcore.Property(prefix + '.bricktex',
                                                 self.ConvertMaterialChannel(luxTex, 'bricktex', 'float')))
                    props.Set(pyluxcore.Property(prefix + '.brickmodtex',
                                                 self.ConvertMaterialChannel(luxTex, 'brickmodtex', 'float')))
                    props.Set(pyluxcore.Property(prefix + '.mortartex',
                                                 self.ConvertMaterialChannel(luxTex, 'mortartex', 'float')))
                self.ConvertTransform(prefix, texture)
            ####################################################################
            # CHECKERBOARD
            ####################################################################
            elif texType == 'checkerboard':
                # props.Set(pyluxcore.Property(prefix + '.aamode', [float(luxTex.aamode)])) # not yet in luxcore
                props.Set(
                    pyluxcore.Property(prefix + '.texture1', self.ConvertMaterialChannel(luxTex, 'tex1', 'float')))
                props.Set(
                    pyluxcore.Property(prefix + '.texture2', self.ConvertMaterialChannel(luxTex, 'tex2', 'float')))
                if texture.luxrender_texture.luxrender_tex_checkerboard.dimension == 2:
                    props.Set(pyluxcore.Property(prefix + '.type', ['checkerboard2d']))
                    self.ConvertMapping(prefix, texture)
                else:
                    props.Set(pyluxcore.Property(prefix + '.type', ['checkerboard3d']))
                    self.ConvertTransform(prefix, texture)
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
                props.Set(
                    pyluxcore.Property(prefix + '.inside', self.ConvertMaterialChannel(luxTex, 'inside', 'float')))
                props.Set(
                    pyluxcore.Property(prefix + '.outside', self.ConvertMaterialChannel(luxTex, 'outside', 'float')))
                self.ConvertMapping(prefix, texture)
            ####################################################################
            # FBM
            ####################################################################
            elif texType == 'fbm':
                props.Set(pyluxcore.Property(prefix + '.octaves', [float(luxTex.octaves)]))
                props.Set(pyluxcore.Property(prefix + '.roughness', [float(luxTex.roughness)]))
                self.ConvertTransform(prefix, texture)
            ####################################################################
            # Imagemap
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
                props.Set(
                    pyluxcore.Property(prefix + '.amount', self.ConvertMaterialChannel(luxTex, 'amount', 'float')))
                props.Set(pyluxcore.Property(prefix + '.variant', [(luxTex.variant)]))
                if luxTex.variant == 'color':
                    props.Set(
                        pyluxcore.Property(prefix + '.texture1', self.ConvertMaterialChannel(luxTex, 'tex1', 'color')))
                    props.Set(
                        pyluxcore.Property(prefix + '.texture2', self.ConvertMaterialChannel(luxTex, 'tex2', 'color')))
                elif luxTex.variant == 'float':
                    props.Set(
                        pyluxcore.Property(prefix + '.texture1', self.ConvertMaterialChannel(luxTex, 'tex1', 'float')))
                    props.Set(
                        pyluxcore.Property(prefix + '.texture2', self.ConvertMaterialChannel(luxTex, 'tex2', 'float')))
                elif luxTex.variant == 'fresnel':
                    props.Set(pyluxcore.Property(prefix + '.texture1',
                                                 self.ConvertMaterialChannel(luxTex, 'tex1', 'fresnel')))
                    props.Set(pyluxcore.Property(prefix + '.texture2',
                                                 self.ConvertMaterialChannel(luxTex, 'tex2', 'fresnel')))
            ####################################################################
            # Scale
            ####################################################################
            elif texType == 'scale':
                props.Set(pyluxcore.Property(prefix + '.variant', [(luxTex.variant)]))
                if luxTex.variant == 'color':
                    props.Set(
                        pyluxcore.Property(prefix + '.texture1', self.ConvertMaterialChannel(luxTex, 'tex1', 'color')))
                    props.Set(
                        pyluxcore.Property(prefix + '.texture2', self.ConvertMaterialChannel(luxTex, 'tex2', 'color')))
                elif luxTex.variant == 'float':
                    props.Set(
                        pyluxcore.Property(prefix + '.texture1', self.ConvertMaterialChannel(luxTex, 'tex1', 'float')))
                    props.Set(
                        pyluxcore.Property(prefix + '.texture2', self.ConvertMaterialChannel(luxTex, 'tex2', 'float')))
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
            # Vertex Color
            ####################################################################
            elif texType == 'hitpointcolor':
                pass
            ####################################################################
            # Vertex Color (black/white)
            ####################################################################
            elif texType == 'hitpointgrey':
                pass
            ####################################################################
            # Vertex Color (alpha)
            ####################################################################
            elif texType == 'hitpointalpha':
                pass
            ####################################################################
            # Fallback to exception
            ####################################################################
            else:
                raise Exception('Unknown type ' + texType + ' for texture: ' + texture.name)

            if texType not in ('normalmap', 'checkerboard', 'constant'):
                props.Set(pyluxcore.Property(prefix + '.type', texType))

            self.scnProps.Set(props)
            self.texturesCache.add(texName)
            return texName

        raise Exception('Unknown texture type: ' + texture.name)

    def ConvertMaterialChannel(self, luxMaterial, materialChannel, variant):
        if getattr(luxMaterial, '%s_use%stexture' % (materialChannel, variant)):
            texName = getattr(luxMaterial, '%s_%stexturename' % (materialChannel, variant))
            is_multiplied = getattr(luxMaterial, '%s_multiply%s' % (materialChannel, variant))
            validTexName = ToValidLuxCoreName(texName)
            # Check if it is an already defined texture, but texture with different multipliers must not stop here
            if validTexName in self.texturesCache and not is_multiplied:
                return validTexName
            LuxLog('Texture: ' + texName)

            texture = get_texture_from_scene(self.blScene, texName)
            if texture:
                if hasattr(luxMaterial, '%s_multiply%s' % (materialChannel, variant)) and is_multiplied:
                    texName = self.ConvertTexture(texture)
                    sv = BlenderSceneConverter.next_scale_value()
                    sctexName = '%s_scaled_%i' % (texName, sv)

                    self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.type', ['scale']))
                    if variant == 'color':
                        self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.texture1', ' '.join(
                        str(i) for i in (getattr(luxMaterial, materialChannel + '_color')))))
                    else:
                        self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.texture1', str(getattr(
                            luxMaterial, materialChannel + '_%svalue' % variant))))

                    self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.texture2', [texName]))

                    return sctexName

                else:
                    return self.ConvertTexture(texture)
        else:
            if variant == 'color':
                return ' '.join(str(i) for i in getattr(luxMaterial, materialChannel + '_color'))
            else:
                return str(getattr(luxMaterial, materialChannel + '_%svalue' % variant))

        raise Exception(
            'Unknown texture in channel' + materialChannel + ' for material ' + luxMaterial.luxrender_material.type)

    def ConvertCommonChannel(self, luxMap, material, type):
        if getattr(material.luxrender_material, '%s_usefloattexture' % type):
            is_multiplied = getattr(material.luxrender_material, '%s_multiplyfloat' % type)
            texName = getattr(material.luxrender_material, '%s_floattexturename' % type)
            validTexName = ToValidLuxCoreName(texName)
            # Check if it is an already defined texture, but texture with different multipliers must not stop here
            if validTexName in self.texturesCache and not is_multiplied:
                return validTexName
            LuxLog('Texture: ' + texName)

            texture = get_texture_from_scene(self.blScene, texName)
            if texture:
                if hasattr(material.luxrender_material, '%s_multiplyfloat' % type) and is_multiplied:
                    texName = self.ConvertTexture(texture)
                    sv = BlenderSceneConverter.next_scale_value()
                    sctexName = '%s_scaled_%i' % (texName, sv)

                    self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.type', ['scale']))
                    self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.texture1', float(
                        getattr(material.luxrender_material, '%s_floatvalue' % type))))
                    self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.texture2', ['%s' % texName]))

                    return sctexName

                else:
                    return self.ConvertTexture(texture)

    def ConvertMaterial(self, material, materials = None, no_conversion = False):
        """
        material: material to convert
        materials: obj.material_slots
        """

        def set_volumes(prefix):
            # Interior volume
            if hasattr(material.luxrender_material, 'Interior_volume') and \
                    material.luxrender_material.Interior_volume:
                validInteriorName = BlenderSceneConverter.volumes_cache[material.luxrender_material.Interior_volume]
                props.Set(pyluxcore.Property(prefix + '.volume.interior', validInteriorName))

            # Exterior volume
            if hasattr(material.luxrender_material, 'Exterior_volume') and \
                    material.luxrender_material.Exterior_volume:
                validExteriorName = BlenderSceneConverter.volumes_cache[material.luxrender_material.Exterior_volume]
                props.Set(pyluxcore.Property(prefix + '.volume.exterior', validExteriorName))

        try:
            if material is None:
                return 'LUXBLEND_LUXCORE_CLAY_MATERIAL'

            matName = BlenderSceneConverter.generate_material_name(material.name)

            # in realtimepreview, we sometimes only need the name
            if no_conversion and self.lcScene.IsMaterialDefined(matName):
                return matName

            # Check if it is an already defined material
            if matName in self.materialsCache:
                return matName

            LuxLog('Converting material \'%s\'' % material.name)

            matType = material.luxrender_material.type
            luxMat = getattr(material.luxrender_material, 'luxrender_mat_' + matType)
            props = pyluxcore.Properties()
            prefix = 'scene.materials.' + matName

            # material override (clay render)
            translator_settings = self.blScene.luxcore_translatorsettings
            if translator_settings.override_materials and matType != 'mix':
                if 'glass' in matType:
                    if translator_settings.override_glass:
                        return 'LUXBLEND_LUXCORE_CLAY_MATERIAL'
                elif matType == 'null':
                    if translator_settings.override_null:
                        return 'LUXBLEND_LUXCORE_CLAY_MATERIAL'
                else:
                    # all materials that are not glass, lights or null
                    return 'LUXBLEND_LUXCORE_CLAY_MATERIAL'

            # ###################################################################
            # Matte and Roughmatte
            ####################################################################
            if matType == 'matte':
                sigma = self.ConvertMaterialChannel(luxMat, 'sigma', 'float')

                if sigma == '0.0':
                    props.Set(pyluxcore.Property(prefix + '.type', ['matte']))
                    props.Set(pyluxcore.Property(prefix + '.kd', self.ConvertMaterialChannel(luxMat, 'Kd', 'color')))
                else:
                    props.Set(pyluxcore.Property(prefix + '.type', ['roughmatte']))
                    props.Set(pyluxcore.Property(prefix + '.kd', self.ConvertMaterialChannel(luxMat, 'Kd', 'color')))
                    props.Set(
                        pyluxcore.Property(prefix + '.sigma', self.ConvertMaterialChannel(luxMat, 'sigma', 'float')))

            ####################################################################
            # Mattetranslucent
            ####################################################################
            elif matType == 'mattetranslucent':
                props.Set(pyluxcore.Property(prefix + '.type', ['mattetranslucent']))
                props.Set(pyluxcore.Property(prefix + '.kr', self.ConvertMaterialChannel(luxMat, 'Kr', 'color')))
                props.Set(pyluxcore.Property(prefix + '.kt', self.ConvertMaterialChannel(luxMat, 'Kt', 'color')))
                props.Set(pyluxcore.Property(prefix + '.sigma', self.ConvertMaterialChannel(luxMat, 'sigma', 'float')))

            ####################################################################
            # Metal (for keeping bw compat., but use metal2 )
            ####################################################################
            elif matType == 'metal':
                props.Set(pyluxcore.Property(prefix + '.type', ['metal2']))
                m_type = material.luxrender_material.luxrender_mat_metal.name

                if m_type != 'nk':
                    props.Set(
                        pyluxcore.Property(prefix + '.preset', m_type))

                # TODO: nk_data
                else:
                    LuxLog('WARNING: Not yet supported metal type: %s' % m_type)

                props.Set(pyluxcore.Property(prefix + '.uroughness',
                                             self.ConvertMaterialChannel(luxMat, 'uroughness', 'float')))

                props.Set(pyluxcore.Property(prefix + '.vroughness',
                                             self.ConvertMaterialChannel(luxMat, 'vroughness', 'float')))

            ####################################################################
            # Metal2
            ####################################################################
            elif matType == 'metal2':
                props.Set(pyluxcore.Property(prefix + '.type', ['metal2']))
                m2_type = material.luxrender_material.luxrender_mat_metal2.metaltype

                if m2_type == 'preset':
                    props.Set(
                        pyluxcore.Property(prefix + '.preset', material.luxrender_material.luxrender_mat_metal2.preset))
                elif m2_type == 'fresnelcolor':
                    fn_dummy_tex = '%s_fn_dummy_tex' % matName
                    fk_dummy_tex = '%s_fk_dummy_tex' % matName
                    props.Set(pyluxcore.Property(prefix + '.n', fn_dummy_tex))
                    props.Set(pyluxcore.Property(prefix + '.k', fk_dummy_tex))
                    props.Set(pyluxcore.Property('scene.textures.' + fn_dummy_tex + '.type', 'fresnelapproxn'))
                    props.Set(pyluxcore.Property('scene.textures.' + fn_dummy_tex + '.texture',
                                                 self.ConvertMaterialChannel(luxMat, 'Kr', 'color')))
                    props.Set(pyluxcore.Property('scene.textures.' + fk_dummy_tex + '.type', 'fresnelapproxk'))
                    props.Set(pyluxcore.Property('scene.textures.' + fk_dummy_tex + '.texture',
                                                 self.ConvertMaterialChannel(luxMat, 'Kr', 'color')))
                # TODO: nk_data and fresneltex
                else:
                    LuxLog('WARNING: Not yet supported metal2 type: %s' % m2_type)

                props.Set(pyluxcore.Property(prefix + '.uroughness',
                                             self.ConvertMaterialChannel(luxMat, 'uroughness', 'float')))

                props.Set(pyluxcore.Property(prefix + '.vroughness',
                                             self.ConvertMaterialChannel(luxMat, 'vroughness', 'float')))
            ####################################################################
            # Mirror
            ####################################################################
            elif matType == 'mirror':
                props.Set(pyluxcore.Property(prefix + '.type', ['mirror']))
                props.Set(pyluxcore.Property(prefix + '.kr', self.ConvertMaterialChannel(luxMat, 'Kr', 'color')))
            ####################################################################
            # Glossy
            ####################################################################
            elif matType == 'glossy':
                props.Set(pyluxcore.Property(prefix + '.type', ['glossy2']))
                props.Set(pyluxcore.Property(prefix + '.kd', self.ConvertMaterialChannel(luxMat, 'Kd', 'color')))

                if material.luxrender_material.luxrender_mat_glossy.useior:
                    props.Set(
                        pyluxcore.Property(prefix + '.index', self.ConvertMaterialChannel(luxMat, 'index', 'float')))
                else:
                    props.Set(pyluxcore.Property(prefix + '.ks', self.ConvertMaterialChannel(luxMat, 'Ks', 'color')))

                props.Set(pyluxcore.Property(prefix + '.ka', self.ConvertMaterialChannel(luxMat, 'Ka', 'color')))
                props.Set(pyluxcore.Property(prefix + '.multibounce',
                                             material.luxrender_material.luxrender_mat_glossy.multibounce))

                props.Set(pyluxcore.Property(prefix + '.sigma', self.ConvertMaterialChannel(luxMat, 'sigma', 'float')))
                props.Set(pyluxcore.Property(prefix + '.d', self.ConvertMaterialChannel(luxMat, 'd', 'float')))

                props.Set(pyluxcore.Property(prefix + '.uroughness',
                                             self.ConvertMaterialChannel(luxMat, 'uroughness', 'float')))

                props.Set(pyluxcore.Property(prefix + '.vroughness',
                                             self.ConvertMaterialChannel(luxMat, 'vroughness', 'float')))

            ####################################################################
            # Glossytranslucent
            ####################################################################
            elif matType == 'glossytranslucent':
                props.Set(pyluxcore.Property(prefix + '.type', ['glossytranslucent']))
                props.Set(pyluxcore.Property(prefix + '.kt', self.ConvertMaterialChannel(luxMat, 'Kt', 'color')))
                props.Set(pyluxcore.Property(prefix + '.kd', self.ConvertMaterialChannel(luxMat, 'Kd', 'color')))

                if material.luxrender_material.luxrender_mat_glossy.useior:
                    props.Set(
                        pyluxcore.Property(prefix + '.index', self.ConvertMaterialChannel(luxMat, 'index', 'float')))
                else:
                    props.Set(pyluxcore.Property(prefix + '.ks', self.ConvertMaterialChannel(luxMat, 'Ks', 'color')))

                props.Set(pyluxcore.Property(prefix + '.ka', self.ConvertMaterialChannel(luxMat, 'Ka', 'color')))
                props.Set(pyluxcore.Property(prefix + '.multibounce',
                                             material.luxrender_material.luxrender_mat_glossytranslucent.multibounce))

                props.Set(pyluxcore.Property(prefix + '.d', self.ConvertMaterialChannel(luxMat, 'd', 'float')))

                props.Set(pyluxcore.Property(prefix + '.uroughness',
                                             self.ConvertMaterialChannel(luxMat, 'uroughness', 'float')))

                props.Set(pyluxcore.Property(prefix + '.vroughness',
                                             self.ConvertMaterialChannel(luxMat, 'vroughness', 'float')))

                # Backface values
                if material.luxrender_material.luxrender_mat_glossytranslucent.two_sided:
                    if material.luxrender_material.luxrender_mat_glossytranslucent.bf_useior:
                        props.Set(pyluxcore.Property(prefix + '.index_bf',
                                                     self.ConvertMaterialChannel(luxMat, 'bf_index', 'float')))
                    else:
                        props.Set(pyluxcore.Property(prefix + '.ks_bf',
                                                     self.ConvertMaterialChannel(luxMat, 'backface_Ks', 'color')))

                    props.Set(pyluxcore.Property(prefix + '.ka_bf',
                                                 self.ConvertMaterialChannel(luxMat, 'backface_Ka', 'color')))
                    props.Set(pyluxcore.Property(prefix + '.multibounce_bf',
                                    material.luxrender_material.luxrender_mat_glossytranslucent.backface_multibounce))

                    props.Set(pyluxcore.Property(prefix + '.d_bf',
                                                 self.ConvertMaterialChannel(luxMat, 'bf_d', 'float')))

                    props.Set(pyluxcore.Property(prefix + '.uroughness_bf',
                                                 self.ConvertMaterialChannel(luxMat, 'bf_uroughness', 'float')))

                    props.Set(pyluxcore.Property(prefix + '.vroughness_bf',
                                                 self.ConvertMaterialChannel(luxMat, 'bf_vroughness', 'float')))

            ####################################################################
            # Glass
            ####################################################################
            elif matType == 'glass':
                if not material.luxrender_material.luxrender_mat_glass.architectural:
                    props.Set(pyluxcore.Property(prefix + '.type', ['glass']))
                else:
                    props.Set(pyluxcore.Property(prefix + '.type', ['archglass']))

                props.Set(pyluxcore.Property(prefix + '.kr', self.ConvertMaterialChannel(luxMat, 'Kr', 'color')))
                props.Set(pyluxcore.Property(prefix + '.kt', self.ConvertMaterialChannel(luxMat, 'Kt', 'color')))

                props.Set(pyluxcore.Property(prefix + '.cauchyb', self.ConvertMaterialChannel(luxMat,
                                                                                              'cauchyb', 'float')))

                props.Set(pyluxcore.Property(prefix + '.film', self.ConvertMaterialChannel(luxMat,
                                                                                           'film', 'float')))

                props.Set(pyluxcore.Property(prefix + '.interiorior', self.ConvertMaterialChannel(luxMat,
                                                                                                  'index', 'float')))

                props.Set(pyluxcore.Property(prefix + '.filmindex', self.ConvertMaterialChannel(luxMat,
                                                                                                'filmindex', 'float')))
            ####################################################################
            # Glass2
            ####################################################################
            elif matType == 'glass2':
                if not material.luxrender_material.luxrender_mat_glass2.architectural:
                    props.Set(pyluxcore.Property(prefix + '.type', ['glass']))
                else:
                    props.Set(pyluxcore.Property(prefix + '.type', ['archglass']))

                props.Set(pyluxcore.Property(prefix + '.kr', '1.0 1.0 1.0'))
                props.Set(pyluxcore.Property(prefix + '.kt', '1.0 1.0 1.0'))

            ####################################################################
            # Roughlass
            ####################################################################
            elif matType == 'roughglass':
                props.Set(pyluxcore.Property(prefix + '.type', ['roughglass']))
                props.Set(pyluxcore.Property(prefix + '.kr', self.ConvertMaterialChannel(luxMat, 'Kr', 'color')))
                props.Set(pyluxcore.Property(prefix + '.kt', self.ConvertMaterialChannel(luxMat, 'Kt', 'color')))

                props.Set(pyluxcore.Property(prefix + '.cauchyb', self.ConvertMaterialChannel(luxMat, 'cauchyb',
                                                                                              'float')))
                props.Set(pyluxcore.Property(prefix + '.interiorior', self.ConvertMaterialChannel(luxMat, 'index',
                                                                                                  'float')))
                props.Set(pyluxcore.Property(prefix + '.uroughness',
                                             self.ConvertMaterialChannel(luxMat, 'uroughness', 'float')))

                props.Set(pyluxcore.Property(prefix + '.vroughness',
                                             self.ConvertMaterialChannel(luxMat, 'vroughness', 'float')))

            ####################################################################
            # Cloth
            ####################################################################
            elif matType == 'cloth':
                props.Set(pyluxcore.Property(prefix + '.type', ['cloth']))
                props.Set(
                    pyluxcore.Property(prefix + '.preset', material.luxrender_material.luxrender_mat_cloth.presetname))
                props.Set(
                    pyluxcore.Property(prefix + '.warp_kd', self.ConvertMaterialChannel(luxMat, 'warp_Kd', 'color')))
                props.Set(
                    pyluxcore.Property(prefix + '.warp_ks', self.ConvertMaterialChannel(luxMat, 'warp_Ks', 'color')))
                props.Set(
                    pyluxcore.Property(prefix + '.weft_kd', self.ConvertMaterialChannel(luxMat, 'weft_Kd', 'color')))
                props.Set(
                    pyluxcore.Property(prefix + '.weft_ks', self.ConvertMaterialChannel(luxMat, 'weft_Ks', 'color')))
                props.Set(
                    pyluxcore.Property(prefix + '.repeat_u', material.luxrender_material.luxrender_mat_cloth.repeat_u))
                props.Set(
                    pyluxcore.Property(prefix + '.repeat_v', material.luxrender_material.luxrender_mat_cloth.repeat_v))

            ####################################################################
            # Carpaint
            ####################################################################
            elif matType == 'carpaint':
                props.Set(pyluxcore.Property(prefix + '.type', ['carpaint']))
                props.Set(
                    pyluxcore.Property(prefix + '.preset', material.luxrender_material.luxrender_mat_carpaint.name))
                props.Set(pyluxcore.Property(prefix + '.kd', self.ConvertMaterialChannel(luxMat, 'Kd', 'color')))
                props.Set(pyluxcore.Property(prefix + '.ka', self.ConvertMaterialChannel(luxMat, 'Ka', 'color')))
                props.Set(pyluxcore.Property(prefix + '.ks1', self.ConvertMaterialChannel(luxMat, 'Ks1', 'color')))
                props.Set(pyluxcore.Property(prefix + '.ks2', self.ConvertMaterialChannel(luxMat, 'Ks2', 'color')))
                props.Set(pyluxcore.Property(prefix + '.ks3', self.ConvertMaterialChannel(luxMat, 'Ks3', 'color')))
                props.Set(pyluxcore.Property(prefix + '.d', self.ConvertMaterialChannel(luxMat, 'd', 'float')))
                props.Set(pyluxcore.Property(prefix + '.m1',
                                             material.luxrender_material.luxrender_mat_carpaint.M1_floatvalue))
                props.Set(pyluxcore.Property(prefix + '.m2',
                                             material.luxrender_material.luxrender_mat_carpaint.M2_floatvalue))
                props.Set(pyluxcore.Property(prefix + '.m3',
                                             material.luxrender_material.luxrender_mat_carpaint.M3_floatvalue))
                props.Set(pyluxcore.Property(prefix + '.r1',
                                             material.luxrender_material.luxrender_mat_carpaint.R1_floatvalue))
                props.Set(pyluxcore.Property(prefix + '.r2',
                                             material.luxrender_material.luxrender_mat_carpaint.R2_floatvalue))
                props.Set(pyluxcore.Property(prefix + '.r3',
                                             material.luxrender_material.luxrender_mat_carpaint.R3_floatvalue))

            ####################################################################
            # Velvet
            ####################################################################
            elif matType == 'velvet':
                props.Set(pyluxcore.Property(prefix + '.type', ['velvet']))
                props.Set(pyluxcore.Property(prefix + '.kd', self.ConvertMaterialChannel(luxMat, 'Kd', 'color')))
                props.Set(pyluxcore.Property(prefix + '.thickness',
                                             material.luxrender_material.luxrender_mat_velvet.thickness))
                props.Set(pyluxcore.Property(prefix + '.p1', material.luxrender_material.luxrender_mat_velvet.p1))
                props.Set(pyluxcore.Property(prefix + '.p2', material.luxrender_material.luxrender_mat_velvet.p2))
                props.Set(pyluxcore.Property(prefix + '.p3', material.luxrender_material.luxrender_mat_velvet.p3))

            ####################################################################
            # Null
            ####################################################################
            elif matType == 'null':
                props.Set(pyluxcore.Property(prefix + '.type', ['null']))

            ####################################################################
            # Mix
            ####################################################################
            elif matType == 'mix':
                if not material.luxrender_material.luxrender_mat_mix.namedmaterial1_material or \
                        not material.luxrender_material.luxrender_mat_mix.namedmaterial2_material:
                    return 'LUXBLEND_LUXCORE_CLAY_MATERIAL'
                else:
                    try:
                        material_1_name = material.luxrender_material.luxrender_mat_mix.namedmaterial1_material
                        material_2_name = material.luxrender_material.luxrender_mat_mix.namedmaterial2_material

                        if materials is not None:
                            # obj.material_slots passed as argument
                            mat1 = materials[material_1_name].material
                            mat2 = materials[material_2_name].material
                        else:
                            # no material_slots available, get materials from bpy.data.materials
                            mat1 = bpy.data.materials[material_1_name]
                            mat2 = bpy.data.materials[material_2_name]

                        mat1Name = self.ConvertMaterial(mat1, materials)
                        mat2Name = self.ConvertMaterial(mat2, materials)

                        props.Set(pyluxcore.Property(prefix + '.type', ['mix']))
                        props.Set(pyluxcore.Property(prefix + '.material1', mat1Name))
                        props.Set(pyluxcore.Property(prefix + '.material2', mat2Name))
                        props.Set(pyluxcore.Property(prefix + '.amount',
                                                     self.ConvertMaterialChannel(luxMat, 'amount', 'float')))
                    except Exception as err:
                        LuxLog('WARNING: unable to convert mix material %s\n%s' % (material.name, err))
                        import traceback
                        traceback.print_exc()
                        return 'LUXBLEND_LUXCORE_CLAY_MATERIAL'

            ####################################################################
            # Fallback
            ####################################################################
            else:
                return 'LUXBLEND_LUXCORE_CLAY_MATERIAL'

            ####################################################################
            # Common settings for all material types
            ####################################################################
            if not translator_settings.override_materials:
                # Common material settings
                if material.luxrender_material.bumpmap_usefloattexture:
                    luxMap = material.luxrender_material.bumpmap_floattexturename
                    props.Set(
                        pyluxcore.Property(prefix + '.bumptex', self.ConvertCommonChannel(luxMap, material, 'bumpmap')))

                if material.luxrender_material.normalmap_usefloattexture:
                    luxMap = material.luxrender_material.normalmap_floattexturename
                    props.Set(
                        pyluxcore.Property(prefix + '.normaltex', self.ConvertCommonChannel(luxMap, material, 'normalmap')))

                set_volumes(prefix)

            # LuxCore specific material settings
            if material.luxcore_material.id != -1:
                props.Set(pyluxcore.Property(prefix + '.id', [material.luxcore_material.id]))
                if material.luxcore_material.create_MATERIAL_ID_MASK and self.blScene.luxrender_channels.enable_aovs:
                    self.createChannelOutputString('MATERIAL_ID_MASK', material.luxcore_material.id)
                if material.luxcore_material.create_BY_MATERIAL_ID and self.blScene.luxrender_channels.enable_aovs:
                    self.createChannelOutputString('BY_MATERIAL_ID', material.luxcore_material.id)

            props.Set(pyluxcore.Property(prefix + '.samples', [material.luxcore_material.samples]))
            props.Set(pyluxcore.Property(prefix + '.emission.samples', [material.luxcore_material.emission_samples]))
            props.Set(
                pyluxcore.Property(prefix + '.bumpsamplingdistance', [material.luxcore_material.bumpsamplingdistance]))

            props.Set(pyluxcore.Property(prefix + '.visibility.indirect.diffuse.enable',
                                         material.luxcore_material.visibility_indirect_diffuse_enable))
            props.Set(pyluxcore.Property(prefix + '.visibility.indirect.glossy.enable',
                                         material.luxcore_material.visibility_indirect_glossy_enable))
            props.Set(pyluxcore.Property(prefix + '.visibility.indirect.specular.enable',
                                         material.luxcore_material.visibility_indirect_specular_enable))

            if not (translator_settings.override_materials and translator_settings.override_lights):
                # LuxRender emission
                if material.luxrender_emission.use_emission:
                    emit_enabled = self.blScene.luxrender_lightgroups.is_enabled(material.luxrender_emission.lightgroup)
                    emit_enabled &= (material.luxrender_emission.L_color.v * material.luxrender_emission.gain) > 0.0
                    if emit_enabled:
                        props.Set(pyluxcore.Property(prefix + '.emission',
                                                     self.ConvertMaterialChannel(material.luxrender_emission, 'L',
                                                                                 'color')))
                        props.Set(pyluxcore.Property(prefix + '.emission.gain', [
                            material.luxrender_emission.gain, material.luxrender_emission.gain,
                            material.luxrender_emission.gain]))
                        props.Set(pyluxcore.Property(prefix + '.emission.power', material.luxrender_emission.power))
                        props.Set(pyluxcore.Property(prefix + '.emission.efficency', material.luxrender_emission.efficacy))

                        if not self.blScene.luxrender_lightgroups.ignore:
                            lightgroup = material.luxrender_emission.lightgroup
                            if lightgroup in self.lightgroups_cache:
                                # there is already an material with this lightgroup, use the same id
                                lightgroup_id = self.lightgroups_cache[lightgroup]
                            else:
                                # this is the first material to use this lightgroup, add an entry with a new id
                                lightgroup_id = len(self.lightgroups_cache)
                                self.lightgroups_cache[lightgroup] = lightgroup_id

                            props.Set(pyluxcore.Property(prefix + '.emission.id', [lightgroup_id]))

            # alpha transparency
            use_alpha_transparency = False
            name_mix = matName + '_alpha_mix'

            if hasattr(material, 'luxrender_transparency') and material.luxrender_transparency.transparent:
                use_alpha_transparency = True

                name_null = 'LUXBLEND_LUXCORE_NULL_MATERIAL' # created in self.Convert()

                alpha = [0.0]

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
                        texture = bpy.data.textures[texture_name]
                        alpha = self.ConvertTexture(texture, ToValidLuxCoreName(texture_name + material.name + '_alpha'))

                        props.Set(pyluxcore.Property('scene.textures.' + alpha + '.channel', ['alpha']))

                        if material.luxrender_transparency.inverse:
                            sv = BlenderSceneConverter.next_scale_value()
                            inverter_name = alpha + '_inverter_' + str(sv)
                            inverter_prefix = 'scene.textures.' + inverter_name

                            props.Set(pyluxcore.Property(inverter_prefix + '.type', ['mix']))
                            props.Set(pyluxcore.Property(inverter_prefix + '.amount', alpha))
                            props.Set(pyluxcore.Property(inverter_prefix + '.texture1', [1.0]))
                            props.Set(pyluxcore.Property(inverter_prefix + '.texture2', [0.0]))

                            alpha = inverter_name

                elif alpha_source == 'constant':
                    alpha = material.luxrender_transparency.alpha_value

                # diffusealpha, diffusemean, diffuseintensity
                elif material.luxrender_material.type in sourceMap:
                    # Get base texture name
                    texture_name = getattr(luxMat, '%s_colortexturename' % sourceMap[material.luxrender_material.type])

                    try:
                        # Get blender texture
                        texture = bpy.data.textures[texture_name]
                        # Export texture, get luxcore texture name
                        alpha = self.ConvertTexture(texture, ToValidLuxCoreName(texture_name + material.name + '_alpha'))

                        channelMap = {
                        'diffusealpha': 'alpha',
                        'diffusemean': 'mean',
                        'diffuseintensity': 'colored_mean',
                        }
                        props.Set(pyluxcore.Property('scene.textures.' + alpha + '.channel', [channelMap[alpha_source]]))

                    except KeyError:
                        LuxLog('Texturename %s is not in bpy.data.textures' % texture_name)
                        use_alpha_transparency = False
                else:
                    LuxLog('WARNING: alpha transparency not supported for material type %s' % material.luxrender_material.type)
                    use_alpha_transparency = False

                if use_alpha_transparency:
                    mix_prefix = 'scene.materials.' + name_mix
                    props.Set(pyluxcore.Property(mix_prefix + '.type', ['mix']))
                    props.Set(pyluxcore.Property(mix_prefix + '.material1', name_null))
                    props.Set(pyluxcore.Property(mix_prefix + '.material2', matName))
                    props.Set(pyluxcore.Property(mix_prefix + '.amount', alpha))

                    set_volumes(mix_prefix)

            self.scnProps.Set(props)
            self.materialsCache.add(matName)

            if use_alpha_transparency:
                self.materialsCache.add(name_mix)
                return name_mix
            else:
                return matName
        except Exception as err:
            LuxLog('Material export failed, skipping material: %s\n%s' % (material.name, err))
            import traceback
            traceback.print_exc()

            return 'LUXBLEND_LUXCORE_CLAY_MATERIAL'

    def ConvertParamToLuxcoreProperty(self, param):
        """
        Convert Luxrender parameters of the form
        ['float gain', 1.0]
        to LuxCore property format

        Returns list of parsed values without type specifier
        e.g. ['gain', 1.0]
        """

        parsed = param[0].split(' ')
        parsed.pop(0)

        return [parsed[0], param[1]]

    def ConvertLight(self, obj):
        if not is_obj_visible(self.blScene, obj):
            hide_lamp = True
        else:
            hide_lamp = False

        light = obj.data
        luxcore_name = ToValidLuxCoreName(obj.name)

        # data to cache all exported lights later
        luxcore_data = []
        if light.type != 'SUN':
            luxcore_data.append(ExportedObjectData(luxcore_name, lightType = light.type))

        light_params = ParamSet() \
            .add_float('gain', light.energy) \
            .add_float('importance', light.luxrender_lamp.importance)

        # Params from light sub-types
        light_params.update(getattr(light.luxrender_lamp, 'luxrender_lamp_%s' % light.type.lower()).get_paramset(obj))

        params_converted = []
        for rawParam in light_params:
            params_converted.append(self.ConvertParamToLuxcoreProperty(rawParam))

        params_keyValue = {}
        for param in params_converted:
            params_keyValue[param[0]] = param[1]

        # Common light params
        lux_lamp = getattr(light.luxrender_lamp, 'luxrender_lamp_%s' % light.type.lower())
        energy = params_keyValue['gain'] if not hide_lamp else 0  # workaround for no lights render recovery
        position = bpy.data.objects[obj.name].location
        importance = params_keyValue['importance']
        lightgroup = getattr(light.luxrender_lamp, 'lightgroup')
        lightgroup_id = -1 # for luxcore RADIANCE_GROUP

        if lightgroup != '':
            lightgroup_enabled = self.blScene.luxrender_lightgroups.lightgroups[lightgroup].lg_enabled
            if lightgroup_enabled:
                energy *= self.blScene.luxrender_lightgroups.lightgroups[lightgroup].gain

                if lightgroup in self.lightgroups_cache:
                    # lightgroup already has a luxcore id, use it
                    lightgroup_id = self.lightgroups_cache[lightgroup]
                else:
                    # this is the first material to use this lightgroup, add an entry with a new id
                    lightgroup_id = len(self.lightgroups_cache)
                    self.lightgroups_cache[lightgroup] = lightgroup_id
            else:
                energy = 0  # use gain for muting to keep geometry exported

        if lightgroup_id != -1 and light.type != 'SUN' and not self.blScene.luxrender_lightgroups.ignore:
            self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.id', [lightgroup_id]))

        gain_spectrum = [energy, energy, energy] # luxcore gain is spectrum!

        # not for distant light,
        # not for area lamps (because these are meshlights and gain is controlled by material settings
        if getattr(lux_lamp, 'L_color') and not (
                    light.type == 'SUN' and getattr(lux_lamp, 'sunsky_type') != 'distant') and not (
                    light.type == 'AREA' and not light.luxrender_lamp.luxrender_lamp_laser.is_laser):
            iesfile = getattr(light.luxrender_lamp, 'iesname')
            iesfile, basename = get_expanded_file_name(light, iesfile)
            if iesfile != '':
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.iesfile', iesfile))

            # Workaround for lights without color, multiply gain with color here
            if (light.type == 'HEMI' and (not getattr(lux_lamp, 'infinite_map')
                                          or getattr(lux_lamp, 'hdri_multiply'))) or light.type == 'SPOT':
                colorRaw = getattr(lux_lamp, 'L_color') * energy
                gain_spectrum = [colorRaw[0], colorRaw[1], colorRaw[2]]
            else:
                colorRaw = getattr(lux_lamp, 'L_color')
                color = [colorRaw[0], colorRaw[1], colorRaw[2]]
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.color', color))

            self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.gain', gain_spectrum))
            self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.importance', importance))

        ####################################################################
        # Sun (includes sun, sky, distant)
        ####################################################################
        if light.type == 'SUN':
            invmatrix = obj.matrix_world.inverted()
            sundir = [invmatrix[2][0], invmatrix[2][1], invmatrix[2][2]]
            samples = params_keyValue['nsamples']

            sunsky_type = light.luxrender_lamp.luxrender_lamp_sun.sunsky_type
            legacy_sky = light.luxrender_lamp.luxrender_lamp_sun.legacy_sky

            if 'sun' in sunsky_type:
                name = luxcore_name + '_sun'
                luxcore_data.append(ExportedObjectData(name, lightType = light.type))
                if lightgroup_id != -1 and not self.blScene.luxrender_lightgroups.ignore:
                    self.scnProps.Set(pyluxcore.Property('scene.lights.' + name + '.id', [lightgroup_id]))

                turbidity = params_keyValue['turbidity']

                self.scnProps.Set(pyluxcore.Property('scene.lights.' + name + '.type', ['sun']))
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + name + '.turbidity', [turbidity]))
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + name + '.dir', sundir))
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + name + '.gain', gain_spectrum))
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + name + '.importance', importance))
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + name + '.samples', [samples]))

                if 'relsize' in params_keyValue:
                    relsize = params_keyValue['relsize']
                    self.scnProps.Set(pyluxcore.Property('scene.lights.' + name + '.relsize', [relsize]))

            if 'sky' in sunsky_type:
                name = luxcore_name + '_sky'
                luxcore_data.append(ExportedObjectData(name, lightType = light.type))
                if lightgroup_id != -1 and not self.blScene.luxrender_lightgroups.ignore:
                    self.scnProps.Set(pyluxcore.Property('scene.lights.' + name + '.id', [lightgroup_id]))

                turbidity = params_keyValue['turbidity']
                skyVersion = 'sky' if legacy_sky else 'sky2'

                self.scnProps.Set(pyluxcore.Property('scene.lights.' + name + '.type', [skyVersion]))
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + name + '.turbidity', [turbidity]))
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + name + '.dir', sundir))
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + name + '.gain', gain_spectrum))
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + name + '.importance', importance))
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + name + '.samples', [samples]))

            if sunsky_type == 'distant':
                luxcore_data.append(ExportedObjectData(luxcore_name, lightType = light.type))
                if lightgroup_id != -1 and not self.blScene.luxrender_lightgroups.ignore:
                    self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.id', [lightgroup_id]))

                distant_dir = [-sundir[0], -sundir[1], -sundir[2]]

                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.type', ['distant']))
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.direction', distant_dir))

                if 'theta' in params_keyValue:
                    theta = params_keyValue['theta']
                    self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.theta', [theta]))

        ####################################################################
        # Hemi (infinite)
        ####################################################################
        elif light.type == 'HEMI':
            infinite_map_path = getattr(lux_lamp, 'infinite_map')
            if infinite_map_path:
                infinite_map_path_abs, basename = get_expanded_file_name(light, infinite_map_path)
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.type', ['infinite']))
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.file', infinite_map_path_abs))
            else:
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.type', ['constantinfinite']))

            self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.gamma', getattr(lux_lamp, 'gamma')))
            hemi_fix = mathutils.Matrix.Scale(1.0, 4)  # create new scale matrix 4x4
            hemi_fix[0][0] = -1.0  # mirror the hdri_map
            transform = matrix_to_list(hemi_fix * obj.matrix_world.inverted())
            self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.transformation', transform))

        ####################################################################
        # Point
        ####################################################################
        elif light.type == 'POINT':
            # if getattr(lux_lamp, 'usesphere'):
            # print('------------------------', getattr(lux_lamp, 'pointsize'))
            if iesfile:
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.type', ['mappoint']))
            else:
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.type', ['point']))

            if getattr(lux_lamp, 'flipz'):
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.flipz', lux_lamp.flipz))

            transform = matrix_to_list(obj.matrix_world)
            self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.transformation', transform))
            self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.position', [0.0, 0.0, 0.0]))
            self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.power', getattr(lux_lamp, 'power')))
            self.scnProps.Set(
                pyluxcore.Property('scene.lights.' + luxcore_name + '.efficency', getattr(lux_lamp, 'efficacy')))

        ####################################################################
        # Spot (includes projector)
        ####################################################################
        elif light.type == 'SPOT':
            coneangle = math.degrees(light.spot_size) * 0.5
            conedeltaangle = math.degrees(light.spot_size * 0.5 * light.spot_blend)
            if getattr(lux_lamp, 'projector'):
                projector_map_path = getattr(lux_lamp, 'mapname')
                projector_map_path_abs, basename = get_expanded_file_name(light, projector_map_path)
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.type', ['projection']))
                self.scnProps.Set(
                    pyluxcore.Property('scene.lights.' + luxcore_name + '.mapfile', projector_map_path_abs))
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.fov', coneangle * 2))
            else:
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.type', ['spot']))

            spot_fix = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'Z')  # match to lux
            transform = matrix_to_list(obj.matrix_world * spot_fix)
            self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.transformation', transform))
            self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.position', [0.0, 0.0, 0.0]))
            self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.target', [0.0, 0.0, -1.0]))

            self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.coneangle', coneangle))
            self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.conedeltaangle', conedeltaangle))
            self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.power', getattr(lux_lamp, 'power')))
            self.scnProps.Set(
                pyluxcore.Property('scene.lights.' + luxcore_name + '.efficency', getattr(lux_lamp, 'efficacy')))
        
        ####################################################################
        # Area (includes laser)
        ####################################################################
        elif light.type == 'AREA':
            if light.luxrender_lamp.luxrender_lamp_laser.is_laser:
                # Laser lamp
                transform = matrix_to_list(obj.matrix_world)
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.transformation', transform))
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.position', [0.0, 0.0, 0.0]))
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.type', ['laser']))
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.target', [0.0, 0.0, -1.0]))
                self.scnProps.Set(pyluxcore.Property('scene.lights.' + luxcore_name + '.radius', [light.size]))
            else:
                # Area lamp workaround: create plane and add emitting material
                mat_name = luxcore_name + '_helper_mat'
                # TODO: match with API 1.x
                # overwrite gain with a gain scaled by ws^2 to account for change in lamp area
                raw_color = light.luxrender_lamp.luxrender_lamp_area.L_color * energy * (get_worldscale(as_scalematrix=False) ** 2) #* 20000
                emission_color = [raw_color[0], raw_color[1], raw_color[2]]

                #light_params.add_float('gain', light.energy * lg_gain * (get_worldscale(as_scalematrix=False) ** 2))

                self.scnProps.Set(pyluxcore.Property('scene.materials.' + mat_name + '.type', ['matte']))
                self.scnProps.Set(pyluxcore.Property('scene.materials.' + mat_name + '.kd', [0.0, 0.0, 0.0]))
                self.scnProps.Set(pyluxcore.Property('scene.materials.' + mat_name + '.power', [light.luxrender_lamp.luxrender_lamp_area.power]))
                self.scnProps.Set(pyluxcore.Property('scene.materials.' + mat_name + '.efficiency', [light.luxrender_lamp.luxrender_lamp_area.efficacy]))

                translator_settings = self.blScene.luxcore_translatorsettings
                if not (translator_settings.override_materials and translator_settings.override_lights):
                    self.scnProps.Set(pyluxcore.Property('scene.materials.' + mat_name + '.emission', emission_color))

                # assign material to object
                self.scnProps.Set(pyluxcore.Property('scene.objects.' + luxcore_name + '.material', [mat_name]))
                
                # add mesh
                mesh_name = 'Mesh-' + luxcore_name
                if not self.lcScene.IsMeshDefined(mesh_name):
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
                    self.lcScene.DefineMesh(mesh_name, vertices, faces, None, None, None, None)
                # assign mesh to object
                self.scnProps.Set(pyluxcore.Property('scene.objects.' + luxcore_name + '.ply', [mesh_name]))
                    
                # copy transformation of area lamp object
                scale_matrix = mathutils.Matrix()
                scale_matrix[0][0] = light.size / 2.0 * obj.scale.x
                scale_matrix[1][1] = light.size_y / 2.0 if light.shape == 'RECTANGLE' else light.size / 2.0
                scale_matrix[1][1] *= obj.scale.y
                rotation_matrix = obj.rotation_euler.to_matrix()
                rotation_matrix.resize_4x4()
                transform_matrix = mathutils.Matrix()
                transform_matrix[0][3] = obj.location.x
                transform_matrix[1][3] = obj.location.y
                transform_matrix[2][3] = obj.location.z
                
                transform = matrix_to_list(transform_matrix * rotation_matrix * scale_matrix)
                self.scnProps.Set(pyluxcore.Property('scene.objects.' + luxcore_name + '.transformation', transform))
                
        else:
            raise Exception('Unknown lighttype ' + light.type + ' for light: ' + obj.name)

        # create cache entry
        BlenderSceneConverter.export_cache.add_obj(obj, luxcore_data)

    def ConvertDuplis(self, obj, particle_system):
        """
        Converts duplis and OBJECT and GROUP particle systems
        """
        print('Exporting duplis of duplicator %s' % particle_system)

        try:
            obj.dupli_list_create(self.blScene, settings = 'RENDER')
            if not obj.dupli_list:
                raise Exception('cannot create dupli list for object %s' % obj.name)

            # Create our own DupliOb list to work around incorrect layers
            # attribute when inside create_dupli_list()..free_dupli_list()
            duplis = []
            for dupli_ob in obj.dupli_list:
                # metaballs are omitted from this function intentionally. Adding them causes recursion when building
                # the ball. (add 'META' to this if you actually want that bug, it makes for some fun glitch
                # art with particles)
                if dupli_ob.object.type not in ['MESH', 'SURFACE', 'FONT', 'CURVE']:
                    continue
                if not is_obj_visible(self.blScene, dupli_ob.object, is_dupli = True):
                    continue

                duplis.append((dupli_ob.object, dupli_ob.matrix.copy()))

            obj.dupli_list_clear()
            self.dupli_amount = len(duplis)

            # dupli object, dupli matrix
            for dupli_object, dupli_matrix in duplis:
                # Check for group layer visibility, if the object is in a group
                group_visible = len(dupli_object.users_group) == 0

                for group in dupli_object.users_group:
                    group_visible |= True in [a & b for a, b in zip(dupli_object.layers, group.layers)]

                if not group_visible:
                    continue

                self.ConvertObject(dupli_object, matrix = dupli_matrix, is_dupli = True, particle_sytem = particle_system)

            del duplis
            self.dupli_number = 0

            print('Dupli export finished')
        except Exception as err:
            LuxLog('Error in ConvertDuplis for object %s: %s' % (obj, err))
            import traceback
            traceback.print_exc()

    def ConvertHair(self):
        """
        Converts PATH type particle systems (hair systems)
        """
        print('Hair export not supported yet')

    def SetObjectProperties(self, lcObjName, lcMeshName, lcMatName, transform):
        self.scnProps.Set(pyluxcore.Property('scene.objects.' + lcObjName + '.material', [lcMatName]))
        self.scnProps.Set(pyluxcore.Property('scene.objects.' + lcObjName + '.ply', [lcMeshName]))

        if transform is not None:
            self.scnProps.Set(pyluxcore.Property('scene.objects.' + lcObjName + '.transformation', transform))

    def ExportMesh(self, obj, preview, update_mesh, update_material, transform, is_dupli):
        meshDefinitions = []
        meshDefinitions.extend(self.ConvertObjectGeometry(obj, preview, update_mesh, is_dupli))
        luxcore_data = []

        for meshDefinition in meshDefinitions:
            lcObjName = meshDefinition[0]
            objMatIndex = meshDefinition[1]

            # Convert the (main) material
            try:
                objMat = obj.material_slots[objMatIndex].material
            except IndexError:
                objMat = None
                LuxLog('WARNING: material slot %d on object \"%s\" is unassigned!' % (objMatIndex + 1, obj.name))

            objMatName = self.ConvertMaterial(objMat, obj.material_slots, no_conversion = not update_material)
            objMeshName = 'Mesh-' + lcObjName

            # Add to cache
            exported_object_data = ExportedObjectData(lcObjName, objMeshName, objMatName, objMatIndex)
            luxcore_data.append(exported_object_data)

            self.SetObjectProperties(lcObjName, objMeshName, objMatName, transform)

        return luxcore_data

    def ConvertObject(self, obj, matrix = None, is_dupli = False, particle_sytem = '', preview = False,
                      update_mesh = True, update_transform = True, update_material = True):
        if obj is None or (self.renderengine is not None and self.renderengine.test_break()):
            return

        if obj.type == 'LAMP':
            try:
                self.ConvertLight(obj)
            except Exception as err:
                LuxLog('Light export failed, skipping light: %s\n%s' % (obj.name, err))
                import traceback
                traceback.print_exc()
            return

        convert_object = True

        transform = None
        if update_transform:
            if matrix is not None:
                transform = matrix_to_list(matrix)
            else:
                transform = matrix_to_list(obj.matrix_world, apply_worldscale=True)

        # check if object is proxy
        if obj.luxrender_object.append_proxy and obj.luxrender_object.proxy_type == 'plymesh':
            convert_object = not obj.luxrender_object.hide_proxy_mesh

            path = efutil.filesystem_path(obj.luxrender_object.external_mesh)
            name = ToValidLuxCoreName(obj.name)
            material = self.ConvertMaterial(obj.active_material, obj.material_slots, no_conversion = not update_material)

            self.SetObjectProperties(name, path, material, transform)

        # check if object is particle emitter
        if len(obj.particle_systems) > 0:
            convert_object = False

            for psys in obj.particle_systems:
                convert_object = convert_object or psys.settings.use_render_emitter

                if self.blScene.luxcore_translatorsettings.export_particles:
                    if psys.settings.render_type in ['OBJECT', 'GROUP']:
                        self.ConvertDuplis(obj, psys.name)
                    elif psys.settings.render_type == 'PATH':
                        self.ConvertHair()

        # Check if object is duplicator
        if obj.is_duplicator and len(obj.particle_systems) < 1:
            if obj.dupli_type in ['FACES', 'GROUP', 'VERTS']:
                self.ConvertDuplis(obj, obj.name)

        # Some dupli types should hide the original
        if obj.is_duplicator and obj.dupli_type in ('VERTS', 'FACES', 'GROUP'):
            convert_object = False

        if not is_obj_visible(self.blScene, obj, is_dupli = is_dupli) or not convert_object or obj.data is None:
            return

        cache = BlenderSceneConverter.export_cache

        # Check if mesh was already exported
        if cache.has_obj_data(obj.data):
            # Check if this object was already exported
            if cache.has_obj(obj) and not is_dupli:
                # object was already exported
                print('[Data: %s][Object: %s] obj already in cache' % (obj.data.name, obj.name))

                if update_mesh and obj.data.users == 1:
                    # re-export mesh (disabled for multiuser meshes because it crashes Blender)
                    cache.add_obj(obj, self.ExportMesh(obj, preview, update_mesh, update_material, transform, is_dupli))
                else:
                    # read from cache (only transformation update required)
                    exported_object = cache.get_exported_object_key_obj(obj)
                    for exported_object_data in exported_object.luxcore_data:
                        self.SetObjectProperties(exported_object_data.lcObjName, exported_object_data.lcMeshName,
                                                 exported_object_data.lcMaterialName, transform)
            else:
                # Mesh data is already exported, but this object is not yet "registered" to use it
                if not is_dupli:
                    # Don't spam the log when thousands of duplis are exported
                    print('[Data: %s][Object: %s] no obj entry, creating one' % (obj.data.name, obj.name))

                exported_object = cache.get_exported_object_key_data(obj.data)
                new_luxcore_data = []

                for exported_object_data in exported_object.luxcore_data:
                    # Create unique name for the lcObject
                    name = ToValidLuxCoreName(obj.name + str(exported_object_data.matIndex))
                    if is_dupli:
                        name += '_%s_%d' % (particle_sytem, self.dupli_number)
                        self.dupli_number += 1

                        if self.dupli_number % 100 == 0 and self.renderengine is not None:
                            dupli_percent = float(self.dupli_number) / self.dupli_amount * 100.0
                            self.renderengine.update_stats('Exporting...', 'Duplicator %s (%d%%)' % (particle_sytem, dupli_percent))

                    new_exported_object_data = ExportedObjectData(name,
                                                                  exported_object_data.lcMeshName,
                                                                  exported_object_data.lcMaterialName,
                                                                  exported_object_data.matIndex)
                    new_luxcore_data.append(new_exported_object_data)

                    self.SetObjectProperties(name, exported_object_data.lcMeshName,
                                             exported_object_data.lcMaterialName, transform)

                # Create new entry in cache
                cache.add_obj(obj, new_luxcore_data)
        else:
            print('[Data: %s][Object: %s] mesh not in cache, exporting' % (obj.data.name, obj.name))
            cache.add_obj(obj, self.ExportMesh(obj, preview, update_mesh, update_material, transform, is_dupli))

    def convert_clipping_plane(self, lux_camera_settings):
        if lux_camera_settings.enable_clipping_plane:
            obj_name = lux_camera_settings.clipping_plane_obj

            try:
                obj = bpy.data.objects[obj_name]

                position = [obj.location.x, obj.location.y, obj.location.z]
                normal_vector = obj.rotation_euler.to_matrix() * mathutils.Vector((0.0, 0.0, 1.0))
                normal = [normal_vector.x, normal_vector.y, normal_vector.z]

                self.scnProps.Set(pyluxcore.Property('scene.camera.clippingplane.enable', [True]))
                self.scnProps.Set(pyluxcore.Property('scene.camera.clippingplane.center', position))
                self.scnProps.Set(pyluxcore.Property('scene.camera.clippingplane.normal', normal))
            except KeyError:
                # No valid clipping plane object selected
                self.scnProps.Set(pyluxcore.Property('scene.camera.clippingplane.enable', [False]))
        else:
            self.scnProps.Set(pyluxcore.Property('scene.camera.clippingplane.enable', [False]))

    def ConvertCamera(self):
        """
        Camera for final rendering
        """

        blCamera = self.blScene.camera
        blCameraData = blCamera.data
        luxCamera = blCameraData.luxrender_camera

        lookat = luxCamera.lookAt(blCamera)
        orig = list(lookat[0:3])
        target = list(lookat[3:6])
        up = list(lookat[6:9])
        self.scnProps.Set(pyluxcore.Property('scene.camera.lookat.orig', orig))
        self.scnProps.Set(pyluxcore.Property('scene.camera.lookat.target', target))
        self.scnProps.Set(pyluxcore.Property('scene.camera.up', up))

        if blCameraData.type == 'PERSP' and luxCamera.type == 'perspective':
            self.scnProps.Set(pyluxcore.Property('scene.camera.fieldofview', [math.degrees(blCameraData.angle)]))

        # border rendering
        if self.blScene.render.use_border:
            width, height = luxCamera.luxrender_film.resolution(self.blScene)
            self.scnProps.Set(pyluxcore.Property('scene.camera.screenwindow', luxCamera.screenwindow(
                width, height, self.blScene, blCameraData, luxcore_export=True)))

        if luxCamera.use_dof:
            # Do not world-scale this, it is already in meters!
            self.scnProps.Set(
                pyluxcore.Property('scene.camera.lensradius', (blCameraData.lens / 1000.0) / (2.0 * luxCamera.fstop)))

        ws = get_worldscale(as_scalematrix=False)

        if luxCamera.use_dof:
            if blCameraData.dof_object is not None:
                self.scnProps.Set(pyluxcore.Property('scene.camera.focaldistance', ws * (
                    (blCamera.location - blCameraData.dof_object.location).length)))
            elif blCameraData.dof_distance > 0:
                self.scnProps.Set(pyluxcore.Property('scene.camera.focaldistance', ws * blCameraData.dof_distance))

        if luxCamera.use_clipping:
            self.scnProps.Set(pyluxcore.Property('scene.camera.cliphither', ws * blCameraData.clip_start))
            self.scnProps.Set(pyluxcore.Property('scene.camera.clipyon', ws * blCameraData.clip_end))

        # arbitrary clipping plane
        self.convert_clipping_plane(luxCamera)

    def ConvertViewportCamera(self, context):
        """
        Camera for viewport rendering
        """

        view_persp = context.region_data.view_perspective
        view_matrix = mathutils.Matrix(context.region_data.view_matrix)
        view_lens = context.space_data.lens
        view_camera_zoom = context.region_data.view_camera_zoom
        view_camera_offset = list(context.region_data.view_camera_offset)

        luxCamera = context.scene.camera.data.luxrender_camera if context.scene.camera is not None else None

        if view_persp == 'ORTHO':
            raise Exception('Orthographic camera is not supported')
        else:
            lensradius = 0.0
            focaldistance = 0.0

            zoom = 1.0
            dx = 0.0
            dy = 0.0
            cam_trans = mathutils.Vector((view_matrix[0][3], view_matrix[1][3], view_matrix[2][3]))
            cam_lookat = list(context.region_data.view_location)

            rot = mathutils.Matrix(((-view_matrix[0][0], -view_matrix[1][0], -view_matrix[2][0]),
                                    (-view_matrix[0][1], -view_matrix[1][1], -view_matrix[2][1]),
                                    (-view_matrix[0][2], -view_matrix[1][2], -view_matrix[2][2])))

            cam_origin = list(rot * cam_trans)
            cam_fov = 2 * math.atan(0.5 * 32.0 / view_lens)
            cam_up = list(rot * mathutils.Vector((0, -1, 0)))

            if context.region.width > context.region.height:
                xaspect = 1.0
                yaspect = context.region.height / context.region.width
            else:
                xaspect = context.region.width / context.region.height
                yaspect = 1.0

            if view_persp == 'CAMERA':
                blcamera = context.scene.camera
                #magic zoom formula for camera viewport zoom from blender source
                zoom = view_camera_zoom
                zoom = (1.41421 + zoom / 50.0)
                zoom *= zoom
                zoom = 2.0 / zoom

                #camera plane offset in camera viewport
                view_camera_shift_x = context.scene.camera.data.shift_x
                view_camera_shift_y = context.scene.camera.data.shift_y
                dx = 2.0 * (view_camera_shift_x + view_camera_offset[0] * xaspect * 2.0)
                dy = 2.0 * (view_camera_shift_y + view_camera_offset[1] * yaspect * 2.0)

                cam_fov = blcamera.data.angle

                lookat = luxCamera.lookAt(blcamera)
                cam_origin = list(lookat[0:3])
                cam_lookat = list(lookat[3:6])
                cam_up = list(lookat[6:9])

                if luxCamera.use_dof:
                    # Do not world-scale this, it is already in meters!
                    lensradius = (blcamera.data.lens / 1000.0) / (2.0 * luxCamera.fstop)

                ws = get_worldscale(as_scalematrix = False)

                if luxCamera.use_dof:
                    if blcamera.data.dof_object is not None:
                        focaldistance = ws * ((blcamera.location - blcamera.data.dof_object.location).length)
                    elif blcamera.data.dof_distance > 0:
                        focaldistance = ws * blcamera.data.dof_distance

            zoom *= 2.0

            scr_left = -xaspect * zoom
            scr_right = xaspect * zoom
            scr_bottom = -yaspect * zoom
            scr_top = yaspect * zoom

            screenwindow = [scr_left + dx, scr_right + dx, scr_bottom + dy, scr_top + dy]

            self.scnProps.Set(pyluxcore.Property('scene.camera.lookat.target', cam_lookat))
            self.scnProps.Set(pyluxcore.Property('scene.camera.lookat.orig', cam_origin))
            self.scnProps.Set(pyluxcore.Property('scene.camera.up', cam_up))
            self.scnProps.Set(pyluxcore.Property('scene.camera.screenwindow', screenwindow))
            self.scnProps.Set(pyluxcore.Property('scene.camera.fieldofview', math.degrees(cam_fov)))
            self.scnProps.Set(pyluxcore.Property('scene.camera.lensradius', lensradius))
            self.scnProps.Set(pyluxcore.Property('scene.camera.focaldistance', focaldistance))

            # arbitrary clipping plane
            if luxCamera is not None:
                self.convert_clipping_plane(luxCamera)

    def ConvertImagepipelineSettings(self, realtime_preview=False):
        if self.blScene.camera is None:
            return

        imagepipeline_settings = self.blScene.camera.data.luxrender_camera.luxcore_imagepipeline_settings
        index = 0
        prefix = 'film.imagepipeline.'
        
        # Output switcher
        if imagepipeline_settings.output_switcher_pass != 'disabled':
            channel = imagepipeline_settings.output_switcher_pass
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.type', ['OUTPUT_SWITCHER']))
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.channel', [channel]))
            index += 1
        
        # Tonemapper
        tonemapper = imagepipeline_settings.tonemapper_type
        self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.type', [tonemapper]))
        # Note: TONEMAP_AUTOLINEAR has no parameters and is thus not in the if/elif block
        if tonemapper == 'TONEMAP_LINEAR':
            scale = imagepipeline_settings.linear_scale
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.scale', [scale]))
        elif tonemapper == 'TONEMAP_REINHARD02':
            prescale = imagepipeline_settings.reinhard_prescale
            postscale = imagepipeline_settings.reinhard_postscale
            burn = imagepipeline_settings.reinhard_burn
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.prescale', [prescale]))
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.postscale', [postscale]))
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.burn', [burn]))
        elif tonemapper == 'TONEMAP_LUXLINEAR':
            lux_camera = self.blScene.camera.data.luxrender_camera
            sensitivity = lux_camera.sensitivity
            exposure = lux_camera.exposure_time() if not realtime_preview else lux_camera.exposure_time() * 2.25
            fstop = lux_camera.fstop
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.sensitivity', [sensitivity]))
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.exposure', [exposure]))
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.fstop', [fstop]))
        index += 1
        
        # Camera response function
        if imagepipeline_settings.crf_preset != 'None':
            preset = imagepipeline_settings.crf_preset
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.type', ['CAMERA_RESPONSE_FUNC']))
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.name', [preset]))
            index += 1
            
        # Contour lines for IRRADIANCE pass
        if imagepipeline_settings.output_switcher_pass == 'IRRADIANCE':
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.type', ['CONTOUR_LINES']))
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.range', [imagepipeline_settings.contour_range]))
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.scale', [imagepipeline_settings.contour_scale]))
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.steps', [imagepipeline_settings.contour_steps]))
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.zerogridsize', [imagepipeline_settings.contour_zeroGridSize]))
            index += 1
            
        # Gamma correction: Blender expects gamma corrected image in realtime preview, but not in final render
        if realtime_preview:
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.type', ['GAMMA_CORRECTION']))
            self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.value', [2.2]))
            index += 1
        else:
            # prevent crash in 1.4 without gamma correction
            from ..outputs.luxcore_api import LUXCORE_VERSION

            if LUXCORE_VERSION[:3] < '1.5':
                self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.type', ['GAMMA_CORRECTION']))
                self.cfgProps.Set(pyluxcore.Property(prefix + str(index) + '.value', [1.0]))
                index += 1

        # Deprecated but used for backwardscompatibility
        if getattr(self.blScene.camera.data.luxrender_camera.luxrender_film, 'output_alpha'):
            self.cfgProps.Set(pyluxcore.Property('film.alphachannel.enable', ['1']))

    def ConvertSamplerSettings(self):
        engine_settings = self.blScene.luxcore_enginesettings

        self.cfgProps.Set(pyluxcore.Property('sampler.type', [engine_settings.sampler_type]))

        if engine_settings.advanced and engine_settings.sampler_type == 'METROPOLIS':
            self.cfgProps.Set(pyluxcore.Property('sampler.metropolis.largesteprate', [engine_settings.largesteprate]))
            self.cfgProps.Set(
                pyluxcore.Property('sampler.metropolis.maxconsecutivereject', [engine_settings.maxconsecutivereject]))
            self.cfgProps.Set(
                pyluxcore.Property('sampler.metropolis.imagemutationrate', [engine_settings.imagemutationrate]))

    def ConvertFilterSettings(self):
        engine_settings = self.blScene.luxcore_enginesettings

        self.cfgProps.Set(pyluxcore.Property('film.filter.type', [engine_settings.filter_type]))
        self.cfgProps.Set(pyluxcore.Property('film.filter.width', [engine_settings.filter_width]))

    def ConvertEngineSettings(self):
        engine_settings = self.blScene.luxcore_enginesettings
        engine = engine_settings.renderengine_type
        if len(engine) == 0:
            engine = 'PATHCPU'

        if self.blScene.luxcore_translatorsettings.use_filesaver:
            output_path = efutil.filesystem_path(self.blScene.render.filepath)

            self.cfgProps.Set(pyluxcore.Property('renderengine.type', ['FILESAVER']))
            self.cfgProps.Set(pyluxcore.Property('filesaver.directory', [output_path]))
            self.cfgProps.Set(pyluxcore.Property('filesaver.renderengine.type', [engine]))
        else:
            self.cfgProps.Set(pyluxcore.Property('renderengine.type', [engine]))

        if engine in ['BIASPATHCPU', 'BIASPATHOCL']:
            self.cfgProps.Set(pyluxcore.Property('tile.size', [engine_settings.tile_size]))
            self.cfgProps.Set(pyluxcore.Property('tile.multipass.enable',
                                                 [engine_settings.tile_multipass_enable]))
            self.cfgProps.Set(pyluxcore.Property('tile.multipass.convergencetest.threshold',
                                                 [engine_settings.tile_multipass_convergencetest_threshold]))
            self.cfgProps.Set(pyluxcore.Property('tile.multipass.convergencetest.threshold.reduction',
                                                 [engine_settings.tile_multipass_convergencetest_threshold_reduction]))
            self.cfgProps.Set(pyluxcore.Property('biaspath.sampling.aa.size',
                                                 [engine_settings.biaspath_sampling_aa_size]))
            self.cfgProps.Set(pyluxcore.Property('biaspath.sampling.diffuse.size',
                                                 [engine_settings.biaspath_sampling_diffuse_size]))
            self.cfgProps.Set(pyluxcore.Property('biaspath.sampling.glossy.size',
                                                 [engine_settings.biaspath_sampling_glossy_size]))
            self.cfgProps.Set(pyluxcore.Property('biaspath.sampling.specular.size',
                                                 [engine_settings.biaspath_sampling_specular_size]))
            self.cfgProps.Set(pyluxcore.Property('biaspath.pathdepth.total',
                                                 [engine_settings.biaspath_pathdepth_total]))
            self.cfgProps.Set(pyluxcore.Property('biaspath.pathdepth.diffuse',
                                                 [engine_settings.biaspath_pathdepth_diffuse]))
            self.cfgProps.Set(pyluxcore.Property('biaspath.pathdepth.glossy',
                                                 [engine_settings.biaspath_pathdepth_glossy]))
            self.cfgProps.Set(pyluxcore.Property('biaspath.pathdepth.specular',
                                                 [engine_settings.biaspath_pathdepth_specular]))
            self.cfgProps.Set(pyluxcore.Property('biaspath.clamping.radiance.maxvalue',
                                                 [engine_settings.biaspath_clamping_radiance_maxvalue]))
            self.cfgProps.Set(pyluxcore.Property('biaspath.clamping.pdf.value',
                                                 [engine_settings.biaspath_clamping_pdf_value]))
            self.cfgProps.Set(pyluxcore.Property('biaspath.lights.samplingstrategy.type',
                                                 [engine_settings.biaspath_lights_samplingstrategy_type]))
        elif engine in ['PATHCPU', 'PATHOCL']:
            self.cfgProps.Set(pyluxcore.Property('path.maxdepth', [engine_settings.path_maxdepth]))
            self.cfgProps.Set(pyluxcore.Property('path.clamping.radiance.maxvalue',
                                                 [engine_settings.biaspath_clamping_radiance_maxvalue]))
            self.cfgProps.Set(pyluxcore.Property('path.clamping.pdf.value',
                                                 [engine_settings.biaspath_clamping_pdf_value]))
        elif engine in ['BIDIRCPU']:
            self.cfgProps.Set(pyluxcore.Property('path.maxdepth', [engine_settings.bidir_eyedepth]))
            self.cfgProps.Set(pyluxcore.Property('light.maxdepth', [engine_settings.bidir_lightdepth]))
        elif engine in ['BIDIRVMCPU']:
            self.cfgProps.Set(pyluxcore.Property('path.maxdepth', [engine_settings.bidirvm_eyedepth]))
            self.cfgProps.Set(pyluxcore.Property('light.maxdepth', [engine_settings.bidirvm_lightdepth]))
            self.cfgProps.Set(pyluxcore.Property('bidirvm.lightpath.count',
                                                 [engine_settings.bidirvm_lightpath_count]))
            self.cfgProps.Set(pyluxcore.Property('bidirvm.startradius.scale',
                                                 [engine_settings.bidirvm_startradius_scale]))
            self.cfgProps.Set(pyluxcore.Property('bidirvm.alpha', [engine_settings.bidirvm_alpha]))

        # CPU settings
        if engine_settings.native_threads_count > 0:
            self.cfgProps.Set(
                pyluxcore.Property('native.threads.count', [engine_settings.native_threads_count]))

        # OpenCL settings
        if len(engine_settings.luxcore_opencl_devices) > 0:
            dev_string = ''
            for dev_index in range(len(engine_settings.luxcore_opencl_devices)):
                dev = engine_settings.luxcore_opencl_devices[dev_index]
                dev_string += '1' if dev.opencl_device_enabled else '0'

            self.cfgProps.Set(pyluxcore.Property('opencl.devices.select', [dev_string]))

        # Accelerator settings
        self.cfgProps.Set(pyluxcore.Property('accelerator.instances.enable', [engine_settings.instancing]))

    def ConvertRealtimeSettings(self):
        realtime_settings = self.blScene.luxcore_realtimesettings
        engine_settings = self.blScene.luxcore_enginesettings
    
        # Renderengine
        if realtime_settings.device_type == 'CPU':
            engine = realtime_settings.cpu_renderengine_type
        elif realtime_settings.device_type == 'OCL':
            engine = realtime_settings.ocl_renderengine_type
        else:
            engine = 'PATHCPU'

        self.cfgProps.Set(pyluxcore.Property('renderengine.type', [engine]))
        
        # use global clamping settings
        if engine in ['PATHCPU', 'PATHOCL']:
            self.cfgProps.Set(pyluxcore.Property('path.clamping.radiance.maxvalue', [
                                             engine_settings.biaspath_clamping_radiance_maxvalue]))
            self.cfgProps.Set(pyluxcore.Property('path.clamping.pdf.value',
                                             [engine_settings.biaspath_clamping_pdf_value]))

        # OpenCL settings
        if len(self.blScene.luxcore_enginesettings.luxcore_opencl_devices) > 0:
            dev_string = ''
            for dev_index in range(len(self.blScene.luxcore_enginesettings.luxcore_opencl_devices)):
                dev = self.blScene.luxcore_enginesettings.luxcore_opencl_devices[dev_index]
                dev_string += '1' if dev.opencl_device_enabled else '0'

            self.cfgProps.Set(pyluxcore.Property('opencl.devices.select', [dev_string]))

        # Accelerator settings (global)
        self.cfgProps.Set(pyluxcore.Property('accelerator.instances.enable', [engine_settings.instancing]))

        # Sampler settings
        self.cfgProps.Set(pyluxcore.Property('sampler.type', [realtime_settings.sampler_type]))

        # Filter settings
        if realtime_settings.device_type == 'CPU':
            filter_type = realtime_settings.filter_type_cpu
        elif realtime_settings.device_type == 'OCL':
            filter_type = realtime_settings.filter_type_ocl

        self.cfgProps.Set(pyluxcore.Property('film.filter.type', [filter_type]))
        if filter_type != 'NONE':
            self.cfgProps.Set(pyluxcore.Property('film.filter.width', [1.5]))

    def ConvertCustomProps(self):
        engine_settings = self.blScene.luxcore_enginesettings
        # Custom Properties
        if engine_settings.advanced and engine_settings.custom_properties:
            custom_params = engine_settings.custom_properties.replace(' ', '').split('|')
            for prop in custom_params:
                prop = prop.split('=')
                self.cfgProps.Set(pyluxcore.Property(prop[0], prop[1]))

    def ConvertConfig(self, realtime_preview = False):
        realtime_settings = self.blScene.luxcore_realtimesettings

        if realtime_preview and not realtime_settings.use_finalrender_settings:
            self.ConvertRealtimeSettings()
        else:
            # Config for final render
            self.ConvertEngineSettings()
            self.ConvertFilterSettings()
            self.ConvertSamplerSettings()

        self.ConvertCustomProps()
        self.ConvertImagepipelineSettings(realtime_preview)
        self.ConvertChannelSettings(realtime_preview)

        from ..outputs.luxcore_api import LUXCORE_VERSION
        # crashes in 1.4
        if LUXCORE_VERSION[:3] >= '1.5':
            if not realtime_preview:
                self.ConvertLightgroups()

    def ConvertVolumes(self):
        # default volumes
        if self.blScene.camera is not None and self.blScene.camera.data.luxrender_camera.Exterior_volume:
            # Default volume from camera exterior
            volume = BlenderSceneConverter.generate_volume_name(self.blScene.camera.data.luxrender_camera.Exterior_volume)
            self.scnProps.Set(pyluxcore.Property('scene.world.volume.default', [volume]))
        elif self.blScene.luxrender_world.default_exterior_volume:
            # Default volume from world
            volume = BlenderSceneConverter.generate_volume_name(self.blScene.luxrender_world.default_exterior_volume)
            self.scnProps.Set(pyluxcore.Property('scene.world.volume.default', [volume]))

        # convert all volumes
        for volume in self.blScene.luxrender_volumes.volumes:
            self.convert_volume(volume)

    def convert_volume_channel(self, volume, type, variant):
        if getattr(volume, '%s_use%stexture' % (type, variant)):
            is_multiplied = getattr(volume, '%s_multiply%s' % (type, variant))
            tex_name = getattr(volume, '%s_%stexturename' % (type, variant))
            luxcore_tex_name = ToValidLuxCoreName(tex_name)
            # Check if it is an already defined texture, but texture with different multipliers must not stop here
            if luxcore_tex_name in self.texturesCache and not is_multiplied:
                return luxcore_tex_name

            LuxLog('Volume texture: ' + tex_name)

            texture = get_texture_from_scene(self.blScene, tex_name)
            if texture:
                if hasattr(volume, '%s_multiply%s' % (type, variant)) and is_multiplied:
                    tex_name = self.ConvertTexture(texture)
                    scale_value = BlenderSceneConverter.next_scale_value()
                    scale_tex_name = '%s_scaled_%i' % (tex_name, scale_value)

                    self.scnProps.Set(pyluxcore.Property('scene.textures.' + scale_tex_name + '.type', ['scale']))
                    if variant == 'color':
                        self.scnProps.Set(pyluxcore.Property('scene.textures.' + scale_tex_name + '.texture1',
                                                         list(getattr(volume, '%s_%s' % (type, variant)))))
                    else:
                        self.scnProps.Set(pyluxcore.Property('scene.textures.' + scale_tex_name + '.texture1',
                                     str(getattr(volume, '%s_%svalue' % (type, variant)))))
                    self.scnProps.Set(pyluxcore.Property('scene.textures.' + scale_tex_name + '.texture2',
                                                         ['%s' % tex_name]))

                    return scale_tex_name

                else:
                    return self.ConvertTexture(texture)

    def convert_volume(self, volume):
        def absorption_at_depth_scaled(abs_col):
            for i in range(len(abs_col)):
                v = float(abs_col[i])
                depth = volume.depth
                scale = volume.absorption_scale
                abs_col[i] = (-math.log(max([v, 1e-30])) / depth) * scale * (v == 1.0 and -1 or 1)

        name = BlenderSceneConverter.generate_volume_name(volume.name)
        prefix = 'scene.volumes.' + name

        # add to cache
        BlenderSceneConverter.volumes_cache[volume.name] = name

        # IOR Fresnel
        if volume.fresnel_usefresneltexture:
            ior_val = self.convert_volume_channel(volume, 'fresnel', 'fresnel')
        else:
            ior_val = volume.fresnel_fresnelvalue

        # Absorption
        if volume.absorption_usecolortexture:
            abs_col = self.convert_volume_channel(volume, 'absorption', 'color')
        elif volume.sigma_a_usecolortexture:
            abs_col = self.convert_volume_channel(volume, 'sigma_a', 'color')
        else:
            abs_col = [volume.sigma_a_color.r, volume.sigma_a_color.g, volume.sigma_a_color.b]
            absorption_at_depth_scaled(abs_col)

        self.scnProps.Set(pyluxcore.Property(prefix + '.absorption', abs_col))
        self.scnProps.Set(pyluxcore.Property(prefix + '.type', [volume.type]))
        self.scnProps.Set(pyluxcore.Property(prefix + '.ior', ior_val))
        self.scnProps.Set(pyluxcore.Property(prefix + '.priority', volume.priority))

        if volume.type in ['homogeneous', 'heterogeneous']:

            # Scattering color
            if volume.sigma_s_usecolortexture:
                s_source = self.convert_volume_channel(volume, 'sigma_s', 'color')
                if volume.scattering_scale != 1.0:
                    s_source = self.convert_volume_channel(volume, 'sigma_s', 'color')
                    self.scnProps.Set(pyluxcore.Property('scene.textures.' + name + '_scatterscaling.type', ['scale']))
                    self.scnProps.Set(pyluxcore.Property('scene.textures.' + name + '_scatterscaling.texture1', volume.scattering_scale))
                    self.scnProps.Set(pyluxcore.Property('scene.textures.' + name + '_scatterscaling.texture2', s_source))
                    s_col = name + '_scatterscaling'
                else:
                    s_col = s_source

            else:
                s_col = [volume.sigma_s_color.r * volume.scattering_scale,
                         volume.sigma_s_color.g * volume.scattering_scale,
                         volume.sigma_s_color.b * volume.scattering_scale]

            self.scnProps.Set(pyluxcore.Property(prefix + '.scattering', s_col))
            self.scnProps.Set(pyluxcore.Property(prefix + '.asymmetry', list(volume.g)))
            self.scnProps.Set(pyluxcore.Property(prefix + '.multiscattering', [volume.multiscattering]))

        if volume.type == 'heterogenous':
            self.scnProps.Set(pyluxcore.Property(prefix + '.steps.size', volume.stepsize))

    def ConvertChannelSettings(self, realtime_preview=False):
        if self.blScene.camera is None:
            return

        luxrender_camera = self.blScene.camera.data.luxrender_camera
        output_switcher_channel = luxrender_camera.luxcore_imagepipeline_settings.output_switcher_pass
        channels = self.blScene.luxrender_channels

        if (channels.enable_aovs and not realtime_preview) or output_switcher_channel != 'disabled':
            if channels.RGB:
                self.createChannelOutputString('RGB')
            if channels.RGBA:
                self.createChannelOutputString('RGBA')
            if channels.RGB_TONEMAPPED:
                self.createChannelOutputString('RGB_TONEMAPPED')
            if channels.RGBA_TONEMAPPED:
                self.createChannelOutputString('RGBA_TONEMAPPED')
            if channels.ALPHA or output_switcher_channel == 'ALPHA':
                self.createChannelOutputString('ALPHA')
            if channels.DEPTH or output_switcher_channel == 'DEPTH':
                self.createChannelOutputString('DEPTH')
            if channels.POSITION or output_switcher_channel == 'POSITION':
                self.createChannelOutputString('POSITION')
            if channels.GEOMETRY_NORMAL or output_switcher_channel == 'GEOMETRY_NORMAL':
                self.createChannelOutputString('GEOMETRY_NORMAL')
            if channels.SHADING_NORMAL or output_switcher_channel == 'SHADING_NORMAL':
                self.createChannelOutputString('SHADING_NORMAL')
            if channels.MATERIAL_ID or output_switcher_channel == 'MATERIAL_ID':
                self.createChannelOutputString('MATERIAL_ID')
            if channels.DIRECT_DIFFUSE or output_switcher_channel == 'DIRECT_DIFFUSE':
                self.createChannelOutputString('DIRECT_DIFFUSE')
            if channels.DIRECT_GLOSSY or output_switcher_channel == 'DIRECT_GLOSSY':
                self.createChannelOutputString('DIRECT_GLOSSY')
            if channels.EMISSION or output_switcher_channel == 'EMISSION':
                self.createChannelOutputString('EMISSION')
            if channels.INDIRECT_DIFFUSE or output_switcher_channel == 'INDIRECT_DIFFUSE':
                self.createChannelOutputString('INDIRECT_DIFFUSE')
            if channels.INDIRECT_GLOSSY or output_switcher_channel == 'INDIRECT_GLOSSY':
                self.createChannelOutputString('INDIRECT_GLOSSY')
            if channels.INDIRECT_SPECULAR or output_switcher_channel == 'INDIRECT_SPECULAR':
                self.createChannelOutputString('INDIRECT_SPECULAR')
            if channels.DIRECT_SHADOW_MASK or output_switcher_channel == 'DIRECT_SHADOW_MASK':
                self.createChannelOutputString('DIRECT_SHADOW_MASK')
            if channels.INDIRECT_SHADOW_MASK or output_switcher_channel == 'INDIRECT_SHADOW_MASK':
                self.createChannelOutputString('INDIRECT_SHADOW_MASK')
            if channels.UV or output_switcher_channel == 'UV':
                self.createChannelOutputString('UV')
            if channels.RAYCOUNT or output_switcher_channel == 'RAYCOUNT':
                self.createChannelOutputString('RAYCOUNT')
            if channels.IRRADIANCE or output_switcher_channel == 'IRRADIANCE':
                self.createChannelOutputString('IRRADIANCE')

    def ConvertLightgroups(self):
        if not self.blScene.luxrender_lightgroups.ignore:
            for i in range(len(self.lightgroups_cache)):
                self.createChannelOutputString('RADIANCE_GROUP', i)

    def Convert(self, imageWidth = None, imageHeight = None, realtime_preview = False, context = None):
        export_start = time.time()

        if self.renderengine is not None:
            self.renderengine.update_stats('Exporting...', '')

        # clear cache
        BlenderSceneConverter.clear_export_cache()

        # #######################################################################
        # Convert camera definition
        ########################################################################
        if realtime_preview:
            self.ConvertViewportCamera(context)
        else:
            self.ConvertCamera()

        ########################################################################
        # Add dummy materials
        ########################################################################
        self.scnProps.Set(pyluxcore.Property('scene.materials.LUXBLEND_LUXCORE_CLAY_MATERIAL.type', ['matte']))
        self.scnProps.Set(pyluxcore.Property('scene.materials.LUXBLEND_LUXCORE_CLAY_MATERIAL.kd', '0.7 0.7 0.7'))

        self.scnProps.Set(pyluxcore.Property('scene.materials.LUXBLEND_LUXCORE_NULL_MATERIAL.type', ['null']))

        ########################################################################
        # Convert all volumes
        ########################################################################
        self.ConvertVolumes()

        ########################################################################
        # Convert all objects (and materials and textures)
        ########################################################################
        objects_amount = len(self.blScene.objects)
        objects_counter = 0

        LuxLog('Converting objects:')

        for obj in self.blScene.objects:
            # cancel export when user hits 'Esc'
            if self.renderengine is not None and self.renderengine.test_break():
                break

            # display progress messages in log and UI
            objects_counter += 1
            message = 'Object: %s (%d of %d)' % (obj.name, objects_counter, objects_amount)
            progress = float(objects_counter) / float(objects_amount)
            print('[%d%%] %s' % ((progress * 100), message))

            if self.renderengine is not None:
                self.renderengine.update_stats('Exporting...', message)
                self.renderengine.update_progress(progress)

            # convert object
            self.ConvertObject(obj)
        
        # Debug information
        if self.blScene.luxcore_translatorsettings.print_config:
            LuxLog('Scene Properties:')
            print(str(self.scnProps))

        self.lcScene.Parse(self.scnProps)

        ########################################################################
        # Create the configuration
        ########################################################################
        if self.renderengine is not None:
            self.renderengine.update_stats('Exporting...', 'Setting up renderengine configuration')
        self.ConvertConfig(realtime_preview)

        # Film
        if imageWidth is not None and imageHeight is not None:
            filmWidth = imageWidth
            filmHeight = imageHeight
        else:
            filmWidth, filmHeight = self.blScene.camera.data.luxrender_camera.luxrender_film.resolution(self.blScene)

        self.cfgProps.Set(pyluxcore.Property('film.width', [filmWidth]))
        self.cfgProps.Set(pyluxcore.Property('film.height', [filmHeight]))

        # Debug information
        if self.blScene.luxcore_translatorsettings.print_config:
            LuxLog('RenderConfig Properties:')
            print(str(self.cfgProps))

        # Create config
        self.lcConfig = pyluxcore.RenderConfig(self.cfgProps, self.lcScene)

        BlenderSceneConverter.clear()  # reset scalers_count etc.

        # Show messages about export
        export_time = time.time() - export_start
        print('Export took %.1f seconds' % export_time)
        if self.renderengine is not None:
            engine = self.blScene.luxcore_enginesettings.renderengine_type
            message = 'Compiling OpenCL Kernels...' if 'OCL' in engine else 'Starting LuxRender...'
            self.renderengine.update_stats('Export Finished (%.1fs)' % export_time, message)

        return self.lcConfig
