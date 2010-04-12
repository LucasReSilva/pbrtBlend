import bpy

import luxrender.pylux
import luxrender.module
import luxrender.module.paramset

from luxrender.module.file_api import Files

def write_lxo(l, scene):
    # l = self.LuxManager.lux_context

    sel = scene.objects
    for ob in sel:

        if ob.type in ('LAMP', 'CAMERA', 'EMPTY', 'META', 'ARMATURE'):
            continue

        # materials are exported in write_lxm()
        # me = ob.data
        # me_materials = me.materials

        me = ob.create_mesh(scene, True, 'RENDER')

        if not me:
            continue

        # get object matrix
        matrix = ob.matrix

        l.attributeBegin(comment=ob.name, file=Files.GEOM)

        # object translation/rotation/scale 
        l.transform(matrix[0][0], matrix[0][1], matrix[0][2], matrix[0][3],\
                matrix[1][0], matrix[1][1], matrix[1][2], matrix[1][3],\
                matrix[2][0], matrix[2][1], matrix[2][2], matrix[2][3],\
                matrix[3][0], matrix[3][1], matrix[3][2], matrix[3][3])
        
        # dummy material for now
        l.material('matte')

        faces_verts = [f.verts for f in me.faces]
        ffaces = [f for f in me.faces]
        faces_normals = [tuple(f.normal) for f in me.faces]
        verts_normals = [tuple(v.normal) for v in me.verts]

        # face indices
        index = 0
        indices = []
        for face in ffaces:
            indices.append(index)
            indices.append(index+1)
            indices.append(index+2)
            if (len(face.verts)==4):
                indices.append(index)
                indices.append(index+2)
                indices.append(index+3)
            index += len(face.verts)

        # vertex positions
        points = []
        for face in ffaces:
            for vertex in face.verts:
                v = me.verts[vertex]
                for co in v.co:
                    points.append(co)

        # vertex normals
        normals = []
        for face in ffaces:
            normal = face.normal
            for vertex in face.verts:
                if (face.smooth):
                    normal = vertex.normal
                for no in normal:
                    normals.append(no)

        # uv coordinates
        try:
            uv_layer = me.active_uv_texture.data
        except:
            uv_layer = None

        if uv_layer:
            uvs = []
            for fi, uv in enumerate(uv_layer):
                if len(faces_verts[fi]) == 4:
                    face_uvs = uv.uv1, uv.uv2, uv.uv3, uv.uv4
                else:
                    face_uvs = uv.uv1, uv.uv2, uv.uv3
                for uv in face_uvs:
                    for single_uv in uv:
                        uvs.append(single_uv)

        # export shape
        if uv_layer:
            ss = {
	            'indices': indices,
                'P': points,
                'N': normals,
                'uv': uvs,
            }
        else:        
            ss = {
	            'indices': indices,
                'P': points,
                'N': normals,
            }

        l.shape('trianglemesh', list(ss.items()))
        
        l.attributeEnd()

        bpy.data.meshes.remove(me)
    

