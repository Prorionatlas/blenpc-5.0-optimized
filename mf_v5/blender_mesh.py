"""Blender-specific mesh generation and bmesh operations for Blender 3.0.1."""

import bpy
import bmesh
from typing import List, Iterable
from .datamodel import WallSegment, Rect
from .slabs import Slab
from .roof import RoofGeometry

def create_wall_mesh(segments: Iterable[WallSegment], name: str = "Walls"):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    for s in segments:
        half_t = s.thickness / 2
        # Calculate direction vector
        dx = s.x2 - s.x1
        dy = s.y2 - s.y1
        length = (dx**2 + dy**2)**0.5
        if length < 1e-4: continue
        
        ux = dx / length
        uy = dy / length
        # Normal vector
        nx = -uy
        ny = ux
        
        # 8 vertices for the wall box
        v = []
        for z in [0, s.height]:
            v.append(bm.verts.new((s.x1 + nx * half_t, s.y1 + ny * half_t, z)))
            v.append(bm.verts.new((s.x2 + nx * half_t, s.y2 + ny * half_t, z)))
            v.append(bm.verts.new((s.x2 - nx * half_t, s.y2 - ny * half_t, z)))
            v.append(bm.verts.new((s.x1 - nx * half_t, s.y1 - ny * half_t, z)))
            
        # 6 faces
        try:
            bm.faces.new(v[0:4]) # bottom
            bm.faces.new(v[4:8]) # top
            bm.faces.new((v[0], v[1], v[5], v[4]))
            bm.faces.new((v[1], v[2], v[6], v[5]))
            bm.faces.new((v[2], v[3], v[7], v[6]))
            bm.faces.new((v[3], v[0], v[4], v[7]))
        except ValueError:
            pass

    bm.to_mesh(mesh)
    bm.free()
    return obj

def create_slab_mesh(slabs: Iterable[Slab], name: str = "Slabs"):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    for s in slabs:
        r = s.rect
        v = []
        for z in [s.z, s.z + s.thickness]:
            v.append(bm.verts.new((r.min_x, r.min_y, z)))
            v.append(bm.verts.new((r.max_x, r.min_y, z)))
            v.append(bm.verts.new((r.max_x, r.max_y, z)))
            v.append(bm.verts.new((r.min_x, r.max_y, z)))
            
        try:
            bm.faces.new(v[0:4])
            bm.faces.new(v[4:8])
            bm.faces.new((v[0], v[1], v[5], v[4]))
            bm.faces.new((v[1], v[2], v[6], v[5]))
            bm.faces.new((v[2], v[3], v[7], v[6]))
            bm.faces.new((v[3], v[0], v[4], v[7]))
        except ValueError:
            pass
        
    bm.to_mesh(mesh)
    bm.free()
    return obj

def create_roof_mesh(roof_geo: RoofGeometry, name: str = "Roof"):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    for face in roof_geo.faces:
        verts = [bm.verts.new(v) for v in face.vertices]
        try:
            bm.faces.new(verts)
        except ValueError:
            pass
            
    bm.to_mesh(mesh)
    bm.free()
    return obj

def final_merge_and_cleanup(objects: List[bpy.types.Object], merge_distance: float = 0.0005):
    if not objects: return None
    
    # Select all objects to join
    bpy.ops.object.select_all(action='DESELECT')
    valid_objs = [o for o in objects if o.type == 'MESH']
    if not valid_objs: return None
    
    for obj in valid_objs:
        obj.select_set(True)
    
    bpy.context.view_layer.objects.active = valid_objs[0]
    bpy.ops.object.join()
    
    merged_obj = bpy.context.active_object
    merged_obj.name = "Building_Final"
    
    # Bmesh cleanup
    bm = bmesh.new()
    bm.from_mesh(merged_obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge_distance)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(merged_obj.data)
    bm.free()
    
    return merged_obj
