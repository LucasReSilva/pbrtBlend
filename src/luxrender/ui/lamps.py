import bpy
from properties_data_lamp import DataButtonsPanel 

# EF API
from ef.ui import described_layout
from ef.ef import ef

# Lux API
import luxrender.properties.lamp

narrowui = 180

class lamps(DataButtonsPanel, described_layout):
    bl_label = 'LuxRender Lamps'
    COMPAT_ENGINES = {'luxrender'}
	
    property_group = luxrender.properties.lamp.luxrender_lamp

    # prevent creating luxrender_material property group in Scene
    property_group_non_global = True

    @staticmethod
    def property_reload():
        for lamp in bpy.data.lamps:
            lamps.property_create(lamp)
    
    @staticmethod
    def property_create(lamp):
        if not hasattr(lamp, lamps.property_group.__name__):
            ef.init_properties(lamp, [{
                'type': 'pointer',
                'attr': lamps.property_group.__name__,
                'ptype': lamps.property_group,
                'name': lamps.property_group.__name__,
                'description': lamps.property_group.__name__
            }], cache=False)
            ef.init_properties(lamps.property_group, lamps.properties, cache=False)
    
    # Overridden to provide data storage in the lamp, not the scene
    def draw(self, context):
        if context.lamp is not None:
            layout = self.layout
            lamps.property_create(context.lamp)

            lamp = context.lamp
            wide_ui = context.region.width > narrowui

            if wide_ui:
                layout.prop(lamp, "type", expand=True)
            else:
                layout.prop(lamp, "type", text="")
            
            # Show only certain controls for Blender's perspective lamp type 
            if context.lamp.type not in ['SPOT', 'AREA', 'SUN']:
                context.lamp.luxrender_lamp.type = 'UNSUPPORTED'
                layout.label(text="Lamp type not supported by LuxRender.")
            else:
                context.lamp.luxrender_lamp.type = context.lamp.type

                split = layout.split()

                # TODO: check which properties are supported by which light type
                col = split.column()
                sub = col.column()
                sub.prop(lamp, "color", text="")
                sub.prop(lamp, "energy", text="Gain")

                # SPOT LAMP: Blender Properties
                if lamp.type == 'SPOT':
                    lamp = context.lamp
                    wide_ui = context.region.width > narrowui

                    if wide_ui:
                        col = split.column()
                    col.prop(lamp, "spot_size", text="Size")
                    col.prop(lamp, "spot_blend", text="Blend", slider=True)
                elif wide_ui:
                    col = split.column()
                
                # LuxRender properties
                for p in self.controls:
                    self.draw_column(p, self.layout, context.lamp, supercontext=context)
    
    # luxrender properties
    controls = [
        ['power','efficacy'],
    ]
    
    visibility = {
        'power': { 'type': 'AREA'},
        'efficacy': { 'type': 'AREA'}
    }
    
    properties = [
        {
            'type': 'enum',
            'attr': 'type',
            'name': 'Luxrender Lamp type',
            'default': 'SPOT',
            'items': [
                ('UNSUPPORTED', 'Unsupported', 'UNSUPPORTED'),
                ('SPOT', 'Spot', 'SPOT'),
                ('AREA', 'Area', 'AREA'),
                ('SUN', 'Sun', 'SUN'),
            ]
        },    
        {
            'type': 'float',
            'attr': 'power',
            'name': 'Power',
            'default': 100.0,
        },   
        {
            'type': 'float',
            'attr': 'efficacy',
            'name': 'Efficacy',
            'default': 17.0,
        },      
    ]


