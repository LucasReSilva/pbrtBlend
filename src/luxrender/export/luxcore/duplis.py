# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# David Bucciarelli, Jens Verwiebe, Tom Bech, Doug Hammond, Daniel Genrich, Michael Klemm, Simon Wendsche
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

import math, mathutils, time
from ...outputs.luxcore_api import pyluxcore
from ...outputs.luxcore_api import ToValidLuxCoreName
from ...export import matrix_to_list, is_obj_visible

from .objects import ObjectExporter


class DupliExporter(object):
    def __init__(self, luxcore_exporter, blender_scene, duplicator, is_viewport_render=False):
        self.luxcore_exporter = luxcore_exporter
        self.blender_scene = blender_scene
        self.is_viewport_render = is_viewport_render
        self.duplicator = duplicator

        self.properties = pyluxcore.Properties()
        self.dupli_number = 0
        self.dupli_amount = 1


    def convert(self, luxcore_scene):
        self.properties = pyluxcore.Properties()
        export_settings = self.blender_scene.luxcore_translatorsettings

        try:
            if len(self.duplicator.particle_systems) > 0:
                for particle_system in self.duplicator.particle_systems:
                    if particle_system.settings.render_type in ['OBJECT', 'GROUP'] and export_settings.export_particles:
                        self.__convert_particles2(luxcore_scene)
                    elif particle_system.settings.render_type == 'PATH' and export_settings.export_hair:
                        self.__convert_hair(luxcore_scene, particle_system)
            else:
                self.__convert_duplis(luxcore_scene)
        except Exception:
            print('Could not convert particle systems of object %s' % self.duplicator.name)
            self.luxcore_exporter.errors = True
            import traceback
            traceback.print_exc()
        finally:
            return self.properties


    def __report_progress(self, particle_system=None):
        """
        Show information about the export progress in the UI
        """
        if particle_system is not None:
            name = 'Hair' if particle_system.settings.type == 'HAIR' else 'Particle'
            particle_system_string = ' | %s System: %s' % (name, particle_system.name)
        else:
            particle_system_string = ''

        percentage = (self.dupli_number / self.dupli_amount) * 100
        progress_string = ' (%d%%)' % percentage

        message = 'Object: %s%s%s' % (self.duplicator.name, particle_system_string, progress_string)
        self.luxcore_exporter.renderengine.update_stats('Exporting...', message)


    def __convert_duplis(self, luxcore_scene):
        """
        Converts duplis and OBJECT and GROUP particle systems
        """
        print('[%s] Exporting duplis' % self.duplicator.name)
        time_start = time.time()

        mode = 'VIEWPORT' if self.is_viewport_render else 'RENDER'
        self.duplicator.dupli_list_create(self.blender_scene, settings=mode)
        self.dupli_amount = len(self.duplicator.dupli_list)

        for dupli_ob in self.duplicator.dupli_list:
            # Make it possible to interrupt the export process
            if self.luxcore_exporter.renderengine.test_break():
                return

            self.__report_progress()

            dupli_object = dupli_ob.object

            # Check for group layer visibility, if the object is in a group
            group_visible = len(dupli_object.users_group) == 0

            for group in dupli_object.users_group:
                group_visible |= True in [a & b for a, b in zip(dupli_object.layers, group.layers)]

            if not group_visible:
                continue

            # Convert dupli object
            dupli_name_suffix = '_%s_%d' % (self.duplicator.name, self.dupli_number)
            self.dupli_number += 1

            object_exporter = ObjectExporter(self.luxcore_exporter, self.blender_scene, self.is_viewport_render,
                                             dupli_object, dupli_name_suffix)
            properties = object_exporter.convert(update_mesh=True, update_material=True, luxcore_scene=luxcore_scene,
                                                 matrix=dupli_ob.matrix.copy(), is_dupli=True)
            self.properties.Set(properties)

        self.duplicator.dupli_list_clear()

        time_elapsed = time.time() - time_start
        print('[%s] Dupli export finished (%.3fs)' % (self.duplicator.name, time_elapsed))


    def __convert_particles2(self, luxcore_scene):
        """
        Ported from export/geometry.py (classic export)
        This function always exports with correct rotation, but does not support particle motion blur
        """

        obj = self.duplicator

        print('[%s:] Exporting particle systems' % (obj.name))
        time_start = time.time()

        mode = 'VIEWPORT' if self.is_viewport_render else 'RENDER'
        obj.dupli_list_create(self.blender_scene, settings=mode)
        if not obj.dupli_list:
            raise Exception('cannot create dupli list for object %s' % obj.name)

        self.dupli_amount = len(self.duplicator.dupli_list)

        # Create our own DupliOb list to work around incorrect layers
        # attribute when inside create_dupli_list()..free_dupli_list()
        duplis = []
        for dupli_ob in obj.dupli_list:
            if not is_obj_visible(self.blender_scene, dupli_ob.object, is_dupli=True):
                continue

            # Make it possible to interrupt the export process
            if self.luxcore_exporter.renderengine.test_break():
                return

            # metaballs are omitted from this function intentionally.
            if dupli_ob.object.type not in ['MESH', 'SURFACE', 'FONT', 'CURVE']:
                continue

            duplis.append(
                (
                    dupli_ob.object,
                    dupli_ob.matrix.copy(),
                    dupli_ob.particle_system.name,
                    dupli_ob.persistent_id[:]
                )
            )

        obj.dupli_list_clear()

        # dupli object, dupli matrix
        for do, dm, psys_name, persistent_id in duplis:
            # Check for group layer visibility, if the object is in a group
            gviz = len(do.users_group) == 0

            for grp in do.users_group:
                gviz |= True in [a & b for a, b in zip(do.layers, grp.layers)]

            if not gviz:
                continue

            # Make it possible to interrupt the export process
            if self.luxcore_exporter.renderengine.test_break():
                return

            self.__report_progress()

            persistent_id_str = '_'.join([str(elem) for elem in persistent_id])
            dupli_name_suffix = '%s_%s_%s' % (self.duplicator.name, psys_name, persistent_id_str)
            object_exporter = ObjectExporter(self.luxcore_exporter, self.blender_scene, self.is_viewport_render,
                                             do, dupli_name_suffix)
            properties = object_exporter.convert(update_mesh=True, update_material=True, luxcore_scene=luxcore_scene,
                                                 matrix=dm, is_dupli=True, anim_matrices=None)
            self.properties.Set(properties)

        del duplis

        time_elapsed = time.time() - time_start
        print('[%s:] Particle export finished (%.3fs)' % (obj.name, time_elapsed))


    def __convert_particles(self, luxcore_scene):
        """
        This function supports particle motion blur, but exports particles with wrong rotations in some cases

        (deprecated)
        """

        obj = self.duplicator
        particle_system = self.dupli_system

        print('[%s: %s] Exporting particle system' % (self.duplicator.name, particle_system.name))
        time_start = time.time()

        if (self.blender_scene.camera is not None and self.blender_scene.camera.data.luxrender_camera.usemblur
            and self.blender_scene.camera.data.luxrender_camera.objectmblur):
            steps = self.blender_scene.camera.data.luxrender_camera.motion_blur_samples + 1
        else:
            steps = 1

        old_subframe = self.blender_scene.frame_subframe
        current_frame = self.blender_scene.frame_current

        # Collect particles that should be visible
        particles = [p for p in particle_system.particles if p.alive_state == 'ALIVE' or (
            p.alive_state == 'UNBORN' and particle_system.settings.show_unborn) or (
                         p.alive_state in ['DEAD', 'DYING'] and particle_system.settings.use_dead)]

        mode = 'VIEWPORT' if self.is_viewport_render else 'RENDER'
        obj.dupli_list_create(self.blender_scene, settings=mode)
        self.dupli_amount = len(obj.dupli_list)

        dupli_objects = [dupli.object for dupli in obj.dupli_list]
        particle_dupliobj_pairs = list(zip(particles, dupli_objects))

        # dict of the form {particle: [dupli_object, []]} (the empty list will contain the matrices)
        particle_dupliobj_dict = {pair[0]: [pair[1], []] for pair in particle_dupliobj_pairs}

        for i in range(steps):
            self.blender_scene.frame_set(current_frame, subframe=i / steps)

            # Calculate matrix for each particle
            # I'm not using obj.dupli_list[i].matrix because it contains wrong positions
            for particle in particle_dupliobj_dict:
                # Make it possible to interrupt the export process
                if self.luxcore_exporter.renderengine.test_break():
                    return

                dupli_object = particle_dupliobj_dict[particle][0]

                scale = dupli_object.scale * particle.size
                scale_matrix = mathutils.Matrix()
                scale_matrix[0][0] = scale.x
                scale_matrix[1][1] = scale.y
                scale_matrix[2][2] = scale.z

                rotation_matrix = particle.rotation.to_matrix()
                rotation_matrix.resize_4x4()

                transform_matrix = mathutils.Matrix()
                transform_matrix[0][3] = particle.location.x
                transform_matrix[1][3] = particle.location.y
                transform_matrix[2][3] = particle.location.z

                transform = transform_matrix * rotation_matrix * scale_matrix

                # Only use motion blur for living particles
                if particle.alive_state == 'ALIVE':
                    # Don't append matrix if it is identical to the previous one
                    if particle_dupliobj_dict[particle][1][-1:] != transform:
                        particle_dupliobj_dict[particle][1].append(transform)
                else:
                    # Overwrite old matrix
                    particle_dupliobj_dict[particle][1] = [transform]

        obj.dupli_list_clear()
        self.blender_scene.frame_set(current_frame, subframe=old_subframe)

        # Export particles
        for particle in particle_dupliobj_dict:
            # Make it possible to interrupt the export process
            if self.luxcore_exporter.renderengine.test_break():
                return

            self.__report_progress()

            dupli_object = particle_dupliobj_dict[particle][0]
            anim_matrices = particle_dupliobj_dict[particle][1]

            dupli_name_suffix = '%s_%s_%d' % (self.duplicator.name, self.dupli_system.name, self.dupli_number)
            self.dupli_number += 1
            object_exporter = ObjectExporter(self.luxcore_exporter, self.blender_scene, self.is_viewport_render,
                                             dupli_object, dupli_name_suffix)
            properties = object_exporter.convert(update_mesh=True, update_material=True, luxcore_scene=luxcore_scene,
                                                 matrix=anim_matrices[0], is_dupli=True, anim_matrices=anim_matrices)
            self.properties.Set(properties)

        time_elapsed = time.time() - time_start
        print('[%s: %s] Particle export finished (%.3fs)' % (self.duplicator.name, particle_system.name, time_elapsed))


    def __convert_hair(self, luxcore_scene, particle_system):
        """
        Converts PATH type particle systems (hair systems)
        """
        obj = self.duplicator
        psys = particle_system

        for mod in obj.modifiers:
            if mod.type == 'PARTICLE_SYSTEM':
                if mod.particle_system.name == psys.name:
                    break

        if not mod.type == 'PARTICLE_SYSTEM':
            return
        elif not mod.particle_system.name == psys.name or not mod.show_render:
            return

        print('[%s: %s] Exporting hair' % (self.duplicator.name, psys.name))
        time_start = time.time()

        # Export code copied from export/geometry (line 947)

        settings = psys.settings.luxrender_hair

        hair_size = settings.hair_size
        root_width = settings.root_width
        tip_width = settings.tip_width
        width_offset = settings.width_offset

        if not self.is_viewport_render:
            psys.set_resolution(self.blender_scene, obj, 'RENDER')
        steps = 2 ** psys.settings.render_step
        num_parents = len(psys.particles)
        num_children = len(psys.child_particles)

        if num_children == 0:
            start = 0
        else:
            # Number of virtual parents reduces the number of exported children
            num_virtual_parents = math.trunc(
                0.3 * psys.settings.virtual_parents * psys.settings.child_nbr * num_parents)
            start = num_parents + num_virtual_parents

        segments = []
        points = []
        thickness = []
        colors = []
        uv_coords = []
        total_segments_count = 0
        vertex_color_layer = None
        uv_tex = None
        colorflag = 0
        uvflag = 0
        thicknessflag = 0
        image_width = 0
        image_height = 0
        image_pixels = []

        modifier_mode = 'PREVIEW' if self.is_viewport_render else 'RENDER'
        mesh = obj.to_mesh(self.blender_scene, True, modifier_mode)
        uv_textures = mesh.tessface_uv_textures
        vertex_color = mesh.tessface_vertex_colors

        has_vertex_colors = vertex_color.active and vertex_color.active.data

        if settings.export_color == 'vertex_color':
            if has_vertex_colors:
                vertex_color_layer = vertex_color.active.data
                colorflag = 1

        if uv_textures.active and uv_textures.active.data:
            uv_tex = uv_textures.active.data
            if settings.export_color == 'uv_texture_map':
                if uv_tex[0].image:
                    image_width = uv_tex[0].image.size[0]
                    image_height = uv_tex[0].image.size[1]
                    image_pixels = uv_tex[0].image.pixels[:]
                    colorflag = 1
            uvflag = 1

        transform = obj.matrix_world.inverted()
        total_strand_count = 0

        if root_width == tip_width:
            thicknessflag = 0
            hair_size *= root_width
        else:
            thicknessflag = 1

        self.dupli_amount = num_parents + num_children

        for pindex in range(start, num_parents + num_children):
            # Make it possible to interrupt the export process
            if self.luxcore_exporter.renderengine.test_break():
                return

            self.dupli_number += 1
            self.__report_progress(psys)

            point_count = 0
            i = 0

            if num_children == 0:
                i = pindex

            # A small optimization in order to speedup the export
            # process: cache the uv_co and color value
            uv_co = None
            col = None
            seg_length = 1.0

            for step in range(0, steps):
                co = psys.co_hair(obj, pindex, step)
                if step > 0:
                    seg_length = (co - obj.matrix_world * points[len(points) - 1]).length_squared

                if not (co.length_squared == 0 or seg_length == 0):
                    points.append(transform * co)

                    if thicknessflag:
                        if step > steps * width_offset:
                            thick = (root_width * (steps - step - 1) + tip_width * (
                                        step - steps * width_offset)) / (
                                        steps * (1 - width_offset) - 1)
                        else:
                            thick = root_width

                        thickness.append(thick * hair_size)

                    point_count += + 1

                    if uvflag:
                        if not uv_co:
                            uv_co = psys.uv_on_emitter(mod, psys.particles[i], pindex, uv_textures.active_index)

                        uv_coords.append(uv_co)

                    if settings.export_color == 'uv_texture_map' and not len(image_pixels) == 0:
                        if not col:
                            x_co = round(uv_co[0] * (image_width - 1))
                            y_co = round(uv_co[1] * (image_height - 1))

                            pixelnumber = (image_width * y_co) + x_co

                            r = image_pixels[pixelnumber * 4]
                            g = image_pixels[pixelnumber * 4 + 1]
                            b = image_pixels[pixelnumber * 4 + 2]
                            col = (r, g, b)

                        colors.append(col)
                    elif settings.export_color == 'vertex_color' and has_vertex_colors:
                        if not col:
                            col = psys.mcol_on_emitter(mod, psys.particles[i], pindex, vertex_color.active_index)

                        colors.append(col)

            if point_count == 1:
                points.pop()

                if thicknessflag:
                    thickness.pop()
                point_count -= 1
            elif point_count > 1:
                segments.append(point_count - 1)
                total_strand_count += 1
                total_segments_count = total_segments_count + point_count - 1

        # LuxCore needs tuples, not vectors
        points_as_tuples = [tuple(point) for point in points]

        if not thicknessflag:
            thickness = hair_size

        if not colorflag:
            colors = (1.0, 1.0, 1.0)

        if not uvflag:
            uvs_as_tuples = None
        else:
            # LuxCore needs tuples, not vectors
            uvs_as_tuples = [tuple(uv) for uv in uv_coords]

        luxcore_shape_name = ToValidLuxCoreName(obj.name + '_' + psys.name)

        self.luxcore_exporter.renderengine.update_stats('Exporting...', 'Refining Hair System %s' % psys.name)
        # Documentation: http://www.luxrender.net/forum/viewtopic.php?f=8&t=12116&sid=03a16c5c345db3ee0f8126f28f1063c8#p112819
        luxcore_scene.DefineStrands(luxcore_shape_name, total_strand_count, len(points), points_as_tuples, segments,
                                    thickness, 0.0, colors, uvs_as_tuples,
                                    settings.tesseltype, settings.adaptive_maxdepth, settings.adaptive_error,
                                    settings.solid_sidecount, settings.solid_capbottom, settings.solid_captop,
                                    True)

        # For some reason this index is not starting at 0 but at 1 (Blender is strange)
        material_index = psys.settings.material - 1

        try:
            material = obj.material_slots[material_index].material
        except IndexError:
            material = None
            print('WARNING: material slot %d on object "%s" is unassigned!' % (material_index + 1, obj.name))

        # Convert material
        self.luxcore_exporter.convert_material(material)
        material_exporter = self.luxcore_exporter.material_cache[material]
        luxcore_material_name = material_exporter.luxcore_name

        transform = matrix_to_list(obj.matrix_world, apply_worldscale=True)

        prefix = 'scene.objects.' + luxcore_shape_name
        self.properties.Set(pyluxcore.Property(prefix + '.material', luxcore_material_name))
        self.properties.Set(pyluxcore.Property(prefix + '.shape', luxcore_shape_name))
        self.properties.Set(pyluxcore.Property(prefix + '.transformation', transform))

        if not self.is_viewport_render:
            # Resolution was changed to 'RENDER' for final renders, change it back
            psys.set_resolution(self.blender_scene, obj, 'PREVIEW')

        time_elapsed = time.time() - time_start
        print('[%s: %s] Hair export finished (%.3fs)' % (obj.name, psys.name, time_elapsed))
