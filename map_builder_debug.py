bl_info = {
    "name": "Map Builder Debug (Basic + Trees)",
    "author": "Debug Version",
    "version": (2, 0, 1),
    "blender": (3, 0, 0),
    "location": "View3D > N-panel > OSM",
    "description": "Debug version with basic OSM geometry and simple tree generation",
    "category": "Import-Export",
}

import bpy, bmesh, json, urllib.parse, urllib.request, math, ssl, time, random
from math import cos, radians, sin, pi, sqrt
from pathlib import Path

# -------------------------------------------------------------
# Basic HTTP and geocoding (simplified)
# -------------------------------------------------------------
def make_ua(email):
    return {"User-Agent": "Blender-MapBuilder-Debug/2.0"}

def http_get_json(url, data=None, headers=None, timeout=60):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as f:
        raw = f.read().decode("utf-8", errors="replace")
    return json.loads(raw)

def geocode_address(addr, ua):
    q = urllib.parse.quote(addr)
    url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
    data = http_get_json(url, headers=ua)
    if not data:
        raise RuntimeError("Address not found")
    return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name","")

def overpass_query(lat, lon, radius, ua):
    """Simplified overpass query for basic geometry"""
    query = f"""
    [out:json][timeout:60];
    (
      way["highway"](around:{radius},{lat},{lon});
      way["building"](around:{radius},{lat},{lon});
      way["natural"="water"](around:{radius},{lat},{lon});
      way["landuse"="forest"](around:{radius},{lat},{lon});
      way["leisure"="park"](around:{radius},{lat},{lon});
    );
    out body; >; out skel qt;
    """
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    url = "https://overpass-api.de/api/interpreter"
    return http_get_json(url, data=data, headers=ua, timeout=120)

# -------------------------------------------------------------
# Coordinate conversion
# -------------------------------------------------------------
def meters_per_degree(lat_deg): 
    return 111320.0, 111320.0 * cos(radians(lat_deg))

def deg_to_local_xy(lat, lon, lat0, lon0):
    mlat, mlon = meters_per_degree(lat0)
    return ((lon - lon0) * mlon, (lat - lat0) * mlat)

def split_elements(res):
    nodes = {}; ways = []
    for el in res.get("elements", []):
        if el["type"] == "node":
            nodes[el["id"]] = (el["lat"], el["lon"])
        elif el["type"] == "way": 
            ways.append(el)
    return nodes, ways

# -------------------------------------------------------------
# Basic geometry creation
# -------------------------------------------------------------
def ensure_collection(name):
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col

def new_material(name, color):
    mat = bpy.data.materials.get(name)
    if mat: return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
    return mat

def create_polygon_mesh(name, points_xy, z=0.0):
    """Create a simple polygon mesh"""
    if len(points_xy) < 3:
        return None
    
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    verts = []
    for x, y in points_xy:
        v = bm.verts.new((x, y, z))
        verts.append(v)
    
    if len(verts) >= 3:
        try:
            bm.faces.new(verts)
            bm.to_mesh(mesh)
        except Exception as e:
            print(f"Face creation error: {e}")
    
    bm.free()
    return obj

def create_road_strip(name, points_xy, width=3.0, z=0.0):
    """Create a road strip"""
    if len(points_xy) < 2:
        return None
    
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    
    # Create vertices along both sides of the road
    left_verts = []
    right_verts = []
    
    for i, (x, y) in enumerate(points_xy):
        # Calculate perpendicular direction
        if i == 0 and len(points_xy) > 1:
            dx = points_xy[1][0] - points_xy[0][0]
            dy = points_xy[1][1] - points_xy[0][1]
        elif i == len(points_xy) - 1:
            dx = points_xy[i][0] - points_xy[i-1][0]
            dy = points_xy[i][1] - points_xy[i-1][1]
        else:
            dx = points_xy[i+1][0] - points_xy[i-1][0]
            dy = points_xy[i+1][1] - points_xy[i-1][1]
        
        length = sqrt(dx*dx + dy*dy) or 1.0
        nx, ny = -dy/length, dx/length  # Perpendicular
        
        half_width = width / 2.0
        left_verts.append(bm.verts.new((x + nx * half_width, y + ny * half_width, z)))
        right_verts.append(bm.verts.new((x - nx * half_width, y - ny * half_width, z)))
    
    # Create faces
    for i in range(len(points_xy) - 1):
        try:
            bm.faces.new([left_verts[i], left_verts[i+1], right_verts[i+1], right_verts[i]])
        except:
            pass
    
    bm.to_mesh(mesh)
    bm.free()
    return obj

def create_simple_tree(name, location, tree_type='oak', scale=1.0):
    """Create a very simple tree"""
    try:
        # Create trunk
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.3 * scale,
            depth=8.0 * scale,
            location=(location[0], location[1], location[2] + 4.0 * scale)
        )
        trunk = bpy.context.active_object
        trunk.name = f"{name}_trunk"
        
        # Create crown
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=1,
            radius=4.0 * scale,
            location=(location[0], location[1], location[2] + 10.0 * scale)
        )
        crown = bpy.context.active_object
        crown.name = f"{name}_crown"
        crown.parent = trunk
        
        # Apply materials
        bark_mat = new_material("Bark", (0.4, 0.3, 0.2, 1.0))
        leaf_mat = new_material("Leaves", (0.2, 0.6, 0.1, 1.0))
        
        trunk.data.materials.append(bark_mat)
        crown.data.materials.append(leaf_mat)
        
        return trunk
    except Exception as e:
        print(f"Tree creation error: {e}")
        return None

# -------------------------------------------------------------
# Properties (simplified)
# -------------------------------------------------------------
class OSMProps(bpy.types.PropertyGroup):
    address: bpy.props.StringProperty(
        name="Address", default="Central Park, New York"
    )
    radius_km: bpy.props.FloatProperty(name="Radius (km)", default=0.5, min=0.1, max=5.0)
    clear_scene: bpy.props.BoolProperty(name="Clear Scene", default=True)
    
    # Features
    do_roads: bpy.props.BoolProperty(name="Roads", default=True)
    do_buildings: bpy.props.BoolProperty(name="Buildings", default=True)
    do_water: bpy.props.BoolProperty(name="Water", default=True)
    do_parks: bpy.props.BoolProperty(name="Parks/Forests", default=True)
    
    # Trees
    generate_trees: bpy.props.BoolProperty(name="Generate Trees", default=True)
    tree_density: bpy.props.FloatProperty(name="Tree Density", default=0.3, min=0.0, max=1.0)

# -------------------------------------------------------------
# Main Build Operator (simplified)
# -------------------------------------------------------------
class OSM_OT_BuildDebug(bpy.types.Operator):
    bl_idname = "osm.build_debug"
    bl_label = "Build Debug Scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, ctx):
        p = ctx.scene.osm_builder
        
        print("[DEBUG] Starting build...")
        
        if p.clear_scene:
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete()
            print("[DEBUG] Scene cleared")

        # Geocode address
        try:
            ua = make_ua("")
            lat0, lon0, label = geocode_address(p.address, ua)
            print(f"[DEBUG] Geocoded: {label} at {lat0:.6f}, {lon0:.6f}")
        except Exception as e:
            self.report({'ERROR'}, f"Geocoding failed: {e}")
            return {'CANCELLED'}

        # Get OSM data
        try:
            radius_m = p.radius_km * 1000
            res = overpass_query(lat0, lon0, radius_m, ua)
            print(f"[DEBUG] Overpass returned {len(res.get('elements', []))} elements")
        except Exception as e:
            self.report({'ERROR'}, f"Overpass failed: {e}")
            return {'CANCELLED'}

        nodes, ways = split_elements(res)
        print(f"[DEBUG] Parsed: {len(nodes)} nodes, {len(ways)} ways")

        # Create collections
        col_roads = ensure_collection("DEBUG_Roads")
        col_buildings = ensure_collection("DEBUG_Buildings")
        col_water = ensure_collection("DEBUG_Water")
        col_parks = ensure_collection("DEBUG_Parks")
        col_trees = ensure_collection("DEBUG_Trees")

        # Create materials
        mat_road = new_material("Road", (0.7, 0.7, 0.7, 1.0))
        mat_building = new_material("Building", (0.8, 0.8, 0.8, 1.0))
        mat_water = new_material("Water", (0.3, 0.5, 0.9, 1.0))
        mat_park = new_material("Park", (0.3, 0.7, 0.3, 1.0))

        built = {"roads": 0, "buildings": 0, "water": 0, "parks": 0, "trees": 0}
        park_polygons = []

        # Build geometry
        for way in ways:
            tags = way.get("tags", {})
            way_nodes = [nodes[n] for n in way.get("nodes", []) if n in nodes]
            
            if len(way_nodes) < 2:
                continue
            
            # Convert to local coordinates
            local_points = [deg_to_local_xy(lat, lon, lat0, lon0) for lat, lon in way_nodes]
            
            # Roads
            if p.do_roads and tags.get("highway"):
                road = create_road_strip(f"road_{way['id']}", local_points, width=6.0, z=0.1)
                if road:
                    road.data.materials.append(mat_road)
                    col_roads.objects.link(road)
                    for c in list(road.users_collection):
                        if c != col_roads:
                            try: c.objects.unlink(road)
                            except: pass
                    built["roads"] += 1
            
            # Buildings
            elif p.do_buildings and tags.get("building"):
                if len(local_points) >= 3:
                    # Close polygon if needed
                    if local_points[0] != local_points[-1]:
                        local_points.append(local_points[0])
                    
                    building = create_polygon_mesh(f"building_{way['id']}", local_points, z=0.0)
                    if building:
                        # Add height
                        mod = building.modifiers.new("Solidify", 'SOLIDIFY')
                        mod.thickness = 10.0  # Default building height
                        
                        building.data.materials.append(mat_building)
                        col_buildings.objects.link(building)
                        for c in list(building.users_collection):
                            if c != col_buildings:
                                try: c.objects.unlink(building)
                                except: pass
                        built["buildings"] += 1
            
            # Water
            elif p.do_water and tags.get("natural") == "water":
                if len(local_points) >= 3:
                    if local_points[0] != local_points[-1]:
                        local_points.append(local_points[0])
                    
                    water = create_polygon_mesh(f"water_{way['id']}", local_points, z=0.0)
                    if water:
                        water.data.materials.append(mat_water)
                        col_water.objects.link(water)
                        for c in list(water.users_collection):
                            if c != col_water:
                                try: c.objects.unlink(water)
                                except: pass
                        built["water"] += 1
            
            # Parks and forests
            elif p.do_parks and (tags.get("leisure") == "park" or tags.get("landuse") == "forest"):
                if len(local_points) >= 3:
                    if local_points[0] != local_points[-1]:
                        local_points.append(local_points[0])
                    
                    park = create_polygon_mesh(f"park_{way['id']}", local_points, z=0.01)
                    if park:
                        park.data.materials.append(mat_park)
                        col_parks.objects.link(park)
                        for c in list(park.users_collection):
                            if c != col_parks:
                                try: c.objects.unlink(park)
                                except: pass
                        built["parks"] += 1
                        
                        # Store for tree placement
                        park_polygons.append(local_points)

        # Generate trees in parks/forests
        if p.generate_trees and park_polygons:
            print(f"[DEBUG] Generating trees in {len(park_polygons)} park areas...")
            
            for poly_idx, polygon in enumerate(park_polygons):
                # Find bounding box
                xs = [p[0] for p in polygon[:-1]]
                ys = [p[1] for p in polygon[:-1]]
                minx, maxx = min(xs), max(xs)
                miny, maxy = min(ys), max(ys)
                
                # Simple grid placement
                spacing = 15.0
                grid_x = int((maxx - minx) / spacing) + 1
                grid_y = int((maxy - miny) / spacing) + 1
                
                for i in range(grid_x):
                    for j in range(grid_y):
                        if random.random() > p.tree_density:
                            continue
                        
                        x = minx + (i + random.uniform(0.2, 0.8)) * spacing
                        y = miny + (j + random.uniform(0.2, 0.8)) * spacing
                        
                        # Simple point-in-polygon check
                        inside = False
                        n = len(polygon) - 1
                        p1x, p1y = polygon[0]
                        for k in range(1, n + 1):
                            p2x, p2y = polygon[k % n]
                            if y > min(p1y, p2y):
                                if y <= max(p1y, p2y):
                                    if x <= max(p1x, p2x):
                                        if p1y != p2y:
                                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                                        if p1x == p2x or x <= xinters:
                                            inside = not inside
                            p1x, p1y = p2x, p2y
                        
                        if inside:
                            tree = create_simple_tree(f"tree_{poly_idx}_{i}_{j}", (x, y, 0), scale=random.uniform(0.8, 1.2))
                            if tree:
                                col_trees.objects.link(tree)
                                for c in list(tree.users_collection):
                                    if c != col_trees:
                                        try: c.objects.unlink(tree)
                                        except: pass
                                built["trees"] += 1

        print(f"[DEBUG] Built: {built}")
        msg = f"Debug build complete: roads={built['roads']} buildings={built['buildings']} water={built['water']} parks={built['parks']} trees={built['trees']}"
        self.report({'INFO'}, msg)
        return {'FINISHED'}

# -------------------------------------------------------------
# Simple tree creation
# -------------------------------------------------------------
def create_simple_tree(name, location, tree_type='oak', scale=1.0):
    """Create a simple tree with trunk and crown"""
    try:
        # Create trunk
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.3 * scale,
            depth=8.0 * scale,
            location=(location[0], location[1], location[2] + 4.0 * scale)
        )
        trunk = bpy.context.active_object
        trunk.name = f"{name}_trunk"
        
        # Create crown
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=1,
            radius=4.0 * scale,
            location=(location[0], location[1], location[2] + 10.0 * scale)
        )
        crown = bpy.context.active_object
        crown.name = f"{name}_crown"
        crown.parent = trunk
        
        # Apply simple materials
        bark_mat = new_material("TreeBark", (0.4, 0.3, 0.2, 1.0))
        leaf_mat = new_material("TreeLeaves", (0.2, 0.6, 0.1, 1.0))
        
        trunk.data.materials.append(bark_mat)
        crown.data.materials.append(leaf_mat)
        
        return trunk
    except Exception as e:
        print(f"Tree creation error: {e}")
        return None

# -------------------------------------------------------------
# UI Panel (simplified)
# -------------------------------------------------------------
class OSM_PT_DebugPanel(bpy.types.Panel):
    bl_idname = "OSM_PT_debug_panel"
    bl_label = "OSM Debug Builder"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "OSM"

    def draw(self, ctx):
        layout = self.layout
        props = ctx.scene.osm_builder

        col = layout.column(align=True)
        col.prop(props, "address")
        col.prop(props, "radius_km")
        col.prop(props, "clear_scene")

        layout.separator()
        layout.label(text="Features:")
        col = layout.column(align=True)
        col.prop(props, "do_roads")
        col.prop(props, "do_buildings")
        col.prop(props, "do_water")
        col.prop(props, "do_parks")

        layout.separator()
        layout.label(text="Trees:")
        col = layout.column(align=True)
        col.prop(props, "generate_trees")
        if props.generate_trees:
            col.prop(props, "tree_density")

        layout.separator()
        layout.operator("osm.build_debug", text="Build Debug Scene", icon='WORLD')

# -------------------------------------------------------------
# Test operator
# -------------------------------------------------------------
class OSM_OT_TestDebug(bpy.types.Operator):
    bl_idname = "osm.test_debug"
    bl_label = "Test Debug"
    bl_options = {"INTERNAL"}

    def execute(self, ctx):
        # Create a simple test cube to verify the addon is working
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1))
        cube = bpy.context.active_object
        cube.name = "DebugTest"
        self.report({'INFO'}, "Debug test cube created successfully!")
        return {'FINISHED'}

# -------------------------------------------------------------
# Register
# -------------------------------------------------------------
classes = (OSMProps, OSM_OT_BuildDebug, OSM_OT_TestDebug, OSM_PT_DebugPanel)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.osm_builder = bpy.props.PointerProperty(type=OSMProps)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.osm_builder

if __name__ == "__main__":
    register()