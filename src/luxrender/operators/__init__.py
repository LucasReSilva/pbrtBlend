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
import os,  mathutils, tempfile, shutil, urllib.request, urllib.error, zipfile

# LuxRender Libs
from .. import LuxRenderAddon

# Per-IDPropertyGroup preset handling

class LUXRENDER_MT_base(bpy.types.Menu):
    preset_operator = "script.execute_preset"

    def draw(self, context):
        return bpy.types.Menu.draw_preset(self, context)


@LuxRenderAddon.addon_register_class
class LUXRENDER_MT_presets_engine(LUXRENDER_MT_base):
    bl_label = "LuxRender Engine Presets"
    preset_subdir = "luxrender/engine"


@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_preset_engine_add(bl_operators.presets.AddPresetBase, bpy.types.Operator):
    """Save the current settings as a preset"""
    bl_idname = 'luxrender.preset_engine_add'
    bl_label = 'Add LuxRender Engine settings preset'
    preset_menu = 'LUXRENDER_MT_presets_engine'
    preset_values = []
    preset_subdir = 'luxrender/engine'

    def execute(self, context):
        self.preset_values = [
                                 'bpy.context.scene.luxrender_engine.%s' % v['attr'] for v in
                                 bpy.types.luxrender_engine.get_exportable_properties()
                             ] + [
                                 'bpy.context.scene.luxrender_sampler.%s' % v['attr'] for v in
                                 bpy.types.luxrender_sampler.get_exportable_properties()
                             ] + [
                                 'bpy.context.scene.luxrender_integrator.%s' % v['attr'] for v in
                                 bpy.types.luxrender_integrator.get_exportable_properties()
                             ] + [
                                 'bpy.context.scene.luxrender_volumeintegrator.%s' % v['attr'] for v in
                                 bpy.types.luxrender_volumeintegrator.get_exportable_properties()
                             ] + [
                                 'bpy.context.scene.luxrender_filter.%s' % v['attr'] for v in
                                 bpy.types.luxrender_filter.get_exportable_properties()
                             ] + [
                                 'bpy.context.scene.luxrender_accelerator.%s' % v['attr'] for v in
                                 bpy.types.luxrender_accelerator.get_exportable_properties()
                             ]
        return super().execute(context)


@LuxRenderAddon.addon_register_class
class LUXRENDER_MT_presets_networking(LUXRENDER_MT_base):
    bl_label = "LuxRender Networking Presets"
    preset_subdir = "luxrender/networking"


@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_preset_networking_add(bl_operators.presets.AddPresetBase, bpy.types.Operator):
    '''Save the current settings as a preset'''
    bl_idname = 'luxrender.preset_networking_add'
    bl_label = 'Add LuxRender Networking settings preset'
    preset_menu = 'LUXRENDER_MT_presets_networking'
    preset_values = []
    preset_subdir = 'luxrender/networking'

    def execute(self, context):
        self.preset_values = [
            'bpy.context.scene.luxrender_networking.%s' % v['attr'] for v in
            bpy.types.luxrender_networking.get_exportable_properties()
        ]
        return super().execute(context)


# Volume data handling

@LuxRenderAddon.addon_register_class
class LUXRENDER_MT_presets_volume(LUXRENDER_MT_base):
    bl_label = "LuxRender Volume Presets"
    preset_subdir = "luxrender/volume"


@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_preset_volume_add(bl_operators.presets.AddPresetBase, bpy.types.Operator):
    """Save the current settings as a preset"""
    bl_idname = 'luxrender.preset_volume_add'
    bl_label = 'Add LuxRender Volume settings preset'
    preset_menu = 'LUXRENDER_MT_presets_volume'
    preset_values = []
    preset_subdir = 'luxrender/volume'

    def execute(self, context):
        ks = 'bpy.context.scene.luxrender_volumes.volumes[bpy.context.scene.luxrender_volumes.volumes_index].%s'
        pv = [
            ks % v['attr'] for v in bpy.types.luxrender_volume_data.get_exportable_properties()
        ]

        self.preset_values = pv
        return super().execute(context)


@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_volume_add(bpy.types.Operator):
    """Add a new material volume definition to the scene"""

    bl_idname = "luxrender.volume_add"
    bl_label = "Add LuxRender Volume"

    new_volume_name = bpy.props.StringProperty(default='New Volume')

    def invoke(self, context, event):
        v = context.scene.luxrender_volumes.volumes
        v.add()
        new_vol = v[len(v) - 1]
        new_vol.name = self.properties.new_volume_name
        return {'FINISHED'}


@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_volume_remove(bpy.types.Operator):
    """Remove the selected material volume definition"""

    bl_idname = "luxrender.volume_remove"
    bl_label = "Remove LuxRender Volume"

    def invoke(self, context, event):
        w = context.scene.luxrender_volumes
        w.volumes.remove(w.volumes_index)
        w.volumes_index = len(w.volumes) - 1
        return {'FINISHED'}


@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_lightgroup_add(bpy.types.Operator):
    """Add a new light group definition to the scene"""

    bl_idname = "luxrender.lightgroup_add"
    bl_label = "Add LuxRender Light Group"

    lg_count = 0
    new_lightgroup_name = bpy.props.StringProperty(default='New Light Group ')

    def invoke(self, context, event):
        lg = context.scene.luxrender_lightgroups.lightgroups
        lg.add()
        new_lg = lg[len(lg) - 1]
        new_lg.name = self.properties.new_lightgroup_name + str(LUXRENDER_OT_lightgroup_add.lg_count)
        LUXRENDER_OT_lightgroup_add.lg_count += 1
        return {'FINISHED'}


@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_lightgroup_remove(bpy.types.Operator):
    """Remove the selected lightgroup definition"""

    bl_idname = "luxrender.lightgroup_remove"
    bl_label = "Remove LuxRender Light Group"

    lg_index = bpy.props.IntProperty(default=-1)

    def invoke(self, context, event):
        w = context.scene.luxrender_lightgroups
        if self.properties.lg_index == -1:
            w.lightgroups.remove(w.lightgroups_index)
        else:
            w.lightgroups.remove(self.properties.lg_index)
        w.lightgroups_index = len(w.lightgroups) - 1
        return {'FINISHED'}


@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_opencl_device_list_update(bpy.types.Operator):
    """Update the OpenCL device list"""

    bl_idname = "luxrender.opencl_device_list_update"
    bl_label = "Update the OpenCL device list"

    def invoke(self, context, event):
        devs = context.scene.luxcore_enginesettings.luxcore_opencl_devices
        # Clear the list
        for i in range(len(devs)):
            devs.remove(0)

        # Create the new list
        from ..outputs.luxcore_api import pyluxcore

        deviceList = pyluxcore.GetOpenCLDeviceList()
        for dev in deviceList:
            devs.add()
            index = len(devs) - 1
            new_dev = devs[index]
            new_dev.name = 'Device ' + str(index) + ': ' + dev[0] + ' (' + dev[1] + ')'

        return {'FINISHED'}


@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_update_luxblend(bpy.types.Operator):
    """Update LuxBlend to the latest version"""
    bl_idname = "luxrender.update_luxblend"
    bl_label = "Update LuxBlend"

    def execute(self, context):
        def recursive_overwrite(src, dest, ignore=None):
            if os.path.isdir(src):
                if not os.path.isdir(dest):
                    os.makedirs(dest)
                files = os.listdir(src)
                if ignore is not None:
                    ignored = ignore(src, files)
                else:
                    ignored = set()
                for f in files:
                    if f not in ignored:
                        recursive_overwrite(os.path.join(src, f),
                                            os.path.join(dest, f),
                                            ignore)
            else:
                shutil.copyfile(src, dest)

        print('-' * 20)
        print('Updating LuxBlend...')

        with tempfile.TemporaryDirectory() as temp_dir_path:
            temp_zip_path = os.path.join(temp_dir_path, 'default.zip')

            # Download LuxBlend zip archive of latest default branch commit
            url = 'https://bitbucket.org/luxrender/luxblend25/get/default.zip'
            try:
                print('Downloading', url)

                with urllib.request.urlopen(url, timeout=60) as url_handle, \
                                   open(temp_zip_path, 'wb') as file_handle:
                    file_handle.write(url_handle.read())
            except urllib.error.URLError as err:
                self.report({'ERROR'}, 'Could not download: %s' % err)

            # Extract the zip
            print('Extracting ZIP archive')
            with zipfile.ZipFile(temp_zip_path) as zip:
                for member in zip.namelist():
                    if 'src/luxrender' in member:
                        # Remove the first two directories and the filename
                        # e.g. luxrender-luxblend25-bfb488c84111/src/luxrender/ui/textures/wrinkled.py
                        # becomes luxrender/ui/textures/
                        target_path = os.path.join(temp_dir_path,
                                        os.path.join(*member.split('/')[2:-1]))

                        filename = os.path.basename(member)
                        # Skip directories
                        if len(filename) == 0:
                            continue

                        # Create the target directory if necessary
                        if not os.path.exists(target_path):
                            os.makedirs(target_path)

                        source = zip.open(member)
                        target = open(os.path.join(target_path, filename), "wb")

                        with source, target:
                            shutil.copyfileobj(source, target)
                            print('copying', source, 'to', target)

            extracted_luxblend_path = os.path.join(temp_dir_path, 'luxrender')

            if not os.path.exists(extracted_luxblend_path):
                self.report({'ERROR'}, 'Could not extract ZIP archive! Aborting.')
                return {'FINISHED'}

            # Find the old LuxBlend files
            luxblend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            print('LuxBlend addon folder:', luxblend_dir)

            # TODO: Create backup


            # Delete old LuxBlend files (only directories and *.py files, the user might have other stuff in there!)
            print('Deleting old LuxBlend files')
            # remove __init__.py
            os.remove(os.path.join(luxblend_dir, '__init__.py'))
            # remove all folders
            DIRNAMES = 1
            for dir in next(os.walk(luxblend_dir))[DIRNAMES]:
                shutil.rmtree(os.path.join(luxblend_dir, dir))

            print('Copying new LuxBlend files')
            # copy new LuxBlend files
            # copy __init__.py
            shutil.copy2(os.path.join(extracted_luxblend_path, '__init__.py'), luxblend_dir)
            # copy all folders
            recursive_overwrite(extracted_luxblend_path, luxblend_dir)

        print('LuxBlend update finished, restart Blender for the changes to take effect.')
        print('-' * 20)
        self.report({'WARNING'}, 'Restart Blender!')
        return {'FINISHED'}
