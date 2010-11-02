
from luxrender.export import ParamSet
from luxrender.export.film import resolution

def preview_scene(scene, lux_context, obj=None, mat=None):
	
	HALTSPP = 8
	
	# Camera
	lux_context.lookAt(0.0,-3.0,0.5, 0.0,-2.0,0.5, 0.0,0.0,1.0)
	camera_params = ParamSet().add_float('fov', 22.5)
	lux_context.camera('perspective', camera_params)
	
	# Film
	xr, yr = resolution(scene)
	
	film_params = ParamSet() \
		.add_integer('xresolution', int(xr)) \
		.add_integer('yresolution', int(yr)) \
		.add_string('filename', 'luxblend25-preview') \
		.add_bool('write_exr', False) \
		.add_bool('write_png', True) \
		.add_bool('write_tga', False) \
		.add_bool('write_resume_flm', False) \
		.add_integer('displayinterval', 3) \
		.add_integer('writeinterval', 3600) \
		.add_integer('haltspp', 1) \
		.add_string('tonemapkernel', 'linear') \
		.add_integer('reject_warmup', 64)
	lux_context.film('fleximage', film_params)
	
	# Pixel Filter
	pixelfilter_params = ParamSet() \
		.add_float('xwidth', 1.5) \
		.add_float('ywidth', 1.5) \
		.add_float('B', 0.333) \
		.add_float('C', 0.333) \
		.add_bool('supersample', True)
	lux_context.pixelFilter('mitchell', pixelfilter_params)
	
	# Sampler
	sampler_params = ParamSet() \
		.add_string('pixelsampler', 'hilbert') \
		.add_integer('pixelsamples', HALTSPP)
	lux_context.sampler('lowdiscrepancy', sampler_params)
	
	# Surface Integrator
	surfaceintegrator_params = ParamSet() \
		.add_integer('directsamples', 1) \
		.add_integer('diffusereflectdepth', 1) \
		.add_integer('diffusereflectsamples', 4) \
		.add_integer('diffuserefractdepth', 4) \
		.add_integer('diffuserefractsamples', 1) \
		.add_integer('glossyreflectdepth', 1) \
		.add_integer('glossyreflectsamples', 2) \
		.add_integer('glossyrefractdepth', 4) \
		.add_integer('glossyrefractsamples', 1) \
		.add_integer('specularreflectdepth', 2) \
		.add_integer('specularrefractdepth', 4)
	lux_context.surfaceIntegrator('distributedpath', surfaceintegrator_params)
	
	lux_context.worldBegin()
	
#def preview_scene_lights(lux_context):
	# Light
	lux_context.transformBegin()
	lux_context.transform([
		1.0, 0.0, 0.0, 0.0,
		0.0, 1.0, 0.0, 0.0,
		0.0, 0.0, 1.0, 0.0,
		1.0, -1.0, 4.0, 1.0
	])
	light_bb_params = ParamSet().add_float('temperature', 6500.0)
	lux_context.texture('pL', 'color', 'blackbody', light_bb_params)
	light_params = ParamSet() \
		.add_texture('L', 'pL') \
		.add_float('gain', 0.002)
	lux_context.lightSource('point', light_params)
	lux_context.transformEnd()
	
	# back drop
	lux_context.attributeBegin()
	lux_context.transform([
		5.0, 0.0, 0.0, 0.0,
		0.0, 5.0, 0.0, 0.0,
		0.0, 0.0, 5.0, 0.0,
		0.0, 0.0, 0.0, 1.0
	])
	checks_pattern_params = ParamSet() \
		.add_integer('dimension', 2) \
		.add_string('mapping', 'uv') \
		.add_float('uscale', 36.8) \
		.add_float('vscale', 36.0) #.add_string('aamode', 'supersample') \
	lux_context.texture('checks::pattern', 'float', 'checkerboard', checks_pattern_params)
	checks_params = ParamSet() \
		.add_texture('amount', 'checks::pattern') \
		.add_color('tex1', [0.9, 0.9, 0.9]) \
		.add_color('tex2', [0.0, 0.0, 0.0])
	lux_context.texture('checks', 'color', 'mix', checks_params)
	mat_params = ParamSet().add_texture('Kd', 'checks')
	lux_context.material('matte', mat_params)
	bd_shape_params = ParamSet() \
		.add_integer('nlevels', 3) \
		.add_bool('dmnormalsmooth', True) \
		.add_bool('dmsharpboundary', False) \
		.add_integer('ntris', 18) \
		.add_integer('nvertices', 8) \
		.add_integer('indices', [0,1,2,0,2,3,1,0,4,1,4,5,5,4,6,5,6,7]) \
		.add_point('P', [
			 1.0,  1.0, 0.0,
			-1.0,  1.0, 0.0,
			-1.0, -1.0, 0.0,
			 1.0, -1.0, 0.0,
			 1.0,  3.0, 0.0,
			-1.0,  3.0, 0.0,
			 1.0,  3.0, 2.0,
			-1.0,  3.0, 2.0,
		]) \
		.add_normal('N', [
			0.0,  0.000000, 1.000000,
			0.0,  0.000000, 1.000000,
			0.0,  0.000000, 1.000000,
			0.0,  0.000000, 1.000000,
			0.0, -0.707083, 0.707083,
			0.0, -0.707083, 0.707083,
			0.0, -1.000000, 0.000000,
			0.0, -1.000000, 0.000000,
		]) \
		.add_float('uv', [
			0.333334, 0.000000,
			0.333334, 0.333334,
			0.000000, 0.333334,
			0.000000, 0.000000,
			0.666667, 0.000000,
			0.666667, 0.333333,
			1.000000, 0.000000,
			1.000000, 0.333333,
		])
	lux_context.shape('loopsubdiv', bd_shape_params)
	lux_context.attributeEnd()
	
	if obj is not None and mat is not None:
		# preview object
		lux_context.attributeBegin()
		lux_context.transform([
			0.5, 0.0, 0.0, 0.0,
			0.0, 0.5, 0.0, 0.0,
			0.0, 0.0, 0.5, 0.0,
			0.0, 0.0, 0.5, 1.0
		])
		mat.luxrender_material.export(scene, lux_context, mat, mode='direct')
		sphere_params = ParamSet().add_float('radius', 1.0)
		lux_context.shape('sphere', sphere_params)
		lux_context.attributeEnd()
	
	return int(xr), int(yr)
	