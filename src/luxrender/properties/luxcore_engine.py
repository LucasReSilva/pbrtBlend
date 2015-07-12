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

from ..extensions_framework import declarative_property_group
from ..extensions_framework.validate import Logic_OR as O, Logic_Operator as LO, Logic_AND as A

from .. import LuxRenderAddon


@LuxRenderAddon.addon_register_class
class luxcore_opencl_devices(declarative_property_group):
    """
    Storage class for available OpenCL devices
    """

    ef_attach_to = []  # not attached
    alert = {}

    controls = [  # opencl_device_enabled is drawn manually in the UI class
                  'label_opencl_device_enabled'
    ]

    properties = [
        {
            'type': 'bool',
            'attr': 'opencl_device_enabled',
            'name': 'Enabled',
            'description': 'Enable this OpenCL device',
            'default': True
        },
    ]


@LuxRenderAddon.addon_register_class
class luxcore_enginesettings(declarative_property_group):
    """
    Storage class for LuxCore engine settings.

    Labels are used to minimize visual noise of non-equal button widths:
    Instead of this
        Engine:         [ Bidir ]
        [x] Clamp   (    100    )

    We get this
        Engine:     [   Bidir   ]
        [x] Clamp   (    100    )

    So far this is only implemented for the default controls, "advanced" users still see a mess.
    """

    ef_attach_to = ['Scene']

    controls = [
        ['label_renderengine_type', 'renderengine_type'],
        'label_custom_properties',
        'custom_properties',
        # BIDIR
        ['bidir_eyedepth', 'bidir_lightdepth'],
        # PATH
        ['label_path_maxdepth', 'path_maxdepth'],
        # BIDIRVMCPU
        ['bidirvm_eyedepth', 'bidirvm_lightdepth'],
        'bidirvm_lightpath_count',
        ['bidirvm_startradius_scale', 'bidirvm_alpha'],
        # BIASPATH
        'label_sampling',
        'biaspath_sampling_aa_size',
        ['biaspath_sampling_diffuse_size', 'biaspath_sampling_glossy_size', 'biaspath_sampling_specular_size'],
        'label_path_depth',
        'biaspath_pathdepth_total',
        ['biaspath_pathdepth_diffuse', 'biaspath_pathdepth_glossy', 'biaspath_pathdepth_specular'],
        ['use_clamping', 'biaspath_clamping_radiance_maxvalue'],
        ['spacer_pdf_clamping', 'biaspath_clamping_pdf_value'],
        'label_lights',
        'biaspath_lights_samplingstrategy_type',
        'biaspath_lights_nearstart',
        ['label_sampler_type', 'sampler_type'],
        ['label_biaspath_sampler_type', 'biaspath_sampler_type'],
        # Advanced sampler settings (for all but BIASPATH)
        ['label_largesteprate', 'largesteprate'],
        ['label_maxconsecutivereject', 'maxconsecutivereject'],
        ['label_imagemutationrate', 'imagemutationrate'],
        # Filter settings (for all but BIASPATH)
        ['label_filter_type', 'filter_type'],
        ['label_filter_width', 'filter_width'],
        # Accelerator settings
        ['label_accelerator_type', 'accelerator_type'],
        ['spacer_instancing', 'instancing'],
        # Kernel cache
        ['label_kernelcache', 'kernelcache'],
        # BIASPATH specific halt condition
        'label_halt_conditions',
        ['tile_multipass_enable', 'tile_multipass_convergencetest_threshold'],
        ['tile_multipass_use_threshold_reduction', 'tile_multipass_convergencetest_threshold_reduction'],
    ]

    visibility = {
        'label_custom_properties': {'advanced': True},
        'custom_properties': {'advanced': True},
        # BIDIR
        'bidir_eyedepth': {'renderengine_type': 'BIDIR'},
        'bidir_lightdepth': {'renderengine_type': 'BIDIR'},
        # PATH
        'label_path_maxdepth': {'renderengine_type': 'PATH'},
        'path_maxdepth': {'renderengine_type': 'PATH'},
        # BIDIRVM
        'bidirvm_eyedepth': {'renderengine_type': 'BIDIRVM'},
        'bidirvm_lightdepth': {'renderengine_type': 'BIDIRVM'},
        'bidirvm_lightpath_count': {'advanced': True, 'renderengine_type': 'BIDIRVM'},
        'bidirvm_startradius_scale': {'advanced': True, 'renderengine_type': 'BIDIRVM'},
        'bidirvm_alpha': {'advanced': True, 'renderengine_type': 'BIDIRVM'},
        # BIASPATH noise controls
        'label_halt_conditions': {'renderengine_type': 'BIASPATH'},
        'tile_multipass_enable': {'renderengine_type': 'BIASPATH'},
        'tile_multipass_convergencetest_threshold': {'renderengine_type': 'BIASPATH'},
        'tile_multipass_use_threshold_reduction': {'renderengine_type': 'BIASPATH'},
        'tile_multipass_convergencetest_threshold_reduction': {'renderengine_type': 'BIASPATH'},
        # BIASPATH sampling
        'label_sampling': {'renderengine_type': 'BIASPATH'},
        'biaspath_sampling_aa_size': {'renderengine_type': 'BIASPATH'},
        'biaspath_sampling_diffuse_size': {'renderengine_type': 'BIASPATH'},
        'biaspath_sampling_glossy_size': {'renderengine_type': 'BIASPATH'},
        'biaspath_sampling_specular_size': {'renderengine_type': 'BIASPATH'},
        # BIASPATH path depth
        'label_path_depth': {'renderengine_type': 'BIASPATH'},
        'biaspath_pathdepth_total': {'renderengine_type': 'BIASPATH'},
        'biaspath_pathdepth_diffuse': {'renderengine_type': 'BIASPATH'},
        'biaspath_pathdepth_glossy': {'renderengine_type': 'BIASPATH'},
        'biaspath_pathdepth_specular': {'renderengine_type': 'BIASPATH'},
        # BIASPATH obscure features
        'label_lights':  A([{'advanced': True}, {'renderengine_type': 'BIASPATH'}]),
        'biaspath_lights_samplingstrategy_type': A([{'advanced': True}, {'renderengine_type': 'BIASPATH'}]),
        'biaspath_lights_nearstart': A([{'advanced': True}, {'renderengine_type': 'BIASPATH'}]),
        # Clamping (all unidirectional path engines)
        'use_clamping': {'renderengine_type': O(['BIASPATH', 'PATH'])},
        'biaspath_clamping_radiance_maxvalue': {'renderengine_type': O(['BIASPATH', 'PATH'])},
        'spacer_pdf_clamping': A([{'advanced': True}, {'renderengine_type': O(['BIASPATH', 'PATH'])}]),
        'biaspath_clamping_pdf_value': A([{'advanced': True}, {'renderengine_type': O(['BIASPATH', 'PATH'])}]),
        # Sampler settings, show for all but BIASPATH
        'label_sampler_type': {'renderengine_type': O(['PATH', 'BIDIR', 'BIDIRVM'])},
        'sampler_type': {'renderengine_type': O(['PATH', 'BIDIR', 'BIDIRVM'])},
        'label_largesteprate': A([{'advanced': True}, {'sampler_type': 'METROPOLIS'},
            {'renderengine_type': O(['PATH', 'BIDIR', 'BIDIRVM'])}]),
        'largesteprate': A([{'advanced': True}, {'sampler_type': 'METROPOLIS'},
            {'renderengine_type': O(['PATH', 'BIDIR', 'BIDIRVM'])}]),
        'label_maxconsecutivereject': A([{'advanced': True}, {'sampler_type': 'METROPOLIS'},
            {'renderengine_type': O(['PATH', 'BIDIR', 'BIDIRVM'])}]),
        'maxconsecutivereject': A([{'advanced': True}, {'sampler_type': 'METROPOLIS'},
            {'renderengine_type': O(['PATH', 'BIDIR', 'BIDIRVM'])}]),
        'label_imagemutationrate': A([{'advanced': True}, {'sampler_type': 'METROPOLIS'},
            {'renderengine_type': O(['PATH', 'BIDIR', 'BIDIRVM'])}]),
        'imagemutationrate': A([{'advanced': True}, {'sampler_type': 'METROPOLIS'},
            {'renderengine_type': O(['PATH', 'BIDIR', 'BIDIRVM'])}]),
        # Fake sampler settings for BIASPATH
        'label_biaspath_sampler_type': {'renderengine_type': 'BIASPATH'},
        'biaspath_sampler_type': {'renderengine_type': 'BIASPATH'},
        # Filter settings
        'label_filter_type': {'advanced': True},
        'filter_type': {'advanced': True},
        # don't show filter width if NONE filter is selected
        'filter_width': {'filter_type': O(['BLACKMANHARRIS', 'MITCHELL', 'MITCHELL_SS', 'BOX', 'GAUSSIAN'])},
        # Accelerator settings
        'label_accelerator_type': {'advanced': True},
        'accelerator_type': {'advanced': True},
        'spacer_instancing': {'advanced': True},
        'instancing': {'advanced': True},
        # Kernel cache
        'label_kernelcache': A([{'advanced': True}, {'renderengine_type': O(['PATH', 'BIASPATH'])}, {'device': 'OCL'}]),
        'kernelcache': A([{'advanced': True}, {'renderengine_type': O(['PATH', 'BIASPATH'])}, {'device': 'OCL'}]),
    }

    alert = {}

    enabled = {
        # Clamping value
        'biaspath_clamping_radiance_maxvalue': {'use_clamping': True},
        'biaspath_clamping_pdf_value': {'use_clamping': True},
        # BIASPATH noise multiplier
        'tile_multipass_convergencetest_threshold': {'tile_multipass_enable': True},
        'tile_multipass_use_threshold_reduction': {'tile_multipass_enable': True},
        'tile_multipass_convergencetest_threshold_reduction': {'tile_multipass_enable': True, 
                                                               'tile_multipass_use_threshold_reduction': True},
    }

    properties = [
        {
            'type': 'bool',
            'attr': 'advanced',
            'name': 'Advanced Settings',
            'description': 'Super advanced settings you\'ll never need to change',
            'default': False,
            'save_in_preset': True
        },
        {
            'type': 'text',
            'attr': 'label_renderengine_type',
            'name': 'Engine:',
        },
        {
            'type': 'enum',
            'attr': 'renderengine_type',
            'name': '',
            'description': 'Rendering engine to use',
            'default': 'BIDIR',
            'items': [
                ('PATH', 'Path', 'Path tracer'),
                ('BIASPATH', 'Biased Path', 'Biased path tracer'),
                ('BIDIR', 'Bidir', 'Bidirectional path tracer'),
                ('BIDIRVM', 'BidirVM', 'Bidirectional path tracer with vertex merging'),
            ],
            'save_in_preset': True
        },
        {
            'type': 'enum',
            'attr': 'device',
            'name': 'Final Device',
            'description': 'Device',
            'default': 'CPU',
            'items': [
                ('CPU', 'CPU', 'Use CPU only rendering'),
                ('OCL', 'OpenCL', 'Use OpenCL to render on GPUs, CPUs or both (see "Compute Settings" panel for details)'),
            ],
            'expand': True,
            'save_in_preset': True
        },
        {
            # Fake device to show that only a CPU version of the engine exists
            'type': 'enum',
            'attr': 'device_cpu_only',
            'name': 'Final Device',
            'description': 'Device',
            'default': 'CPU',
            'items': [
                ('CPU', 'CPU', 'Use CPU only rendering'),
                ('OCL', 'OpenCL', 'Not supported by the selected renderengine'),
            ],
            'expand': True,
            'save_in_preset': True
        },
        {
            # Device that is used for viewport rendering
            'type': 'enum',
            'attr': 'device_preview',
            'name': 'Preview Device',
            'description': 'CPU rendering has lower latency, GPU rendering is faster',
            'default': 'CPU',
            'items': [
                ('CPU', 'CPU', 'Use the CPU (slow rendering, fast updates)'),
                ('OCL', 'OpenCL', 'Use the graphics card via OpenCL (fast rendering, slow updates)'),
            ],
            'expand': True,
            'save_in_preset': True
        },
        {
            'type': 'text',
            'attr': 'label_custom_properties',
            'name': 'Custom properties:',
        },
        {
            'type': 'string',
            'attr': 'custom_properties',
            'name': '',
            'description': 'LuxCore custom properties (separated by \'|\', suggested only for advanced users)',
            'default': '',
            'save_in_preset': True
        },
        {   # BIDIR
            'type': 'int',
            'attr': 'bidir_eyedepth',
            'name': 'Max Eye Depth',
            'description': 'Max recursion depth for ray casting from eye',
            'default': 16,
            'min': 1,
            'max': 2048,
            'save_in_preset': True
        },  
        {
            'type': 'int',
            'attr': 'bidir_lightdepth',
            'name': 'Max Light Depth',
            'description': 'Max recursion depth for ray casting from light',
            'default': 16,
            'min': 1,
            'max': 2048,
            'save_in_preset': True
        },
        {   # PATH
            'type': 'text',
            'attr': 'label_path_maxdepth',
            'name': 'Max Depth:',
        },
        {
            'type': 'int',
            'attr': 'path_maxdepth',
            'name': '',
            'description': 'Max recursion depth for ray casting from eye',
            'default': 8,
            'min': 1,
            'max': 2048,
            'save_in_preset': True
        },
        {   # BIDIRVM
            'type': 'int',
            'attr': 'bidirvm_eyedepth',
            'name': 'Max Eye Depth',
            'description': 'Max recursion depth for ray casting from eye',
            'default': 16,
            'min': 1,
            'max': 2048,
            'save_in_preset': True
        },  
        {
            'type': 'int',
            'attr': 'bidirvm_lightdepth',
            'name': 'Max Light Depth',
            'description': 'Max recursion depth for ray casting from light',
            'default': 16,
            'min': 1,
            'max': 2048,
            'save_in_preset': True
        },  
        {   
            'type': 'int',
            'attr': 'bidirvm_lightpath_count',
            'name': 'Lightpath Count',
            'description': '',
            'default': 16000,
            'min': 1000,
            'max': 1000000,
            'save_in_preset': True
        },
        {
            'type': 'float',
            'attr': 'bidirvm_startradius_scale',
            'name': 'Startradius Scale',
            'description': '',
            'default': 0.003,
            'min': 0.0001,
            'max': 0.1,
            'precision': 4,
            'save_in_preset': True
        },
        {
            'type': 'float',
            'attr': 'bidirvm_alpha',
            'name': 'Alpha',
            'description': '',
            'default': 0.95,
            'min': 0.5,
            'max': 0.99,
            'save_in_preset': True
        },
        {   # BIASPATH
            'type': 'text',
            'name': 'Tiles:',
            'attr': 'label_tiles',
        },
        {
            'type': 'int',
            'attr': 'tile_size',
            'name': 'Tile size',
            'description': 'Tile width and height in pixels',
            'default': 32,
            'min': 8,
            'max': 2048,
            'save_in_preset': True
        },
        {
            'type': 'bool',
            'attr': 'tile_multipass_enable',
            'name': 'Adaptive Rendering',
            'description': 'Continue rendering until the noise threshold is reached',
            'default': True,
            'save_in_preset': True
        },
        {
            'type': 'float',
            'attr': 'tile_multipass_convergencetest_threshold',
            'name': 'Noise level',
            'description': 'Lower values mean less noise',
            'default': 0.05,
            'min': 0.000001,
            'soft_min': 0.02,
            'max': 0.9,
            'save_in_preset': True
        },
        {
            'type': 'bool',
            'attr': 'tile_multipass_use_threshold_reduction',
            'name': 'Reduce Noise Level',
            'description': 'When the target noise level is reached, reduce it with the multiplier and continue \
rendering with the reduced noise level',
            'default': True,
            'save_in_preset': True
        },
        {
            'type': 'float',
            'attr': 'tile_multipass_convergencetest_threshold_reduction',
            'name': 'Multiplier',
            'description': 'Multiply noise level with this value after all tiles have converged',
            'default': 0.5,
            'min': 0.001,
            'soft_min': 0.1,
            'max': 0.99,
            'soft_max': 0.9,
            'save_in_preset': True
        },
        {
            'type': 'text',
            'name': 'Sampling:',
            'attr': 'label_sampling',
        },
        {
            'type': 'int',
            'attr': 'biaspath_sampling_aa_size',
            'name': 'AA Samples',
            'description': 'Anti-aliasing samples',
            'default': 3,
            'min': 1,
            'max': 64,
            'save_in_preset': True
        },
        {
            'type': 'int',
            'attr': 'biaspath_sampling_diffuse_size',
            'name': 'Diffuse',
            'description': 'Diffuse material samples (e.g. matte)',
            'default': 2,
            'min': 1,
            'max': 64,
            'save_in_preset': True
        },
        {
            'type': 'int',
            'attr': 'biaspath_sampling_glossy_size',
            'name': 'Glossy',
            'description': 'Glossy material samples (e.g. glossy, metal)',
            'default': 2,
            'min': 1,
            'max': 64,
            'save_in_preset': True
        },
        {
            'type': 'int',
            'attr': 'biaspath_sampling_specular_size',
            'name': 'Specular',
            'description': 'Specular material samples (e.g. glass, mirror)',
            'default': 1,
            'min': 1,
            'max': 64,
            'save_in_preset': True
        },
        {
            'type': 'text',
            'name': 'Path depths:',
            'attr': 'label_path_depth',
        },
        {
            'type': 'int',
            'attr': 'biaspath_pathdepth_total',
            'name': 'Max Total Depth',
            'description': 'Max recursion total depth for a path',
            'default': 10,
            'min': 1,
            'max': 2048,
            'save_in_preset': True
        },
        {
            'type': 'int',
            'attr': 'biaspath_pathdepth_diffuse',
            'name': 'Diffuse',
            'description': 'Max recursion depth for a diffuse path',
            'default': 2,
            'min': 0,
            'max': 2048,
            'save_in_preset': True
        },
        {
            'type': 'int',
            'attr': 'biaspath_pathdepth_glossy',
            'name': 'Glossy',
            'description': 'Max recursion depth for a glossy path',
            'default': 1,
            'min': 0,
            'max': 2048,
            'save_in_preset': True
        },
        {
            'type': 'int',
            'attr': 'biaspath_pathdepth_specular',
            'name': 'Specular',
            'description': 'Max recursion depth for a specular path',
            'default': 5,
            'min': 0,
            'max': 2048,
            'save_in_preset': True
        },
        {
            'type': 'bool',
            'attr': 'use_clamping',
            'name': 'Clamp Brightness',
            'description': '',
            'default': False,
            'save_in_preset': True
        },
        {
            'type': 'float',
            'attr': 'biaspath_clamping_radiance_maxvalue',
            'name': 'Max Brightness',
            'description': 'Max acceptable radiance value for a sample (0.0 = disabled). Used to prevent fireflies',
            'default': 0.0,
            'min': 0.0,
            'max': 999999.0,
            'save_in_preset': True
        },
        {
            'type': 'text',
            'attr': 'spacer_pdf_clamping',
            'name': '',
        },
        {
            'type': 'float',
            'attr': 'biaspath_clamping_pdf_value',
            'name': 'PDF clamping',
            'description': 'Max acceptable PDF (0.0 = disabled)',
            'default': 0.0,
            'min': 0.0,
            'max': 999.0,
            'save_in_preset': True
        },
        {
            'type': 'text',
            'name': 'Lights:',
            'attr': 'label_lights',
        },
        {
            'type': 'enum',
            'attr': 'biaspath_lights_samplingstrategy_type',
            'name': 'Sampling strategy',
            'description': 'How to sample multiple light sources',
            'default': 'ALL',
            'items': [
                ('ALL', 'ALL', 'ALL'),
                ('ONE', 'ONE', 'ONE'),
            ],
            'save_in_preset': True
        },
        {
            'type': 'float',
            'attr': 'biaspath_lights_nearstart',
            'name': 'Near start',
            'description': 'How far, from the light source, must be a point to receive light',
            'default': 0.001,
            'min': 0.0,
            'max': 1000.0,
            'save_in_preset': True
        },  
        # Sampler settings
        {
            'type': 'text',
            'attr': 'label_sampler_type',
            'name': 'Sampler:',
        },
        {
            'type': 'enum',
            'attr': 'sampler_type',
            'name': '',
            'description': 'Pixel sampling algorithm to use',
            'default': 'METROPOLIS',
            'items': [
                ('METROPOLIS', 'Metropolis', 'Recommended for scenes with difficult lighting (caustics, indoors)'),
                ('SOBOL', 'Sobol', 'Recommended for scenes with simple lighting (outdoors, studio setups)'),
            ],
            'save_in_preset': True
        },
        {
            'type': 'text',
            'attr': 'label_largesteprate',
            'name': 'Large Mutation Probability:',
        },
        {
            'type': 'float',
            'attr': 'largesteprate',
            'name': '',
            'description': 'Probability of a completely random mutation rather than a guided one. Lower values \
increase sampler strength',
            'default': 0.4,
            'min': 0,
            'max': 1,
            'slider': True,
            'save_in_preset': True
        },
        {
            'type': 'text',
            'attr': 'label_maxconsecutivereject',
            'name': 'Max Consecutive Rejections:',
        },
        {
            'type': 'int',
            'attr': 'maxconsecutivereject',
            'name': '',
            'description': 'Maximum amount of samples in a particular area before moving on. Setting this too low \
may mute lamps and caustics',
            'default': 512,
            'min': 128,
            'max': 2048,
            'save_in_preset': True
        },
        {
            'type': 'text',
            'attr': 'label_imagemutationrate',
            'name': 'Image Mutation Rate:',
        },
        {
            'type': 'float',
            'attr': 'imagemutationrate',
            'name': '',
            'description': '',
            'default': 0.1,
            'min': 0,
            'max': 1,
            'slider': True,
            'save_in_preset': True
        },
        # Fake sampler to show to the user that BIASPATH sampler is fixed
        {
            'type': 'text',
            'attr': 'label_biaspath_sampler_type',
            'name': 'Sampler:',
        },
        {
            'type': 'enum',
            'attr': 'biaspath_sampler_type',
            'name': '',
            'description': 'Pixel sampling algorithm to use',
            'default': 'SOBOL',
            'items': [
                ('SOBOL', 'Stratified Sampler', 'Biased Path uses a fixed stratified sampler'),
            ],
            'save_in_preset': True
        },
        # Filter settings
        {
            'type': 'text',
            'attr': 'label_filter_type',
            'name': 'Filter Type:',
        },
        {
            'type': 'enum',
            'attr': 'filter_type',
            'name': '',
            'description': 'Pixel filter to use',
            'default': 'BLACKMANHARRIS',
            'items': [
                ('BLACKMANHARRIS', 'Blackman-Harris', 'default'),
                ('MITCHELL', 'Mitchell', 'can produce black ringing artifacts around bright pixels'),
                ('MITCHELL_SS', 'Mitchell_SS', ''),
                ('BOX', 'Box', ''),
                ('GAUSSIAN', 'Gaussian', ''),
                ('NONE', 'None', 'Disable pixel filtering. Fastest setting when rendering on GPU')
            ],
            'save_in_preset': True
        },
        {
            'type': 'text',
            'attr': 'label_filter_width',
            'name': 'Filter Width:',
        },
        {
            'type': 'float',
            'attr': 'filter_width',
            'name': 'Pixels',
            'description': 'Filter width in pixels. Lower values result in a sharper image, higher values smooth out noise',
            'default': 2.0,
            'min': 0.5,
            'soft_min': 0.5,
            'max': 10.0,
            'soft_max': 4.0,
            'save_in_preset': True
        },
        # Accelerator settings
        {
            'type': 'text',
            'attr': 'label_accelerator_type',
            'name': 'Accelerator:',
        },
        {
            'type': 'enum',
            'attr': 'accelerator_type',
            'name': '',
            'description': 'Accelerator to use',
            'default': 'AUTO',
            'items': [
                ('AUTO', 'Auto', 'Automatically choose the best accelerator for each device (strongly recommended!)'),
                ('BVH', 'BVH', 'Static BVH'),
                ('MBVH', 'MBVH', 'Dynamic BVH'),
                ('QBVH', 'QBVH', 'Static QBVH'),
                ('MQBVH', 'MQBVH', 'Dynamic QBVH'),
                ('EMBREE', 'Embree', 'Fastest build times and render speed. Supports only one substep for motion blur. \
Not supported for OpenCL engines')
            ],
            'save_in_preset': True
        },
        {
            'type': 'text',
            'attr': 'spacer_instancing',
            'name': '',
        },
        {
            'type': 'bool',
            'attr': 'instancing',
            'name': 'Use Instancing',
            'description': 'Lower memory usage for instances (like particles), but also lower rendering speed',
            'default': True,
            'save_in_preset': True
        },
        # Kernel cache
        {
            'type': 'text',
            'attr': 'label_kernelcache',
            'name': 'Kernel Cache:',
        },
        {
            'type': 'enum',
            'attr': 'kernelcache',
            'name': '',
            'description': 'Kernel cache mode',
            'default': 'PERSISTENT',
            'items': [
                ('PERSISTENT', 'Persistent', ''),
                ('VOLATILE', 'Volatile', ''),
                ('NONE', 'None', ''),
            ],
            'save_in_preset': True
        },
        # Compute settings
        {
            'type': 'text',
            'name': 'Compute settings:',
            'attr': 'label_compute_settings',
        },  
        # CPU settings
        {
            'type': 'bool',
            'attr': 'auto_threads',
            'name': 'Auto Threads',
            'description': 'Auto-detect the optimal number of CPU threads',
            'default': True,
        },
        {
            'type': 'int',
            'attr': 'native_threads_count',
            'name': 'Threads count',
            'description': 'Number of CPU threads used for the rendering',
            'default': 4,
            'min': 1,
            'max': 512,
        },  
        # OpenCL settings
        {
            'type': 'collection',
            'ptype': luxcore_opencl_devices,
            'attr': 'luxcore_opencl_devices',
            'name': 'OpenCL Devices',
            'items': []
        },
        {
            'type': 'operator',
            'attr': 'op_opencl_device_list_update',
            'operator': 'luxrender.opencl_device_list_update',
            'text': 'Update OpenCL device list',
        },
        # Halt condition settings (halt time and halt spp)
        {
            'type': 'text',
            'name': 'Halt Conditions:',
            'attr': 'label_halt_conditions',
        },
        {
            'type': 'bool',
            'attr': 'use_halt_samples',
            'name': 'Samples',
            'description': 'Rendering process will stop at specified amount of samples',
            'default': False,
            'save_in_preset': True
        },
        {
            'type': 'int',
            'attr': 'halt_samples',
            'name': '',
            'description': 'Rendering process will stop at specified amount of samples',
            'default': 100,
            'min': 1,
            'soft_min': 5,
            'soft_max': 2000,
            'save_in_preset': True
        },
        {
            'type': 'int',
            'attr': 'halt_samples_preview',
            'name': '',
            'description': 'Viewport rendering process will stop at specified amount of samples',
            'default': 20,
            'min': 1,
            'soft_min': 5,
            'soft_max': 2000,
            'save_in_preset': True
        },
        {
            'type': 'bool',
            'attr': 'use_halt_time',
            'name': 'Time',
            'description': 'Rendering process will stop after specified amount of seconds',
            'default': False,
            'save_in_preset': True
        },
        {
            'type': 'int',
            'attr': 'halt_time',
            'name': '',
            'description': 'Rendering process will stop after specified amount of seconds',
            'default': 60,
            'min': 1,
            'soft_min': 5,
            'soft_max': 3600,
            'save_in_preset': True
        },
        {
            'type': 'int',
            'attr': 'halt_time_preview',
            'name': '',
            'description': 'Viewport rendering process will stop after specified amount of seconds',
            'default': 10,
            'min': 1,
            'soft_max': 120,
            'save_in_preset': True
        },
        {
            'type': 'bool',
            'attr': 'use_halt_noise',
            'name': 'Noise',
            'description': 'Rendering process will stop when the specified noise level is reached',
            'default': False,
            'save_in_preset': True
        },
        {
            'type': 'float',
            'attr': 'halt_noise',
            'name': '',
            'description': 'Rendering process will stop when the specified noise level is reached (lower = less noise)',
            'default': 0.0001,
            'min': 0.000001,
            'max': 0.9,
            'save_in_preset': True
        },
        {
            'type': 'float',
            'attr': 'halt_noise_preview',
            'name': '',
            'description': 'Viewport rendering process will stop when the specified noise level is reached (lower = \
less noise)',
            'default': 0.1,
            'min': 0.000001,
            'max': 0.9,
            'save_in_preset': True
        },
    ]
