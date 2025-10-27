bl_info = {
    "name": "Map Builder (OSM + Elevation + Trees + Advanced Features)",
    "author": "You + ChatGPT + Enhanced",
    "version": (2, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > N-panel > OSM",
    "description": "Generate OSM geometry with advanced elevation visualization, procedural tree generation, and intelligent placement algorithms. DEM sources: Mapbox Terrain-RGB or AWS Terrarium.",
    "category": "Import-Export",
}

# -------------------------------------------------------------
# Standard libs
# -------------------------------------------------------------
import bpy, bmesh, json, urllib.parse, urllib.request, math, ssl, time, io, sys, os, random
from math import cos, radians, sin, pi, sqrt, atan2
from mathutils import Vector, Matrix, Euler
from pathlib import Path

# -------------------------------------------------------------
# Optional pillow (for PNG decode). If missing, terrain is disabled.
# -------------------------------------------------------------
try:
    from PIL import Image
    PIL_OK = True
except Exception:
    PIL_OK = False

# -------------------------------------------------------------
# UA & HTTP
# -------------------------------------------------------------
def make_ua(email):
    email = (email or "").strip()
    if email and "@" in email:
        return {"User-Agent": f"Blender-MapBuilder/2.0 ({email})"}
    return {"User-Agent": "Blender-MapBuilder/2.0 (set Contact Email in panel)"}

def http_get_bytes(url, data=None, headers=None, timeout=60):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as f:
        return f.read()

def http_get_json(url, data=None, headers=None, timeout=60):
    raw = http_get_bytes(url, data=data, headers=headers, timeout=timeout).decode("utf-8", errors="replace")
    try:
        return json.loads(raw)
    except Exception as e:
        raise RuntimeError(f"Non-JSON from {url[:60]}… ({e})\\n{raw[:240]}")

# -------------------------------------------------------------
# Geocoding (Nominatim)
# -------------------------------------------------------------
def geocode_address(addr, ua):
    q = urllib.parse.quote(addr)
    url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1&addressdetails=0"
    data = http_get_json(url, headers=ua)
    if not data:
        raise RuntimeError("Address not found (Nominatim empty).")
    return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name","")

# -------------------------------------------------------------
# Overpass API (with endpoint failover)
# -------------------------------------------------------------
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

def overpass_query(lat, lon, r, want_dict, ua, timeout=120):
    parts = []
    if want_dict.get("water"):
        parts.append(
            'way["natural"="water"](around:{0},{1},{2});'
            'relation["natural"="water"](around:{0},{1},{2});'
            'way["waterway"="riverbank"](around:{0},{1},{2});'
            'relation["waterway"="riverbank"](around:{0},{1},{2});'
            .format(r, lat, lon)
        )
    if want_dict.get("land"):
        parts.append(
            'way[leisure=park](around:{0},{1},{2});'
            'way[landuse=grass](around:{0},{1},{2});'
            'way[landuse=forest](around:{0},{1},{2});'
            'way[natural=wood](around:{0},{1},{2});'
            'way[leisure=pitch](around:{0},{1},{2});'
            .format(r, lat, lon)
        )
    if want_dict.get("roads"):
        parts.append('way["highway"](around:{0},{1},{2});'.format(r, lat, lon))
    if want_dict.get("rail"):
        parts.append('way[railway](around:{0},{1},{2});'.format(r, lat, lon))
    if want_dict.get("buildings"):
        parts.append(
            'way[building](around:{0},{1},{2});'
            'relation[building](around:{0},{1},{2});'
            .format(r, lat, lon)
        )
    if want_dict.get("xwalks"):
        parts.append('node["highway"="crossing"](around:{0},{1},{2});'.format(r, lat, lon))

    if not parts:
        return {"elements":[]}

    query = "[out:json][timeout:120];(" + "".join(parts) + ");out body; >; out skel qt;"
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")

    last_err = None
    endpoints = ([want_dict.get("overpass_ep")] if want_dict.get("overpass_ep") else []) + OVERPASS_ENDPOINTS
    for ep in endpoints:
        try:
            return http_get_json(ep, data=data, headers=ua, timeout=timeout)
        except Exception as e:
            last_err = e
            time.sleep(1.0)
    raise RuntimeError(f"Overpass failed on all endpoints: {last_err}")

# -------------------------------------------------------------
# Coordinates & small geometry utils
# -------------------------------------------------------------
DEFAULT_LEVEL_HEIGHT_M = 3.2
DEFAULT_BUILDING_HEIGHT = 10.0

ROAD_HALF_WIDTHS = {
    "motorway": 6.0, "trunk": 5.0, "primary": 4.5, "secondary": 3.8,
    "tertiary": 3.2, "unclassified": 2.2, "residential": 2.6,
    "service": 1.8, "living_street": 2.0, "track": 1.5,
    "path": 0.6, "footway": 0.6, "cycleway": 0.8
}
INCLUDE_ROAD_CLASSES = set(ROAD_HALF_WIDTHS.keys())
CASING_SCALE = 0.20

def meters_per_degree(lat_deg): 
    return 111320.0, 111320.0 * cos(radians(lat_deg))

def deg_to_local_xy(lat, lon, lat0, lon0):
    mlat, mlon = meters_per_degree(lat0)
    return ((lon - lon0) * mlon, (lat - lat0) * mlat)

def split_elements(res):
    nodes = {}; ways = []; rels = []; xwalk_nodes = []
    for el in res.get("elements", []):
        if el["type"] == "node":
            nodes[el["id"]] = (el["lat"], el["lon"])
            if "tags" in el and el["tags"].get("highway") == "crossing":
                xwalk_nodes.append(el)
        elif el["type"] == "way": 
            ways.append(el)
        elif el["type"] == "relation": 
            rels.append(el)
    return nodes, ways, rels, xwalk_nodes

def polygon_from_way(way, nodes):
    pts = [nodes[n] for n in way.get("nodes", []) if n in nodes]
    if len(pts) >= 3 and pts[0] != pts[-1]: 
        pts.append(pts[0])
    return pts

def polygons_from_relation(rel, nodes, elements_by_id):
    polys = []
    for m in rel.get("members", []):
        if m.get("type") == "way" and m.get("role") in ("outer",""):
            w = elements_by_id.get(("way", m["ref"]))
            if w:
                pll = polygon_from_way(w, nodes)
                if len(pll) >= 4: 
                    polys.append(pll)
    return polys

def ensure_collection(name):
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col

def new_flat_material(name, rgba=(0.8,0.8,0.8,1), rough=0.6):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = rough
    return m

def make_face_from_xy(name, pts_xy, z, thickness=0.0):
    if len(pts_xy) < 4: return None
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    bm = bmesh.new()
    try:
        vs = [bm.verts.new((x,y,z)) for (x,y) in pts_xy[:-1]]
        bm.faces.new(vs)
        bm.to_mesh(mesh)
    except Exception as e:
        print("[MapBuilder] face error:", e)
        bm.free()
        return None
    bm.free()
    if thickness != 0.0:
        mod = obj.modifiers.new("Solidify", 'SOLIDIFY')
        mod.thickness = thickness
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True); bpy.ops.object.modifier_apply(modifier=mod.name)
        obj.select_set(False)
    return obj

def polyline_normals(pts_xy):
    n = len(pts_xy); norms = []
    for i in range(n):
        a = pts_xy[i-1] if i>0 else pts_xy[i]; b = pts_xy[i+1] if i<n-1 else pts_xy[i]
        dx, dy = b[0]-a[0], b[1]-a[1]; L = math.hypot(dx,dy) or 1.0
        norms.append((-dy/L, dx/L))
    return norms

# -------------------------------------------------------------
# Enhanced Terrain System
# -------------------------------------------------------------
def latlon_to_tile(lat, lon, z):
    n = 2 ** z
    xtile = (lon + 180.0) / 360.0 * n
    ytile = (1.0 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.log(2.0)) * n / 2.0
    return xtile, ytile

def fetch_terrain_rgb_tile_mapbox(z, x, y, token, ua):
    url = f"https://api.mapbox.com/v4/mapbox.terrain-rgb/{z}/{x}/{y}.pngraw?access_token={token}"
    raw = http_get_bytes(url, headers=ua, timeout=60)
    return Image.open(io.BytesIO(raw)).convert("RGB")

def fetch_terrain_rgb_tile_terrarium(z, x, y, ua):
    url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
    raw = http_get_bytes(url, headers=ua, timeout=60)
    return Image.open(io.BytesIO(raw)).convert("RGB")

def decode_terrain_mapbox(img_rgb):
    w, h = img_rgb.size
    px = img_rgb.load()
    arr = [[0.0]*w for _ in range(h)]
    emin, emax = 1e9, -1e9
    for j in range(h):
        for i in range(w):
            r,g,b = px[i,j]
            e = -10000.0 + (r*256*256 + g*256 + b) * 0.1
            arr[j][i] = e
            if e<emin: emin=e
            if e>emax: emax=e
    return arr, (emin, emax)

def decode_terrain_terrarium(img_rgb):
    w, h = img_rgb.size
    px = img_rgb.load()
    arr = [[0.0]*w for _ in range(h)]
    emin, emax = 1e9, -1e9
    for j in range(h):
        for i in range(w):
            r,g,b = px[i,j]
            e = (r * 256 + g + b / 256.0) - 32768.0
            arr[j][i] = e
            if e<emin: emin=e
            if e>emax: emax=e
    return arr, (emin, emax)

def build_terrain_mesh(name, elev_grid, bbox_world, z_offset=0.0, subdivision=0):
    H = len(elev_grid); W = len(elev_grid[0])
    minx, miny, maxx, maxy = bbox_world
    dx = (maxx - minx) / (W-1)
    dy = (maxy - miny) / (H-1)
    mesh = bpy.data.meshes.new(name)
    obj  = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    bm = bmesh.new()
    verts = []
    for j in range(H):
        row = []
        y = miny + j*dy
        for i in range(W):
            x = minx + i*dx
            v = bm.verts.new((x, y, elev_grid[j][i] + z_offset))
            row.append(v)
        verts.append(row)
    for j in range(H-1):
        for i in range(W-1):
            bm.faces.new([verts[j][i], verts[j][i+1], verts[j+1][i+1], verts[j+1][i]])
    
    # Add subdivision if requested
    if subdivision > 0:
        bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=subdivision, use_grid_fill=True)
    
    bm.to_mesh(mesh); bm.free()
    return obj

def sample_elevation_bilinear(elev_grid, bbox_world, x, y):
    H = len(elev_grid); W = len(elev_grid[0])
    minx, miny, maxx, maxy = bbox_world
    if x < minx or x > maxx or y < miny or y > maxy:
        return 0.0
    u = (x - minx) / max(1e-9, (maxx - minx))
    v = (y - miny) / max(1e-9, (maxy - miny))
    fx = u*(W-1); fy = v*(H-1)
    x0 = int(math.floor(fx)); y0 = int(math.floor(fy))
    x1 = min(x0+1, W-1); y1 = min(y0+1, H-1)
    tx = fx - x0; ty = fy - y0
    e00 = elev_grid[y0][x0]; e10 = elev_grid[y0][x1]
    e01 = elev_grid[y1][x0]; e11 = elev_grid[y1][x1]
    e0 = e00*(1-tx) + e10*tx
    e1 = e01*(1-tx) + e11*tx
    return e0*(1-ty) + e1*ty

def calculate_terrain_slope(elev_grid, bbox_world, x, y, sample_distance=1.0):
    """Calculate terrain slope at a given point"""
    z_center = sample_elevation_bilinear(elev_grid, bbox_world, x, y)
    z_east = sample_elevation_bilinear(elev_grid, bbox_world, x + sample_distance, y)
    z_north = sample_elevation_bilinear(elev_grid, bbox_world, x, y + sample_distance)
    
    slope_x = abs(z_east - z_center) / sample_distance
    slope_y = abs(z_north - z_center) / sample_distance
    return sqrt(slope_x**2 + slope_y**2)

def create_elevation_contours(elev_grid, bbox_world, interval=10.0, z_offset=0.0):
    """Create elevation contour lines"""
    H = len(elev_grid); W = len(elev_grid[0])
    minx, miny, maxx, maxy = bbox_world
    
    # Find elevation range and create contour levels
    flat_elevs = [val for row in elev_grid for val in row]
    min_elev, max_elev = min(flat_elevs), max(flat_elevs)
    
    contour_levels = []
    level = (min_elev // interval) * interval
    while level <= max_elev:
        if level >= min_elev:
            contour_levels.append(level)
        level += interval
    
    contour_objects = []
    
    for level in contour_levels:
        # Simple contour extraction (can be improved with marching squares)
        mesh = bpy.data.meshes.new(f"Contour_{level:.0f}m")
        obj = bpy.data.objects.new(f"Contour_{level:.0f}m", mesh)
        bpy.context.scene.collection.objects.link(obj)
        
        bm = bmesh.new()
        
        # Create contour lines by connecting points at similar elevation
        dx = (maxx - minx) / (W-1)
        dy = (maxy - miny) / (H-1)
        
        for j in range(H-1):
            for i in range(W-1):
                # Check if contour passes through this grid cell
                elevs = [elev_grid[j][i], elev_grid[j][i+1], 
                        elev_grid[j+1][i], elev_grid[j+1][i+1]]
                if min(elevs) <= level <= max(elevs):
                    x = minx + i * dx
                    y = miny + j * dy
                    v = bm.verts.new((x, y, level + z_offset))
        
        if bm.verts:
            bm.to_mesh(mesh)
        bm.free()
        contour_objects.append(obj)
    
    return contour_objects

# -------------------------------------------------------------
# Advanced Tree Generation System
# -------------------------------------------------------------
class TreeGenerator:
    def __init__(self):
        self.tree_types = {
            'oak': {
                'trunk_height': (8, 15),
                'trunk_radius': (0.3, 0.6),
                'crown_radius': (4, 8),
                'crown_height': (6, 12),
                'branch_count': (5, 8),
                'leaf_density': 0.8,
                'bark_color': (0.4, 0.3, 0.2, 1.0),
                'leaf_color': (0.2, 0.6, 0.1, 1.0)
            },
            'pine': {
                'trunk_height': (12, 25),
                'trunk_radius': (0.2, 0.4),
                'crown_radius': (2, 4),
                'crown_height': (8, 18),
                'branch_count': (8, 12),
                'leaf_density': 0.9,
                'bark_color': (0.3, 0.25, 0.2, 1.0),
                'leaf_color': (0.1, 0.4, 0.1, 1.0)
            },
            'birch': {
                'trunk_height': (6, 12),
                'trunk_radius': (0.15, 0.25),
                'crown_radius': (3, 6),
                'crown_height': (4, 8),
                'branch_count': (6, 10),
                'leaf_density': 0.7,
                'bark_color': (0.9, 0.9, 0.85, 1.0),
                'leaf_color': (0.3, 0.7, 0.2, 1.0)
            },
            'palm': {
                'trunk_height': (8, 18),
                'trunk_radius': (0.3, 0.5),
                'crown_radius': (3, 6),
                'crown_height': (2, 4),
                'branch_count': (6, 12),
                'leaf_density': 0.6,
                'bark_color': (0.6, 0.5, 0.3, 1.0),
                'leaf_color': (0.1, 0.5, 0.1, 1.0)
            }
        }
    
    def generate_tree(self, tree_type, location, scale_factor=1.0, variation=0.2):
        """Generate a procedural tree of specified type"""
        if tree_type not in self.tree_types:
            tree_type = 'oak'
        
        spec = self.tree_types[tree_type]
        
        # Apply variation
        def vary(min_val, max_val):
            base = random.uniform(min_val, max_val)
            return base * (1.0 + random.uniform(-variation, variation)) * scale_factor
        
        trunk_height = vary(*spec['trunk_height'])
        trunk_radius = vary(*spec['trunk_radius'])
        crown_radius = vary(*spec['crown_radius'])
        crown_height = vary(*spec['crown_height'])
        branch_count = int(vary(*spec['branch_count']))
        
        # Create trunk
        bpy.ops.mesh.primitive_cylinder_add(
            radius=trunk_radius,
            depth=trunk_height,
            location=(location[0], location[1], location[2] + trunk_height/2)
        )
        trunk = bpy.context.active_object
        trunk.name = f"{tree_type}_trunk"
        
        # Create crown based on tree type
        if tree_type == 'pine':
            self._create_coniferous_crown(trunk, location, trunk_height, crown_radius, crown_height, branch_count)
        elif tree_type == 'palm':
            self._create_palm_crown(trunk, location, trunk_height, crown_radius, branch_count)
        else:
            self._create_deciduous_crown(trunk, location, trunk_height, crown_radius, crown_height, branch_count)
        
        # Apply materials
        bark_mat = self._get_or_create_bark_material(tree_type, spec['bark_color'])
        leaf_mat = self._get_or_create_leaf_material(tree_type, spec['leaf_color'])
        
        if trunk.data.materials:
            trunk.data.materials[0] = bark_mat
        else:
            trunk.data.materials.append(bark_mat)
        
        return trunk
    
    def _create_deciduous_crown(self, trunk, location, trunk_height, crown_radius, crown_height, branch_count):
        """Create a deciduous tree crown with branches and leaves"""
        crown_center = (location[0], location[1], location[2] + trunk_height)
        
        # Create main foliage mass
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=2,
            radius=crown_radius,
            location=(crown_center[0], crown_center[1], crown_center[2] + crown_height/3)
        )
        crown = bpy.context.active_object
        crown.name = f"{trunk.name.split('_')[0]}_crown"
        
        # Add some randomness to crown shape
        bpy.context.view_layer.objects.active = crown
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.transform.resize(value=(1.0, 1.0, crown_height/crown_radius/2))
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Create branches
        for i in range(branch_count):
            angle = (2 * pi * i) / branch_count + random.uniform(-0.5, 0.5)
            branch_length = crown_radius * random.uniform(0.6, 0.9)
            branch_height = trunk_height * random.uniform(0.7, 0.95)
            
            branch_end = (
                location[0] + cos(angle) * branch_length,
                location[1] + sin(angle) * branch_length,
                location[2] + branch_height
            )
            
            self._create_branch(location, branch_end, trunk_height * 0.8)
        
        return crown
    
    def _create_coniferous_crown(self, trunk, location, trunk_height, crown_radius, crown_height, branch_count):
        """Create a coniferous tree crown (cone-shaped)"""
        crown_center = (location[0], location[1], location[2] + trunk_height)
        
        # Create cone-shaped crown
        bpy.ops.mesh.primitive_cone_add(
            radius1=crown_radius,
            radius2=0.1,
            depth=crown_height,
            location=(crown_center[0], crown_center[1], crown_center[2] + crown_height/2)
        )
        crown = bpy.context.active_object
        crown.name = f"{trunk.name.split('_')[0]}_crown"
        
        # Create layered branches for more realistic look
        layers = 5
        for layer in range(layers):
            layer_height = trunk_height * (0.4 + 0.5 * layer / layers)
            layer_radius = crown_radius * (1.0 - 0.6 * layer / layers)
            branch_count_layer = max(4, branch_count - layer * 2)
            
            for i in range(branch_count_layer):
                angle = (2 * pi * i) / branch_count_layer
                branch_end = (
                    location[0] + cos(angle) * layer_radius,
                    location[1] + sin(angle) * layer_radius,
                    location[2] + layer_height
                )
                self._create_branch(location, branch_end, layer_height, thickness=0.02)
        
        return crown
    
    def _create_palm_crown(self, trunk, location, trunk_height, crown_radius, branch_count):
        """Create palm fronds"""
        crown_center = (location[0], location[1], location[2] + trunk_height)
        
        for i in range(branch_count):
            angle = (2 * pi * i) / branch_count + random.uniform(-0.3, 0.3)
            frond_length = crown_radius * random.uniform(0.8, 1.2)
            
            # Create frond as elongated ellipse
            bpy.ops.mesh.primitive_cube_add(
                size=0.1,
                location=(
                    crown_center[0] + cos(angle) * frond_length/2,
                    crown_center[1] + sin(angle) * frond_length/2,
                    crown_center[2]
                )
            )
            frond = bpy.context.active_object
            frond.name = f"{trunk.name.split('_')[0]}_frond_{i}"
            frond.scale = (frond_length, 0.3, 0.1)
            frond.rotation_euler = (0, 0, angle)
    
    def _create_branch(self, start, end, base_height, thickness=0.05):
        """Create a branch between two points"""
        direction = Vector(end) - Vector(start)
        length = direction.length
        
        if length < 0.1:
            return
        
        # Create branch cylinder
        bpy.ops.mesh.primitive_cylinder_add(
            radius=thickness,
            depth=length,
            location=((start[0] + end[0])/2, (start[1] + end[1])/2, (start[2] + end[2])/2)
        )
        branch = bpy.context.active_object
        
        # Orient branch
        direction.normalize()
        up = Vector((0, 0, 1))
        if abs(direction.dot(up)) > 0.99:
            up = Vector((1, 0, 0))
        
        right = direction.cross(up)
        up = right.cross(direction)
        
        rotation_matrix = Matrix([right, up, direction]).transposed()
        branch.rotation_euler = rotation_matrix.to_euler()
    
    def _get_or_create_bark_material(self, tree_type, color):
        """Get or create bark material"""
        mat_name = f"MAT_Bark_{tree_type}"
        mat = bpy.data.materials.get(mat_name)
        if not mat:
            mat = new_flat_material(mat_name, color, rough=0.9)
        return mat
    
    def _get_or_create_leaf_material(self, tree_type, color):
        """Get or create leaf material"""
        mat_name = f"MAT_Leaves_{tree_type}"
        mat = bpy.data.materials.get(mat_name)
        if not mat:
            mat = new_flat_material(mat_name, color, rough=0.8)
        return mat

# -------------------------------------------------------------
# Intelligent Tree Placement System
# -------------------------------------------------------------
class TreePlacer:
    def __init__(self, tree_generator):
        self.tree_generator = tree_generator
        self.placement_rules = {
            'forest': {'density': 0.8, 'types': ['oak', 'pine', 'birch'], 'min_spacing': 3.0},
            'park': {'density': 0.3, 'types': ['oak', 'birch'], 'min_spacing': 8.0},
            'residential': {'density': 0.1, 'types': ['oak', 'birch'], 'min_spacing': 12.0},
            'water_edge': {'density': 0.4, 'types': ['birch'], 'min_spacing': 4.0},
            'tropical': {'density': 0.6, 'types': ['palm'], 'min_spacing': 5.0}
        }
    
    def place_trees_in_area(self, area_polygons, area_type, elev_grid, terrain_bbox, z_offset=0.0, slope_limit=0.3):
        """Place trees in specified areas based on land use type"""
        if area_type not in self.placement_rules:
            area_type = 'park'
        
        rules = self.placement_rules[area_type]
        placed_trees = []
        
        for polygon in area_polygons:
            if len(polygon) < 4:
                continue
            
            # Find bounding box of polygon
            xs = [p[0] for p in polygon[:-1]]
            ys = [p[1] for p in polygon[:-1]]
            minx, maxx = min(xs), max(xs)
            miny, maxy = min(ys), max(ys)
            
            # Create placement grid
            spacing = rules['min_spacing']
            grid_x = int((maxx - minx) / spacing) + 1
            grid_y = int((maxy - miny) / spacing) + 1
            
            for i in range(grid_x):
                for j in range(grid_y):
                    # Random placement within grid cell
                    x = minx + (i + random.uniform(0.2, 0.8)) * spacing
                    y = miny + (j + random.uniform(0.2, 0.8)) * spacing
                    
                    # Check if point is inside polygon
                    if not self._point_in_polygon(x, y, polygon):
                        continue
                    
                    # Check density probability
                    if random.random() > rules['density']:
                        continue
                    
                    # Check terrain slope
                    if elev_grid and terrain_bbox:
                        slope = calculate_terrain_slope(elev_grid, terrain_bbox, x, y)
                        if slope > slope_limit:
                            continue
                        
                        z = sample_elevation_bilinear(elev_grid, terrain_bbox, x, y) + z_offset
                    else:
                        z = z_offset
                    
                    # Select tree type
                    tree_type = random.choice(rules['types'])
                    
                    # Generate tree
                    scale = random.uniform(0.7, 1.3)
                    tree = self.tree_generator.generate_tree(tree_type, (x, y, z), scale)
                    placed_trees.append(tree)
        
        return placed_trees
    
    def place_trees_along_roads(self, road_lines, elev_grid, terrain_bbox, z_offset=0.0, spacing=15.0):
        """Place street trees along roads"""
        placed_trees = []
        
        for road in road_lines:
            if road.get('class') not in ['residential', 'tertiary', 'secondary']:
                continue
            
            center_xy = road['center_xy']
            center_z = road.get('center_z', [z_offset] * len(center_xy))
            
            # Place trees on both sides of the road
            norms = polyline_normals(center_xy)
            offset = road['half_width'] + 2.0  # Place trees 2m from road edge
            
            for side in [-1, 1]:  # Both sides
                tree_positions = []
                
                # Sample positions along road
                accumulated_dist = 0.0
                for i in range(len(center_xy) - 1):
                    x1, y1 = center_xy[i]
                    x2, y2 = center_xy[i + 1]
                    z1, z2 = center_z[i], center_z[i + 1]
                    nx, ny = norms[i]
                    
                    segment_length = sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    
                    while accumulated_dist < segment_length:
                        t = accumulated_dist / segment_length
                        x = x1 + t * (x2 - x1) + side * offset * nx
                        y = y1 + t * (y2 - y1) + side * offset * ny
                        z = z1 + t * (z2 - z1)
                        
                        tree_positions.append((x, y, z))
                        accumulated_dist += spacing
                    
                    accumulated_dist -= segment_length
                
                # Place trees
                for pos in tree_positions:
                    tree_type = random.choice(['oak', 'birch'])
                    scale = random.uniform(0.8, 1.2)
                    tree = self.tree_generator.generate_tree(tree_type, pos, scale)
                    placed_trees.append(tree)
        
        return placed_trees
    
    def _point_in_polygon(self, x, y, polygon):
        """Check if point is inside polygon using ray casting"""
        n = len(polygon) - 1  # Exclude last point if it's duplicate of first
        inside = False
        
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        
        return inside

# -------------------------------------------------------------
# Enhanced mesh builders that follow terrain
# -------------------------------------------------------------
def make_strip_follow_terrain(name, center_xy, center_z, half_width, z_extra=0.0):
    if len(center_xy) < 2: return None
    norms = polyline_normals(center_xy)
    left  = [(p[0]+n[0]*half_width, p[1]+n[1]*half_width) for p,n in zip(center_xy, norms)]
    right = [(p[0]-n[0]*half_width, p[1]-n[1]*half_width) for p,n in zip(center_xy, norms)]
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    bm = bmesh.new()
    vL = [bm.verts.new((x, y, cz + z_extra)) for (x,y), cz in zip(left, center_z)]
    vR = [bm.verts.new((x, y, cz + z_extra)) for (x,y), cz in zip(right, center_z)]
    bm.verts.ensure_lookup_table()
    for i in range(len(center_xy)-1):
        try:
            bm.faces.new([vL[i], vL[i+1], vR[i+1], vR[i]])
        except: 
            pass
    bm.normal_update(); bm.to_mesh(mesh); bm.free()
    return obj

def add_bridge_piers(points_xy, deck_zs=None, base_zs=None, pier_radius=0.35):
    made = []
    for idx, (x,y) in enumerate(points_xy):
        base_z = (base_zs[idx] if base_zs else 0.0)
        deck_z = (deck_zs[idx] if deck_zs else base_z + 3.0)
        h = max(1.0, deck_z - base_z)
        bpy.ops.mesh.primitive_cylinder_add(radius=pier_radius, depth=h, location=(x, y, base_z + h/2))
        obj = bpy.context.active_object
        mat = bpy.data.materials.get("MAT_Road_Casing") or new_flat_material("MAT_Pier", (0.55,0.55,0.56,1), 0.8)
        if obj.data.materials: obj.data.materials[0] = mat
        else: obj.data.materials.append(mat)
        made.append(obj)
    return made

def sample_polyline_every(center_xy, step_m=12.0):
    pts = []
    if len(center_xy) < 2: return pts
    acc = 0.0
    for i in range(len(center_xy)-1):
        x1,y1 = center_xy[i]; x2,y2 = center_xy[i+1]
        seg = math.hypot(x2-x1, y2-y1)
        t = 0.0
        while acc + (seg - t) >= step_m:
            need = step_m - acc
            tt = (t + need) / seg
            px = x1 + (x2-x1)*tt; py = y1 + (y2-y1)*tt
            pts.append((px,py))
            t += need
            acc = 0.0
        acc += seg - t
    return pts

# -------------------------------------------------------------
# Height parsing
# -------------------------------------------------------------
def parse_height(tags):
    h = None
    if "height" in tags:
        s = "".join(c for c in tags["height"] if (c.isdigit() or c=='.'))
        if s:
            try: h = float(s)
            except: pass
    if not h and "building:levels" in tags:
        try: h = float(tags["building:levels"]) * DEFAULT_LEVEL_HEIGHT_M
        except: h = None
    return h if h else DEFAULT_BUILDING_HEIGHT

# -------------------------------------------------------------
# Crosswalk helper (aligned to nearest road segment)
# -------------------------------------------------------------
def nearest_segment_and_tangent(point_xy, polyline_xy):
    px, py = point_xy
    best_i = 0; best_d2 = 1e18; best_tvec = (1.0,0.0)
    for i in range(len(polyline_xy)-1):
        x1,y1 = polyline_xy[i]; x2,y2 = polyline_xy[i+1]
        vx, vy = x2-x1, y2-y1; wx, wy = px-x1, py-y1
        L2 = vx*vx + vy*vy or 1e-9
        t = max(0.0, min(1.0, (wx*vx + wy*vy)/L2))
        projx = x1 + t*vx; projy = y1 + t*vy
        dx, dy = px - projx, py - projy; d2 = dx*dx + dy*dy
        if d2 < best_d2:
            best_d2 = d2; best_i = i
            L = math.sqrt(L2); best_tvec = (vx/L, vy/L)
    return best_i, best_tvec

def build_crosswalk_stripes(name_prefix, center_xy, tvec, road_width, z,
                            depth=3.0, stripe=0.5, gap=0.5, edge_margin=0.06):
    tx, ty = tvec
    nx, ny = -ty, tx
    full_across = road_width * (1.0 - 2.0*edge_margin)
    step = stripe + gap
    n = max(1, int(depth // step))
    start_offset = - (n * step - gap) / 2.0
    stripes = []
    for k in range(n):
        along = start_offset + k*step + stripe/2.0
        cx = center_xy[0] + tx*along; cy = center_xy[1] + ty*along
        half_across = full_across/2.0; half_along = stripe/2.0
        corners = [(+half_along, +half_across), (-half_along, +half_across),
                   (-half_along, -half_across), (+half_along, -half_across)]
        pts = []
        for a, c in corners:
            x = cx + tx*a + nx*c; y = cy + ty*a + ny*c
            pts.append((x, y))
        mesh = bpy.data.meshes.new(f"{name_prefix}_{k}")
        obj = bpy.data.objects.new(f"{name_prefix}_{k}", mesh)
        bpy.context.scene.collection.objects.link(obj)
        bm = bmesh.new()
        v = [bm.verts.new((pts[i][0], pts[i][1], z)) for i in range(4)]
        bm.faces.new(v); bm.to_mesh(mesh); bm.free()
        stripes.append(obj)
    return stripes

# -------------------------------------------------------------
# Enhanced Properties
# -------------------------------------------------------------
class OSMProps(bpy.types.PropertyGroup):
    contact_email: bpy.props.StringProperty(name="Contact Email", default="")
    overpass_ep: bpy.props.StringProperty(name="Overpass Endpoint (optional)", default="")

    address: bpy.props.StringProperty(
        name="Address", default="276 West Main St, Cheshire, Connecticut"
    )
    radius_value: bpy.props.FloatProperty(name="Radius", default=1.0, min=0.05, soft_max=50.0)
    radius_unit: bpy.props.EnumProperty(
        name="Units", items=[('MILES',"Miles","Miles"), ('METERS',"Meters","Meters")], default='MILES'
    )
    clear_scene: bpy.props.BoolProperty(name="Clear Scene First", default=False)

    # Layers
    do_roads: bpy.props.BoolProperty(name="Roads (planes + casing)", default=True)
    do_crosswalks: bpy.props.BoolProperty(name="Crosswalks", default=False)
    do_buildings: bpy.props.BoolProperty(name="Buildings", default=True)
    do_water: bpy.props.BoolProperty(name="Water", default=True)
    do_landuse: bpy.props.BoolProperty(name="Landuse/Leisure", default=True)
    do_rail: bpy.props.BoolProperty(name="Railways", default=False)

    # Crosswalk tuning
    xwalk_depth: bpy.props.FloatProperty(name="Xwalk Depth (m)", default=3.0, min=0.5, max=8.0)
    xwalk_stripe: bpy.props.FloatProperty(name="Stripe (m)", default=0.5, min=0.1, max=2.0)
    xwalk_gap: bpy.props.FloatProperty(name="Gap (m)", default=0.5, min=0.1, max=2.0)
    xwalk_margin: bpy.props.FloatProperty(name="Edge Margin", default=0.06, min=0.0, max=0.2)

    # Scene
    ground_size: bpy.props.FloatProperty(name="Ground Plane (m)", default=0.0, min=0.0, soft_max=5000.0)

    # Enhanced Terrain
    use_terrain: bpy.props.BoolProperty(name="Use Terrain", default=True)
    dem_source: bpy.props.EnumProperty(
        name="DEM Source",
        items=[('MAPBOX',"Mapbox Terrain-RGB",""), ('TERRARIUM',"AWS Terrarium","")],
        default='TERRARIUM'
    )
    mapbox_token: bpy.props.StringProperty(name="Mapbox Token", default="", subtype='PASSWORD')
    terrain_res: bpy.props.IntProperty(name="Terrain Resolution", default=256, min=64, max=1024)
    terrain_size_mode: bpy.props.EnumProperty(
        name="Terrain Size", items=[('AUTO',"Auto (2×Radius)",""), ('CUSTOM',"Custom Square","")], default='AUTO'
    )
    terrain_size_m: bpy.props.FloatProperty(name="Custom Size (m)", default=4000.0, min=500.0, soft_max=20000.0)
    terrain_z_offset: bpy.props.FloatProperty(name="Terrain Z Offset", default=0.0, soft_min=-50.0, soft_max=50.0)
    terrain_subdivision: bpy.props.IntProperty(name="Terrain Subdivision", default=0, min=0, max=3)
    
    # Elevation Features
    show_contours: bpy.props.BoolProperty(name="Show Elevation Contours", default=False)
    contour_interval: bpy.props.FloatProperty(name="Contour Interval (m)", default=10.0, min=1.0, max=100.0)
    terrain_material_mode: bpy.props.EnumProperty(
        name="Terrain Material",
        items=[('FLAT',"Flat Color",""), ('ELEVATION',"Elevation-based",""), ('SLOPE',"Slope-based","")],
        default='FLAT'
    )

    # Tree Generation
    generate_trees: bpy.props.BoolProperty(name="Generate Trees", default=False)
    tree_density: bpy.props.FloatProperty(name="Tree Density", default=0.5, min=0.0, max=1.0)
    tree_scale_variation: bpy.props.FloatProperty(name="Tree Scale Variation", default=0.3, min=0.0, max=1.0)
    tree_slope_limit: bpy.props.FloatProperty(name="Max Slope for Trees", default=0.3, min=0.0, max=1.0)
    
    # Tree Placement Options
    trees_in_forests: bpy.props.BoolProperty(name="Trees in Forests", default=True)
    trees_in_parks: bpy.props.BoolProperty(name="Trees in Parks", default=True)
    street_trees: bpy.props.BoolProperty(name="Street Trees", default=False)
    street_tree_spacing: bpy.props.FloatProperty(name="Street Tree Spacing (m)", default=15.0, min=5.0, max=50.0)

    # Bridges
    bridge_clearance: bpy.props.FloatProperty(name="Bridge Deck Offset (m)", default=1.5, min=0.0, soft_max=8.0)
    tunnel_offset: bpy.props.FloatProperty(name="Tunnel Offset (m)", default=-0.5, soft_min=-10.0, soft_max=0.0)
    add_piers: bpy.props.BoolProperty(name="Add Bridge Piers", default=False)
    pier_spacing: bpy.props.FloatProperty(name="Pier Spacing (m)", default=14.0, min=4.0, soft_max=50.0)
    pier_radius: bpy.props.FloatProperty(name="Pier Radius (m)", default=0.35, min=0.1, soft_max=2.0)

    # Export
    export_fbx: bpy.props.BoolProperty(name="Export FBX", default=False)
    export_obj: bpy.props.BoolProperty(name="Export OBJ", default=False)
    output_dir: bpy.props.StringProperty(name="Output Folder", subtype='DIR_PATH', default="//")
    file_basename: bpy.props.StringProperty(name="File Basename", default="osm_scene")

    # Debug
    verbose: bpy.props.BoolProperty(name="Verbose Console Log", default=True)

# -------------------------------------------------------------
# Enhanced Operators
# -------------------------------------------------------------
class OSM_OT_Test(bpy.types.Operator):
    bl_idname = "osm.test_connection"
    bl_label = "Test Connection"
    bl_options = {"INTERNAL"}

    def execute(self, ctx):
        p = ctx.scene.osm_builder
        ua = make_ua(p.contact_email)
        try:
            lat, lon, label = geocode_address(p.address, ua)
        except Exception as e:
            self.report({'ERROR'}, f"Geocode failed: {e}")
            return {'CANCELLED'}
        want = {"roads": True, "overpass_ep": p.overpass_ep.strip() or None}
        try:
            res = overpass_query(lat, lon, 50.0, want, ua)
        except Exception as e:
            self.report({'ERROR'}, f"Overpass failed: {e}")
            return {'CANCELLED'}
        nodes, ways, rels, _ = split_elements(res)
        self.report({'INFO'}, f"OK: {label} | nodes={len(nodes)} ways={len(ways)}")
        if p.verbose:
            print("[MapBuilder Test] Label:", label)
            print("[MapBuilder Test] Nodes:", len(nodes), "Ways:", len(ways), "Rels:", len(rels))
        return {'FINISHED'}

class OSM_OT_TestTerrain(bpy.types.Operator):
    bl_idname = "osm.test_terrain"
    bl_label = "Test Terrain Fetch"
    bl_options = {"INTERNAL"}

    def execute(self, ctx):
        p = ctx.scene.osm_builder
        if not p.use_terrain:
            self.report({'WARNING'}, "Use Terrain is off.")
            return {'CANCELLED'}
        if not PIL_OK:
            self.report({'ERROR'}, "Pillow not available. Install 'Pillow' to enable terrain.")
            return {'CANCELLED'}

        ua = make_ua(p.contact_email)
        try:
            lat0, lon0, _ = geocode_address(p.address, ua)
        except Exception as e:
            self.report({'ERROR'}, f"Geocode failed: {e}")
            return {'CANCELLED'}

        radius_m = p.radius_value * (1609.34 if p.radius_unit == 'MILES' else 1.0)
        size_m = (2.0*radius_m) if p.terrain_size_mode == 'AUTO' else p.terrain_size_m
        half = size_m/2.0
        minx, miny, maxx, maxy = -half, -half, half, half
        mlat, mlon = meters_per_degree(lat0)
        def xy_to_latlon(x, y):
            lat = y/mlat + lat0
            lon = x/mlon + lon0
            return lat, lon
        ZOOM = 14
        lat_ul, lon_ul = xy_to_latlon(minx, maxy)
        lat_lr, lon_lr = xy_to_latlon(maxx, miny)
        x0f,y0f = latlon_to_tile(lat_ul, lon_ul, ZOOM)
        x1f,y1f = latlon_to_tile(lat_lr, lon_lr, ZOOM)
        x0,x1 = int(math.floor(min(x0f,x1f))), int(math.floor(max(x0f,x1f)))
        y0,y1 = int(math.floor(min(y0f,y1f))), int(math.floor(max(y0f,y1f)))

        try:
            if p.dem_source == 'MAPBOX':
                if not p.mapbox_token.strip():
                    self.report({'ERROR'}, "Mapbox token missing.")
                    return {'CANCELLED'}
                img = fetch_terrain_rgb_tile_mapbox(ZOOM, x0, y0, p.mapbox_token.strip(), ua)
                _, (emin, emax) = decode_terrain_mapbox(img)
            else:
                img = fetch_terrain_rgb_tile_terrarium(ZOOM, x0, y0, ua)
                _, (emin, emax) = decode_terrain_terrarium(img)
        except Exception as e:
            self.report({'ERROR'}, f"Terrain fetch failed: {e}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Terrain OK at z{ZOOM}. Elevation sample range: {emin:.1f} to {emax:.1f} m")
        if p.verbose:
            print(f"[MapBuilder Terrain] z{ZOOM} tile ({x0},{y0}) elevation ~ {emin:.1f}..{emax:.1f} m")
        return {'FINISHED'}

class OSM_OT_Build(bpy.types.Operator):
    bl_idname = "osm.build_from_address"
    bl_label = "Build Enhanced OSM Scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, ctx):
        p = ctx.scene.osm_builder
        ua = make_ua(p.contact_email)

        # Update todo status
        if hasattr(ctx.scene, 'osm_todos'):
            todo_write(merge=True, todos=[{"id": "elevation_enhancements", "status": "completed"}])

        radius_m = p.radius_value * (1609.34 if p.radius_unit == 'MILES' else 1.0)
        if radius_m < 20: radius_m = 20

        if p.clear_scene:
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete()

        try:
            lat0, lon0, label = geocode_address(p.address, ua)
        except Exception as e:
            self.report({'ERROR'}, f"Geocoding failed: {e}")
            return {'CANCELLED'}

        want = {
            "water": p.do_water,
            "land": p.do_landuse,
            "roads": p.do_roads,
            "rail": p.do_rail,
            "buildings": p.do_buildings,
            "xwalks": p.do_crosswalks,
            "overpass_ep": p.overpass_ep.strip() or None
        }

        try:
            res = overpass_query(lat0, lon0, radius_m, want, ua)
        except Exception as e:
            self.report({'ERROR'}, f"Overpass failed: {e}")
            return {'CANCELLED'}

        nodes, ways, rels, xwalk_nodes = split_elements(res)
        elements_by_id = {("way", w["id"]): w for w in ways}
        elements_by_id.update({("relation", r["id"]): r for r in rels})

        # Enhanced collections
        col_water = ensure_collection("OSM_Water")
        col_land  = ensure_collection("OSM_Landuse")
        col_roads = ensure_collection("OSM_Roads")
        col_rails = ensure_collection("OSM_Railways")
        col_bldg  = ensure_collection("OSM_Buildings")
        col_xwalk = ensure_collection("OSM_Crosswalks")
        col_trees = ensure_collection("OSM_Trees")
        col_terrain = ensure_collection("OSM_Terrain")

        # Enhanced materials
        mat_water = new_flat_material("MAT_Water", (0.63,0.78,0.95,1), 0.02)
        mat_land  = new_flat_material("MAT_Land", (0.6,0.8,0.6,1), 0.9)
        mat_road_fill   = new_flat_material("MAT_Road_Fill", (0.95,0.95,0.95,1), 0.6)
        mat_road_casing = new_flat_material("MAT_Road_Casing", (0.73,0.73,0.73,1), 0.8)
        mat_rail  = new_flat_material("MAT_Rail", (0.48,0.48,0.48,1), 0.7)
        mat_bldg  = new_flat_material("MAT_Building", (0.85,0.85,0.83,1), 0.7)
        mat_xwalk = new_flat_material("MAT_Xwalk", (0.97,0.97,0.97,1), 0.3)

        if p.ground_size > 0:
            bpy.ops.mesh.primitive_plane_add(size=p.ground_size, location=(0,0,-0.001))
            bpy.context.active_object.name = "Ground"

        # ----- Enhanced Terrain System -----
        terrain_obj = None
        elev_grid = None
        terrain_bbox = None
        if p.use_terrain:
            if not PIL_OK:
                self.report({'WARNING'}, "Pillow not available: terrain disabled. Install 'Pillow' to enable.")
            else:
                try:
                    size_m = (2.0*radius_m) if p.terrain_size_mode == 'AUTO' else p.terrain_size_m
                    half = size_m/2.0
                    minx, miny, maxx, maxy = -half, -half, half, half
                    mlat, mlon = meters_per_degree(lat0)
                    def xy_to_latlon(x, y):
                        lat = y/mlat + lat0
                        lon = x/mlon + lon0
                        return lat, lon
                    ZOOM = 14
                    lat_ul, lon_ul = xy_to_latlon(minx, maxy)
                    lat_lr, lon_lr = xy_to_latlon(maxx, miny)
                    x0f,y0f = latlon_to_tile(lat_ul, lon_ul, ZOOM)
                    x1f,y1f = latlon_to_tile(lat_lr, lon_lr, ZOOM)
                    x0,x1 = int(math.floor(min(x0f,x1f))), int(math.floor(max(x0f,x1f)))
                    y0,y1 = int(math.floor(min(y0f,y1f))), int(math.floor(max(y0f,y1f)))

                    tiles = []
                    for ty in range(y0, y1+1):
                        row = []
                        for tx in range(x0, x1+1):
                            if p.dem_source == 'MAPBOX':
                                if not p.mapbox_token.strip():
                                    raise RuntimeError("Mapbox token missing (DEM source is Mapbox).")
                                img = fetch_terrain_rgb_tile_mapbox(ZOOM, tx, ty, p.mapbox_token.strip(), ua)
                            else:
                                img = fetch_terrain_rgb_tile_terrarium(ZOOM, tx, ty, ua)
                            row.append(img)
                        tiles.append(row)

                    tw, th = tiles[0][0].size
                    big = Image.new("RGB", ((x1-x0+1)*tw, (y1-y0+1)*th))
                    for j,row in enumerate(tiles):
                        for i,img in enumerate(row):
                            big.paste(img, (i*tw, j*th))

                    big_res = big.resize((p.terrain_res, p.terrain_res), Image.BILINEAR)
                    if p.dem_source == 'MAPBOX':
                        elev_grid, rng = decode_terrain_mapbox(big_res)
                    else:
                        elev_grid, rng = decode_terrain_terrarium(big_res)
                    terrain_bbox = (minx, miny, maxx, maxy)

                    terrain_obj = build_terrain_mesh("Terrain", elev_grid, terrain_bbox, 
                                                   z_offset=p.terrain_z_offset, 
                                                   subdivision=p.terrain_subdivision)
                    
                    # Enhanced terrain materials
                    if p.terrain_material_mode == 'ELEVATION':
                        mat_terrain = self.create_elevation_material(rng)
                    elif p.terrain_material_mode == 'SLOPE':
                        mat_terrain = self.create_slope_material()
                    else:
                        mat_terrain = new_flat_material("MAT_Terrain", (0.32,0.34,0.28,1), 0.9)
                    
                    if terrain_obj.data.materials: 
                        terrain_obj.data.materials[0] = mat_terrain
                    else: 
                        terrain_obj.data.materials.append(mat_terrain)
                    
                    # Move to terrain collection
                    for c in list(terrain_obj.users_collection):
                        try: c.objects.unlink(terrain_obj)
                        except: pass
                    col_terrain.objects.link(terrain_obj)
                    
                    # Create elevation contours if requested
                    if p.show_contours:
                        contour_objects = create_elevation_contours(
                            elev_grid, terrain_bbox, 
                            interval=p.contour_interval, 
                            z_offset=p.terrain_z_offset + 0.1
                        )
                        contour_mat = new_flat_material("MAT_Contours", (0.8, 0.6, 0.4, 1), 0.5)
                        for contour in contour_objects:
                            if contour.data.materials:
                                contour.data.materials[0] = contour_mat
                            else:
                                contour.data.materials.append(contour_mat)
                            for c in list(contour.users_collection):
                                try: c.objects.unlink(contour)
                                except: pass
                            col_terrain.objects.link(contour)
                    
                    if p.verbose:
                        print(f"[MapBuilder] Enhanced terrain: {len(elev_grid)}x{len(elev_grid[0])}, elev ~ {rng[0]:.1f}..{rng[1]:.1f} m")
                except Exception as e:
                    self.report({'WARNING'}, f"Terrain failed: {e}")

        def sampleZ(x, y):
            if elev_grid and terrain_bbox:
                return sample_elevation_bilinear(elev_grid, terrain_bbox, x, y) + p.terrain_z_offset
            return 0.0

        built = {"water":0,"land":0,"roads":0,"rail":0,"bldg":0,"xwalk":0,"trees":0}
        land_polygons = {"forest": [], "park": []}

        # ----- WATER (average drape) -----
        if p.do_water:
            for w in ways:
                t = w.get("tags",{})
                if t.get("natural")=="water" or t.get("waterway")=="riverbank":
                    pll = polygon_from_way(w, nodes)
                    if len(pll)>=4:
                        xy = [deg_to_local_xy(lat,lon,lat0,lon0) for (lat,lon) in pll]
                        avgz = sum(sampleZ(x,y) for (x,y) in xy[:-1]) / max(1, len(xy)-1)
                        obj = make_face_from_xy(f"water_{w['id']}", xy, avgz, 0.0)
                        if obj:
                            if obj.data.materials: obj.data.materials[0] = mat_water
                            else: obj.data.materials.append(mat_water)
                            for c in list(obj.users_collection):
                                try: c.objects.unlink(obj)
                                except: pass
                            col_water.objects.link(obj); built["water"] += 1

            for r in rels:
                t = r.get("tags",{})
                if t.get("natural")=="water" or t.get("waterway")=="riverbank":
                    for i, pll in enumerate(polygons_from_relation(r, nodes, elements_by_id)):
                        xy = [deg_to_local_xy(lat,lon,lat0,lon0) for (lat,lon) in pll]
                        avgz = sum(sampleZ(x,y) for (x,y) in xy[:-1]) / max(1, len(xy)-1)
                        obj = make_face_from_xy(f"water_rel_{r['id']}_{i}", xy, avgz, 0.0)
                        if obj:
                            if obj.data.materials: obj.data.materials[0] = mat_water
                            else: obj.data.materials.append(mat_water)
                            for c in list(obj.users_collection):
                                try: c.objects.unlink(obj)
                                except: pass
                            col_water.objects.link(obj); built["water"] += 1

        # ----- LANDUSE (collect for tree placement) -----
        if p.do_landuse:
            for w in ways:
                t = w.get("tags",{})
                land_type = None
                if t.get("landuse") in ("forest",) or t.get("natural") in ("wood",):
                    land_type = "forest"
                elif t.get("leisure")=="park" or t.get("landuse") in ("grass",) or t.get("leisure")=="pitch":
                    land_type = "park"
                
                if land_type:
                    pll = polygon_from_way(w, nodes)
                    if len(pll)>=4:
                        xy = [deg_to_local_xy(lat,lon,lat0,lon0) for (lat,lon) in pll]
                        avgz = sum(sampleZ(x,y) for (x,y) in xy[:-1]) / max(1, len(xy)-1)
                        obj = make_face_from_xy(f"land_{w['id']}", xy, avgz+0.001, 0.0)
                        if obj:
                            if obj.data.materials: obj.data.materials[0] = mat_land
                            else: obj.data.materials.append(mat_land)
                            for c in list(obj.users_collection):
                                try: c.objects.unlink(obj)
                                except: pass
                            col_land.objects.link(obj); built["land"] += 1
                        
                        # Store for tree placement
                        land_polygons[land_type].append(xy)

        # ----- ROADS (elevated) -----
        road_lines = []
        if p.do_roads:
            for w in ways:
                t = w.get("tags",{})
                hw = t.get("highway")
                if not hw or hw not in INCLUDE_ROAD_CLASSES: continue
                poly_ll = [nodes[n] for n in w.get("nodes", []) if n in nodes]
                if len(poly_ll)<2: continue
                center_xy = [deg_to_local_xy(lat,lon,lat0,lon0) for (lat,lon) in poly_ll]
                center_z  = [sampleZ(x,y) for (x,y) in center_xy]
                half = ROAD_HALF_WIDTHS.get(hw, 1.8)

                z_extra = 0.0
                if t.get("bridge") in ("yes","true","1"): z_extra += p.bridge_clearance
                if t.get("tunnel") in ("yes","true","1"): z_extra += p.tunnel_offset
                if "layer" in t:
                    try: z_extra += float(t["layer"]) * 0.25
                    except: pass

                casing = make_strip_follow_terrain(f"rcase_{w['id']}", center_xy, center_z, half*(1.0+CASING_SCALE), z_extra-0.001)
                if casing:
                    if casing.data.materials: casing.data.materials[0] = mat_road_casing
                    else: casing.data.materials.append(mat_road_casing)
                    for c in list(casing.users_collection):
                        try: c.objects.unlink(casing)
                        except: pass
                    col_roads.objects.link(casing)

                fill = make_strip_follow_terrain(f"road_{w['id']}", center_xy, center_z, half, z_extra)
                if fill:
                    if fill.data.materials: fill.data.materials[0] = mat_road_fill
                    else: fill.data.materials.append(mat_road_fill)
                    for c in list(fill.users_collection):
                        try: c.objects.unlink(fill)
                        except: pass
                    col_roads.objects.link(fill)
                    built["roads"] += 1

                    road_lines.append({
                        "id": w["id"],
                        "class": hw,
                        "center_xy": center_xy,
                        "center_z": center_z,
                        "half_width": half,
                        "z_extra": z_extra,
                        "is_bridge": t.get("bridge") in ("yes","true","1")
                    })

        # ----- RAIL (elevated) -----
        if p.do_rail:
            for w in ways:
                t = w.get("tags",{})
                rw = t.get("railway")
                if not rw: continue
                poly_ll = [nodes[n] for n in w.get("nodes", []) if n in nodes]
                if len(poly_ll)<2: continue
                center_xy = [deg_to_local_xy(lat,lon,lat0,lon0) for (lat,lon) in poly_ll]
                center_z  = [sampleZ(x,y) for (x,y) in center_xy]
                half = {"rail":1.4,"light_rail":1.2,"subway":1.2,"tram":0.9}.get(rw,1.0)
                z_extra = 0.0
                if t.get("bridge") in ("yes","true","1"): z_extra += p.bridge_clearance
                if t.get("tunnel") in ("yes","true","1"): z_extra += p.tunnel_offset
                rail = make_strip_follow_terrain(f"rail_{w['id']}", center_xy, center_z, half, z_extra)
                if rail:
                    if rail.data.materials: rail.data.materials[0] = mat_rail
                    else: rail.data.materials.append(mat_rail)
                    for c in list(rail.users_collection):
                        try: c.objects.unlink(rail)
                        except: pass
                    col_rails.objects.link(rail); built["rail"] += 1

        # ----- BUILDINGS (base at average terrain Z) -----
        if p.do_buildings:
            def avgZ(poly_xy):
                if not poly_xy: return 0.0
                return sum(sampleZ(x,y) for (x,y) in poly_xy[:-1]) / max(1, len(poly_xy)-1)
            for w in ways:
                t = w.get("tags",{})
                if "building" in t:
                    pll = polygon_from_way(w, nodes)
                    if len(pll)>=4:
                        xy = [deg_to_local_xy(lat,lon,lat0,lon0) for (lat,lon) in pll]
                        basez = avgZ(xy)
                        h = parse_height(t)
                        b = make_face_from_xy(f"bldg_{w['id']}", xy, basez, thickness=h)
                        if b:
                            if b.data.materials: b.data.materials[0] = mat_bldg
                            else: b.data.materials.append(mat_bldg)
                            for c in list(b.users_collection):
                                try: c.objects.unlink(b)
                                except: pass
                            col_bldg.objects.link(b); built["bldg"] += 1
            for r in rels:
                t = r.get("tags",{})
                if "building" in t:
                    pll_list = polygons_from_relation(r, nodes, elements_by_id)
                    for i, pll in enumerate(pll_list):
                        xy = [deg_to_local_xy(lat,lon,lat0,lon0) for (lat,lon) in pll]
                        basez = sum(sampleZ(x,y) for (x,y) in xy[:-1]) / max(1, len(xy)-1)
                        h = parse_height(t)
                        b = make_face_from_xy(f"bldg_rel_{r['id']}_{i}", xy, basez, thickness=h)
                        if b:
                            if b.data.materials: b.data.materials[0] = mat_bldg
                            else: b.data.materials.append(mat_bldg)
                            for c in list(b.users_collection):
                                try: c.objects.unlink(b)
                                except: pass
                            col_bldg.objects.link(b); built["bldg"] += 1

        # ----- CROSSWALKS -----
        if p.do_crosswalks and road_lines and xwalk_nodes:
            placed = 0
            for n in xwalk_nodes:
                lat, lon = n["lat"], n["lon"]
                pxy = deg_to_local_xy(lat, lon, lat0, lon0)
                best = None; best_d2 = 1e18; best_tvec = (1.0,0.0); best_width = 6.0; best_zextra = 0.0
                for rl in road_lines:
                    poly = rl["center_xy"]
                    if len(poly)<2: continue
                    i, tvec = nearest_segment_and_tangent(pxy, poly)
                    x1,y1 = poly[i]; x2,y2 = poly[i+1]
                    vx, vy = x2-x1, y2-y1; wx, wy = pxy[0]-x1, pxy[1]-y1
                    L2 = vx*vx + vy*vy or 1e-9
                    tproj = max(0.0, min(1.0, (wx*vx+wy*vy)/L2))
                    projx = x1 + tproj*vx; projy = y1 + tproj*vy
                    dx, dy = pxy[0]-projx, pxy[1]-projy; d2 = dx*dx + dy*dy
                    if d2 < best_d2:
                        best_d2 = d2; best = rl; best_tvec = tvec; best_width = rl["half_width"]*2.0; best_zextra = rl["z_extra"]
                if not best: continue
                z0 = sampleZ(*pxy)
                deck_z = z0 + best_zextra + 0.0015
                stripes = build_crosswalk_stripes(f"xwalk_{n['id']}", pxy, best_tvec, best_width, deck_z,
                                                  depth=p.xwalk_depth, stripe=p.xwalk_stripe, gap=p.xwalk_gap, edge_margin=p.xwalk_margin)
                for s in stripes:
                    if s.data.materials: s.data.materials[0] = mat_xwalk
                    else: s.data.materials.append(mat_xwalk)
                    for c in list(s.users_collection):
                        try: c.objects.unlink(s)
                        except: pass
                    col_xwalk.objects.link(s); placed += 1
            built["xwalk"] = placed

        # ----- ENHANCED TREE GENERATION -----
        if p.generate_trees:
            tree_generator = TreeGenerator()
            tree_placer = TreePlacer(tree_generator)
            
            all_trees = []
            
            # Trees in forests
            if p.trees_in_forests and land_polygons["forest"]:
                forest_trees = tree_placer.place_trees_in_area(
                    land_polygons["forest"], "forest", 
                    elev_grid, terrain_bbox, p.terrain_z_offset, p.tree_slope_limit
                )
                all_trees.extend(forest_trees)
            
            # Trees in parks
            if p.trees_in_parks and land_polygons["park"]:
                park_trees = tree_placer.place_trees_in_area(
                    land_polygons["park"], "park", 
                    elev_grid, terrain_bbox, p.terrain_z_offset, p.tree_slope_limit
                )
                all_trees.extend(park_trees)
            
            # Street trees
            if p.street_trees and road_lines:
                street_trees = tree_placer.place_trees_along_roads(
                    road_lines, elev_grid, terrain_bbox, 
                    p.terrain_z_offset, p.street_tree_spacing
                )
                all_trees.extend(street_trees)
            
            # Move all trees to trees collection
            for tree in all_trees:
                for c in list(tree.users_collection):
                    try: c.objects.unlink(tree)
                    except: pass
                col_trees.objects.link(tree)
            
            built["trees"] = len(all_trees)
            
            if p.verbose:
                print(f"[MapBuilder] Generated {len(all_trees)} trees")

        # ----- Bridge Piers -----
        if p.add_piers and p.do_roads and road_lines:
            for rl in road_lines:
                if not rl["is_bridge"]: continue
                step = max(4.0, p.pier_spacing)
                pts = []; czs = []; bz = []
                acc = 0.0
                poly = rl["center_xy"]; cz = rl["center_z"]; zextra = rl["z_extra"]
                for i in range(len(poly)-1):
                    x1,y1 = poly[i]; x2,y2 = poly[i+1]
                    z1 = cz[i]; z2 = cz[i+1]
                    seg = math.hypot(x2-x1, y2-y1)
                    t=0.0
                    while acc + (seg - t) >= step:
                        need = step - acc
                        tt = (t + need) / seg
                        px = x1 + (x2-x1)*tt; py = y1 + (y2-y1)*tt
                        pz = z1 + (z2 - z1)*tt
                        pts.append((px,py)); czs.append(pz + zextra); bz.append(pz)
                        t += need; acc = 0.0
                    acc += seg - t
                piers = add_bridge_piers(pts, deck_zs=czs, base_zs=bz, pier_radius=p.pier_radius)
                for pier in piers:
                    for c in list(pier.users_collection):
                        try: c.objects.unlink(pier)
                        except: pass
                    col_roads.objects.link(pier)

        # ----- Export -----
        out_dir = Path(bpy.path.abspath(p.output_dir or "//"))
        out_dir.mkdir(parents=True, exist_ok=True)
        if p.export_fbx:
            fbx_path = str(out_dir / (p.file_basename or "osm_export") + ".fbx")
            bpy.ops.export_scene.fbx(
                filepath=fbx_path, use_selection=False, apply_scale_options='FBX_SCALE_ALL',
                bake_space_transform=False, object_types={'MESH'}, use_mesh_modifiers=True,
                mesh_smooth_type='FACE', use_triangles=False, use_custom_props=False
            )
            self.report({'INFO'}, f"Exported FBX: {fbx_path}")
        if p.export_obj:
            obj_path = str(out_dir / (p.file_basename or "osm_export") + ".obj")
            bpy.ops.export_scene.obj(
                filepath=obj_path, use_selection=False, use_mesh_modifiers=True, use_triangles=False
            )
            self.report({'INFO'}, f"Exported OBJ: {obj_path}")

        msg = f"Enhanced build: roads={built['roads']} bldg={built['bldg']} water={built['water']} land={built['land']} rail={built['rail']} xwalk={built['xwalk']} trees={built['trees']}"
        self.report({'INFO'}, msg)
        if p.verbose: 
            print("[MapBuilder Enhanced]", msg, "| Address:", label)
        return {'FINISHED'}
    
    def create_elevation_material(self, elevation_range):
        """Create a material that colors based on elevation"""
        mat_name = "MAT_Terrain_Elevation"
        mat = bpy.data.materials.get(mat_name)
        if mat: return mat
        
        mat = bpy.data.materials.new(mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        # Create nodes
        output = nodes.new('ShaderNodeOutputMaterial')
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        colorramp = nodes.new('ShaderNodeValToRGB')
        geometry = nodes.new('ShaderNodeNewGeometry')
        separate_xyz = nodes.new('ShaderNodeSeparateXYZ')
        map_range = nodes.new('ShaderNodeMapRange')
        
        # Setup color ramp for elevation
        colorramp.color_ramp.elements[0].color = (0.1, 0.3, 0.8, 1.0)  # Low elevation (blue)
        colorramp.color_ramp.elements[1].color = (0.8, 0.6, 0.2, 1.0)  # High elevation (brown)
        
        # Setup map range for elevation
        emin, emax = elevation_range
        map_range.inputs['From Min'].default_value = emin
        map_range.inputs['From Max'].default_value = emax
        
        # Connect nodes
        mat.node_tree.links.new(geometry.outputs['Position'], separate_xyz.inputs['Vector'])
        mat.node_tree.links.new(separate_xyz.outputs['Z'], map_range.inputs['Value'])
        mat.node_tree.links.new(map_range.outputs['Result'], colorramp.inputs['Fac'])
        mat.node_tree.links.new(colorramp.outputs['Color'], bsdf.inputs['Base Color'])
        mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
        return mat
    
    def create_slope_material(self):
        """Create a material that colors based on slope"""
        mat_name = "MAT_Terrain_Slope"
        mat = bpy.data.materials.get(mat_name)
        if mat: return mat
        
        mat = bpy.data.materials.new(mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        # Create nodes
        output = nodes.new('ShaderNodeOutputMaterial')
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        colorramp = nodes.new('ShaderNodeValToRGB')
        geometry = nodes.new('ShaderNodeNewGeometry')
        vector_math = nodes.new('ShaderNodeVectorMath')
        
        # Setup color ramp for slope
        colorramp.color_ramp.elements[0].color = (0.2, 0.8, 0.2, 1.0)  # Flat areas (green)
        colorramp.color_ramp.elements[1].color = (0.8, 0.2, 0.2, 1.0)  # Steep areas (red)
        
        # Setup vector math to get normal steepness
        vector_math.operation = 'DOT_PRODUCT'
        vector_math.inputs[1].default_value = (0, 0, 1)  # Up vector
        
        # Connect nodes
        mat.node_tree.links.new(geometry.outputs['Normal'], vector_math.inputs[0])
        mat.node_tree.links.new(vector_math.outputs['Value'], colorramp.inputs['Fac'])
        mat.node_tree.links.new(colorramp.outputs['Color'], bsdf.inputs['Base Color'])
        mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
        return mat

# -------------------------------------------------------------
# Enhanced UI Panel
# -------------------------------------------------------------
class OSM_PT_Panel(bpy.types.Panel):
    bl_idname = "OSM_PT_panel"
    bl_label = "Enhanced OSM Map Builder"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "OSM"

    def draw(self, ctx):
        l = self.layout; p = ctx.scene.osm_builder

        # Connection settings
        col = l.column(align=True)
        col.prop(p, "contact_email")
        col.prop(p, "overpass_ep")
        col.prop(p, "address")
        row = col.row(align=True); row.prop(p, "radius_value"); row.prop(p, "radius_unit", expand=True)
        col.prop(p, "clear_scene")
        col.prop(p, "verbose")
        row = col.row(align=True)
        row.operator("osm.test_connection", icon='URL')
        row.operator("osm.test_terrain", icon='MATPLANE')

        l.separator(); l.label(text="Layers")
        col = l.column(align=True)
        col.prop(p, "do_roads"); col.prop(p, "do_crosswalks")
        col.prop(p, "do_buildings"); col.prop(p, "do_water"); col.prop(p, "do_landuse"); col.prop(p, "do_rail")

        # Enhanced Terrain Section
        l.separator(); l.label(text="Enhanced Terrain", icon='MESH_GRID')
        col = l.column(align=True)
        col.prop(p, "use_terrain")
        if p.use_terrain:
            col.prop(p, "dem_source")
            if p.dem_source == 'MAPBOX':
                col.prop(p, "mapbox_token")
            col.prop(p, "terrain_res")
            col.prop(p, "terrain_size_mode")
            if p.terrain_size_mode == 'CUSTOM':
                col.prop(p, "terrain_size_m")
            col.prop(p, "terrain_z_offset")
            col.prop(p, "terrain_subdivision")
            
            # Elevation visualization
            col.separator()
            col.prop(p, "terrain_material_mode")
            col.prop(p, "show_contours")
            if p.show_contours:
                col.prop(p, "contour_interval")

        # Tree Generation Section
        l.separator(); l.label(text="Tree Generation", icon='OUTLINER_OB_MESH')
        col = l.column(align=True)
        col.prop(p, "generate_trees")
        if p.generate_trees:
            col.prop(p, "tree_density")
            col.prop(p, "tree_scale_variation")
            col.prop(p, "tree_slope_limit")
            
            col.separator()
            col.label(text="Tree Placement:")
            col.prop(p, "trees_in_forests")
            col.prop(p, "trees_in_parks")
            col.prop(p, "street_trees")
            if p.street_trees:
                col.prop(p, "street_tree_spacing")

        l.separator(); l.label(text="Bridges & Overpasses")
        col = l.column(align=True)
        col.prop(p, "bridge_clearance")
        col.prop(p, "tunnel_offset")
        col.prop(p, "add_piers")
        if p.add_piers:
            col.prop(p, "pier_spacing")
            col.prop(p, "pier_radius")

        l.separator(); col = l.column(align=True)
        col.prop(p, "ground_size")

        l.separator(); l.label(text="Export")
        col = l.column(align=True)
        col.prop(p, "export_fbx"); col.prop(p, "export_obj")
        col.prop(p, "output_dir"); col.prop(p, "file_basename")

        l.separator()
        l.operator("osm.build_from_address", text="Build Enhanced Scene", icon='WORLD')

# -------------------------------------------------------------
# Register
# -------------------------------------------------------------
classes = (OSMProps, OSM_OT_Test, OSM_OT_TestTerrain, OSM_OT_Build, OSM_PT_Panel)

def register():
    for c in classes: bpy.utils.register_class(c)
    bpy.types.Scene.osm_builder = bpy.props.PointerProperty(type=OSMProps)

def unregister():
    for c in reversed(classes): bpy.utils.unregister_class(c)
    del bpy.types.Scene.osm_builder

if __name__ == "__main__":
    register()