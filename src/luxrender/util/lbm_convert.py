'''
Created on 13 Apr 2011

@author: Doug Hammond
'''
import copy, json

LBX_VERSION = '0.71'

# Copied straight out of LuxBlend_0.1
def str2MatTex(s, tex = None):	# todo: this is not absolutely save from attacks!!!
	global LBX_VERSION
	
	s = s.strip()
	if (s[0]=='{') and (s[-1]=='}'):
		d = eval(s, dict(__builtins__=None))
		if type(d) is dict:
			def lb_list_to_dict(list):
				d = {}
				for t, k, v in list:
					if t == 'float':
						v = float(v)
						
					d[k] = v
				return d
			
			if LBX_VERSION == '0.6':
			
				if tex is not None and tex == True:
					test_str = 'TEXTURE'
				else:
					test_str = 'MATERIAL'
					
				if   ('LUX_DATA' in d.keys() and d['LUX_DATA'] == test_str) \
				and  ('LUX_VERSION' in d.keys() and (d['LUX_VERSION'] == '0.6' or d['LUX_VERSION'] == 0.6)):
					return d
				else:
					reason = 'Missing/incorrect metadata'
					
			elif LBX_VERSION == '0.7':
				
				if   ('version' in d.keys() and d['version'] in ['0.6', '0.7']) \
				and  ('type' in d.keys() and d['type'] in ['material', 'texture']) \
				and  ('definition' in d.keys()):
					try:
						definition = lb_list_to_dict(d['definition'])
						
						if 'metadata' in d.keys():
							definition.update( lb_list_to_dict(d['metadata']) )
						return definition
					except:
						reason = 'Incorrect LBX definition data'
				else: 
					reason = 'Missing/incorrect metadata'
			
			elif LBX_VERSION == '0.71':
				
				if   ('version' in d.keys() and d['version'] in ['0.6', '0.7', '0.71']) \
				and  ('type' in d.keys() and d['type'] in ['material', 'texture']) \
				and  ('definition' in d.keys()):
					try:
						definition = lb_list_to_dict(d['definition'])
						
						if 'metadata' in d.keys():
							definition.update( lb_list_to_dict(d['metadata']) )
						if 'volumes' in d.keys():
							definition['__volumes__'] = {}
							for volume in d['volumes']:
								definition['__volumes__'][volume['type']] = lb_list_to_dict(volume['definition'])
						return definition
					except:
						reason = 'Incorrect LBX definition data'
				else: 
					reason = 'Missing/incorrect metadata'
			else:
				reason = 'Unknown LBX version'
		else:
			reason = 'Not a parsed dict'
	else:
		reason = 'Not a stored dict'
			
			
	raise Exception("ERROR: string to material/texture conversion failed: %s" % reason)

def lbm2():
	return copy.deepcopy({
		'name': 'ConvertedMaterial',
		'version': '0.8',
		'category_id': -1,
		'objects': [],
		'metadata': {}
	})

o_count = 0

def lbm2_object():
	global o_count
	o_count += 1
	return copy.deepcopy({
		'type': '',
		'name': 'LBM2_Object_%s' % o_count,
		'extra_tokens': '',
		'paramset': []
	})

def paramset_item(type,name,value):
	return {
		'type': type,
		'name': name,
		'value': value
	}

def lookup_paramtype(name, value_hint=None):
	if name in ['Kd', 'Ks', 'Kt', 'Ka', 'Kr']:
		return "color"
	
	if name in ['uroughness', 'vroughness', 'amount']:
		return "float"
	
	return "float"

def cast_datatype(type, v):
	if type == 'color':
		return [float(c) for c in v.split(' ')]
	
	return v

def extract_vol(data, type):
	print('Found Volume; type=%s'%type)
	out_objs = []
	
	vol = lbm2_object()
	vol['type'] = 'MakeNamedVolume'
	vol['extra_tokens'] = '"%s"' % type
	vol['name'] = data['name']
	
	abs = [float(v) for v in data['absorption:sigma_a'].split(' ')]
	vol['paramset'].append( paramset_item('color', 'sigma_a', abs) )
	
	sct = [float(v) for v in data['sigma_s:sigma_s'].split(' ')]
	vol['paramset'].append( paramset_item('color', 'sigma_s', sct) )
	
	out_objs.append(vol)
	return out_objs

def get_texture_param_variant(param_name):
	if param_name in ['Kd', 'Ks', 'Kt', 'Ka', 'Kr']:
		return "color"
	
	return "float"

def extract_paramset(data):
	out_objs = []
	paramset = []
	for k,v in data.items():
		k_parts = k.split(':')
		k_parts.pop(0)
		if len(k_parts) == 1:
			param_name = k_parts.pop()
			if param_name.endswith('.value'):
				param_name = param_name[:-6]
				param_type = lookup_paramtype(param_name, v)
			elif param_name.endswith('.texture'):
				param_name = param_name[:-8]
				param_type = 'texture'
				tex_data = {}
				for tk,tv in data.items():
					if tk.startswith(':%s:'%param_name):
						tk_parts = tk.split(':')
						tex_data[ ':'.join(tk_parts[2:]) ] = tv
				out_objs.extend(extract_objects(tex_data, type_hint=v, variant_hint=lookup_paramtype(param_name)))
				if len(out_objs) > 0:
					v = out_objs[-1]['name']
			else:
				param_type = lookup_paramtype(param_name, v)
			
			paramset.append( paramset_item(param_type, param_name, cast_datatype(param_type, v)) )
	return out_objs, paramset

def extract_texture(data, type, variant_hint):
	print('Found Texture; type=%s'%type)
	print(data)
	out_objs = []
	tt = lbm2_object()
	tt['type'] = 'Texture'
	tt['extra_tokens'] = '"%s" "%s"' % (variant_hint, type)
	
	tt_objs, tt_paramset = extract_paramset(data)
	out_objs.extend(tt_objs)
	tt['paramset'].extend( tt_paramset )
	
	out_objs.append(tt)
	return out_objs

def extract_material(data, type):
	print('Found Material; type=%s'%type)
	out_objs = []
	
	mt = lbm2_object()
	mt['type'] = 'MakeNamedMaterial'
	mt['paramset'].append(paramset_item('string', 'type', type))
	
	mt_objs, mt_paramset = extract_paramset(data)
	out_objs.extend(mt_objs)
	mt['paramset'].extend( mt_paramset )
	
	out_objs.append(mt)
	return out_objs

def extract_objects(data, type_hint=None, variant_hint=None):
	object_list = []
	
	data_keys = data.keys()
	
	if 'type' in data_keys and type_hint == None:
		type = data['type']
	else:
		type = type_hint
	
	if type in ['homogeneous']:
		object_list.extend( extract_vol(data, type) )
	if type in ['glossytranslucent']:
		object_list.extend( extract_material(data, type) )
	if type in ['mix']:
		object_list.extend( extract_texture(data, type, variant_hint) )
	
	return object_list

def convert(lbm):
	lbm2_out = lbm2()
	lbm_keys = lbm.keys()
	
	gen = lbm['generator'] if 'generator' in lbm_keys else ''
	lbm2_out['metadata']['comment'] = 'converted from %s lbm data' % gen
	
	if '__volumes__' in lbm_keys:
		for vol in ['Exterior', 'Interior']:
			if vol in lbm['__volumes__'].keys():
				v_name = lbm['__volumes__'][vol]['name']
				#print('Found %s Volume: %s' % (vol, v_name) )
				if v_name != "world *":
					lbm2_out['metadata'][vol.lower()] = v_name
					vol_texs = extract_objects(lbm['__volumes__'][vol])
					lbm2_out['objects'].extend(vol_texs)
	
	mat_texs = extract_objects(lbm)
	lbm2_out['objects'].extend(mat_texs)
	lbm2_out['name'] = mat_texs[-1]['name']
	
	return lbm2_out

if __name__ == '__main__':
	import sys, pprint
	with open(sys.argv[1], 'r') as in_file:
		lbm_data_encoded = in_file.read()
	
	try:
		lbm_data = str2MatTex(lbm_data_encoded)
		pprint.pprint(lbm_data, indent=1)
		print('\nConverting...')
		lbm2_data = convert(lbm_data)
		print( json.dumps(lbm2_data, indent=1) )
	except Exception as err:
		print('Cannot convert: %s' % err)
		raise err
