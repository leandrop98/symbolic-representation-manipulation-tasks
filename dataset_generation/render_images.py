import requests
import bpy
import math, sys, random, argparse, json, os, tempfile
from datetime import datetime as dt
from collections import Counter
from mathutils.bvhtree import BVHTree
import bpy, bmesh
import time
from mathutils import Euler
import math
from datetime import datetime
import uuid

LEFT = "left"
RIGHT = "right"
ON = "on"
UNDER ="under"
FRONT = "in front of"
BEHIND = "behind"
LEFT_BEHIND = "left_behind"
RIGHT_BEHIND = "right_behind"
LEFT_FRONT = "left_front"
RIGHT_FRONT = "right_front"
NEAR = "near"
FAR = "far"

relationships = [LEFT,RIGHT,UNDER,ON,FRONT,BEHIND,LEFT_BEHIND,RIGHT_BEHIND,LEFT_FRONT,RIGHT_FRONT]


## SHAPE NET Test Query
""" query = "kitchen"
r =requests.get('https://shapenet.org/solr/models3d/select?q='+query+'+AND+source%3A3dw&rows=1000&wt=json')
if(r.status_code==200):
    print(r.text)   """ 

## BLENDER iteration
# remove mesh Cube
""" bpy.ops.object.select_all(action='DESELECT')
# Deselect all


# https://wiki.blender.org/wiki/Reference/Release_Notes/2.80/Python_API/Scene_and_Object_API
bpy.data.objects['Cube'].select_set(True) # Blender 2.8x
bpy.ops.object.delete() 

# load object in scene
file_loc = '/home/leandro/clevr/clevr-dataset-gen/image_generation/mug.obj'
imported_object = bpy.ops.import_scene.obj(filepath=file_loc)
obj_object = bpy.context.selected_objects[0] ####<--Fix
obj_object.location.x = 1
obj_object.scale = (5,5,5)
print('Imported name: ', obj_object.name)

# print all objects in scene
for obj in bpy.data.objects:
    print(obj.name) """

INSIDE_BLENDER = True
try:
  import bpy, bpy_extras
  from mathutils import Vector
except ImportError as e:
  INSIDE_BLENDER = False
if INSIDE_BLENDER:
  try:
    import utils
  except ImportError as e:
    print("\nERROR")
    print("Running render_images.py from Blender and cannot import utils.py.") 
    print("You may need to add a .pth file to the site-packages of Blender's")
    print("bundled python with a command like this:\n")
    print("echo $PWD >> $BLENDER/$VERSION/python/lib/python3.5/site-packages/clevr.pth")
    print("\nWhere $BLENDER is the directory where Blender is installed, and")
    print("$VERSION is your Blender version (such as 2.78).")
    sys.exit(1)

parser = argparse.ArgumentParser()

# Input options
parser.add_argument('--base_scene_blendfile', default='data/base_scene.blend',
    help="Base blender file on which all scenes are based; includes " +
          "ground plane, lights, and camera.")
parser.add_argument('--properties_json', default='data/properties.json',
    help="JSON file defining objects, materials, sizes, and colors. " +
         "The \"colors\" field maps from CLEVR color names to RGB values; " +
         "The \"sizes\" field maps from CLEVR size names to scalars used to " +
         "rescale object models; the \"materials\" and \"shapes\" fields map " +
         "from CLEVR material and shape names to .blend files in the " +
         "--object_material_dir and --shape_dir directories respectively.")
parser.add_argument('--models_dir', default='data/models',
    help="Directory where .obj files for object models are stored")


# Settings for objects
parser.add_argument('--min_objects', default=3, type=int,
    help="The minimum number of objects to place in each scene")
parser.add_argument('--max_objects', default=10, type=int,
    help="The maximum number of objects to place in each scene")
parser.add_argument('--min_dist', default=0.25, type=float,
    help="The minimum allowed distance between object centers")
parser.add_argument('--margin', default=0.4, type=float,
    help="Along all cardinal directions (left, right, front, back), all " +
         "objects will be at least this distance apart. This makes resolving " +
         "spatial relationships slightly less ambiguous.")
parser.add_argument('--min_pixels_per_object', default=200, type=int,
    help="All objects will have at least this many visible pixels in the " +
         "final rendered images; this ensures that no objects are fully " +
         "occluded by other objects.")
parser.add_argument('--max_retries', default=50, type=int,
    help="The number of times to try placing an object before giving up and " +
         "re-placing all objects in the scene.")
parser.add_argument('--border_limit', default=4, type=float,
    help="The number to change the sensitivy of the relatioships. Higher number means the single "+
    "relationships are more narrow")

# Output settings
parser.add_argument('--start_idx', default=0, type=int,
    help="The index at which to start for numbering rendered images. Setting " +
         "this to non-zero values allows you to distribute rendering across " +
         "multiple machines and recombine the results later.")
parser.add_argument('--num_images', default=5, type=int,
    help="The number of images to render")
parser.add_argument('--filename_prefix', default='CLEVR',
    help="This prefix will be prepended to the rendered images and JSON scenes")
parser.add_argument('--split', default='new',
    help="Name of the split for which we are rendering. This will be added to " +
         "the names of rendered images, and will also be stored in the JSON " +
         "scene structure for each image.")
parser.add_argument('--output_image_dir', default='../output/images/',
    help="The directory where output images will be stored. It will be " +
         "created if it does not exist.")
parser.add_argument('--output_scene_dir', default='../output/scenes/',
    help="The directory where output JSON scene structures will be stored. " +
         "It will be created if it does not exist.")
parser.add_argument('--output_scene_file', default='../output/CLEVR_scenes.json',
    help="Path to write a single JSON file containing all scene information")
parser.add_argument('--output_blend_dir', default='output/blendfiles',
    help="The directory where blender scene files will be stored, if the " +
         "user requested that these files be saved using the " +
         "--save_blendfiles flag; in this case it will be created if it does " +
         "not already exist.")
parser.add_argument('--save_blendfiles', type=int, default=0,
    help="Setting --save_blendfiles 1 will cause the blender scene file for " +
         "each generated image to be stored in the directory specified by " +
         "the --output_blend_dir flag. These files are not saved by default " +
         "because they take up ~5-10MB each.")
parser.add_argument('--version', default='1.0',
    help="String to store in the \"version\" field of the generated JSON file")
parser.add_argument('--license',
    default="Creative Commons Attribution (CC-BY 4.0)",
    help="String to store in the \"license\" field of the generated JSON file")
parser.add_argument('--date', default=dt.today().strftime("%m/%d/%Y"),
    help="String to store in the \"date\" field of the generated JSON file; " +
         "defaults to today's date")

# Rendering options
parser.add_argument('--use_gpu', default=0, type=int,
    help="Setting --use_gpu 1 enables GPU-accelerated rendering using CUDA. " +
         "You must have an NVIDIA GPU with the CUDA toolkit installed for " +
         "to work.")
parser.add_argument('--width', default=320, type=int,
    help="The width (in pixels) for the rendered images")
parser.add_argument('--height', default=240, type=int,
    help="The height (in pixels) for the rendered images")
parser.add_argument('--key_light_jitter', default=1.0, type=float,
    help="The magnitude of random jitter to add to the key light position.")
parser.add_argument('--fill_light_jitter', default=1.0, type=float,
    help="The magnitude of random jitter to add to the fill light position.")
parser.add_argument('--back_light_jitter', default=1.0, type=float,
    help="The magnitude of random jitter to add to the back light position.")
parser.add_argument('--camera_jitter', default=0.5, type=float,
    help="The magnitude of random jitter to add to the camera position")
parser.add_argument('--render_num_samples', default=512, type=int,
    help="The number of samples to use when rendering. Larger values will " +
         "result in nicer images but will cause rendering to take longer.")
parser.add_argument('--render_min_bounces', default=8, type=int,
    help="The minimum number of bounces to use for rendering.")
parser.add_argument('--render_max_bounces', default=8, type=int,
    help="The maximum number of bounces to use for rendering.")
parser.add_argument('--render_tile_size', default=256, type=int,
    help="The tile size to use for rendering. This should not affect the " +
         "quality of the rendered image but may affect the speed; CPU-based " +
         "rendering may achieve better performance using smaller tile sizes " +
         "while larger tile sizes may be optimal for GPU-based rendering.")



#render scene function
def render_scene(args,
    objects_category,
    objects_id,
    relationship,
    output_image_id,
    output_index=0,
    output_split='none',
    output_scene='render_json',
    output_blendfile=None
):

  # Load the main blendfile
  bpy.ops.wm.open_mainfile(filepath='data/base_scene.blend')

  # Set render arguments so we can get pixel coordinates later.
  # We use functionality specific to the CYCLES renderer so BLENDER_RENDER
  # cannot be used.
  render_args = bpy.context.scene.render
  render_args.engine = "BLENDER_EEVEE"
  render_args.filepath = args.output_image_dir + "/" + output_image_id + ".png"
  render_args.resolution_x = args.width
  render_args.resolution_y = args.height
  render_args.resolution_percentage = 100
  render_args.tile_x = args.render_tile_size
  render_args.tile_y = args.render_tile_size
  if args.use_gpu == 1:
    # Blender changed the API for enabling CUDA at some point
    if bpy.app.version < (2, 78, 0):
      bpy.context.user_preferences.system.compute_device_type = 'CUDA'
      bpy.context.user_preferences.system.compute_device = 'CUDA_0'
    else:
      cycles_prefs = bpy.context.user_preferences.addons['cycles'].preferences
      cycles_prefs.compute_device_type = 'CUDA'

  # Some CYCLES-specific stuff
  bpy.data.worlds['World'].cycles.sample_as_light = True
  bpy.context.scene.cycles.blur_glossy = 2.0
  bpy.context.scene.cycles.samples = args.render_num_samples
  bpy.context.scene.cycles.transparent_min_bounces = args.render_min_bounces
  bpy.context.scene.cycles.transparent_max_bounces = args.render_max_bounces
  if args.use_gpu == 1:
    bpy.context.scene.cycles.device = 'GPU'

  # This will give ground-truth information about the scene and its objects
  scene_struct = {
      'split': output_split,
      'image_index': output_index,
      'image_filename': os.path.basename(output_image_id+".png"),
      'objects': [],
      'directions': {},
  }

  # Put a plane on the ground so we can compute cardinal directions
  bpy.ops.mesh.primitive_plane_add(size=5)
  plane = bpy.context.scene.view_layers[0].objects.active 

  def rand(L):
    return 2.0 * L * (random.random() - 0.5)

  # Add random jitter to camera position
  if args.camera_jitter > 0:
    for i in range(3):
      bpy.data.objects['Camera'].location[i] += rand(args.camera_jitter)

  # Figure out the left, up, and behind directions along the plane and record
  # them in the scene structure
  camera = bpy.data.objects['Camera']
  plane_normal = plane.data.vertices[0].normal
  cam_behind = camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))
  cam_left = camera.matrix_world.to_quaternion() @ Vector((-1, 0, 0))
  cam_up = camera.matrix_world.to_quaternion() @ Vector((0, 1, 0))
  plane_behind = (cam_behind - cam_behind.project(plane_normal)).normalized()
  plane_left = (cam_left - cam_left.project(plane_normal)).normalized()
  plane_up = cam_up.project(plane_normal).normalized()

  # Delete the plane; we only used it for normals anyway. The base scene file
  # contains the actual ground plane.
  utils.delete_object(plane)

  # Save all six axis-aligned directions in the scene struct
  scene_struct['directions']['behind'] = tuple(plane_behind)
  scene_struct['directions']['front'] = tuple(-plane_behind)
  scene_struct['directions']['left'] = tuple(plane_left)
  scene_struct['directions']['right'] = tuple(-plane_left)
  scene_struct['directions']['above'] = tuple(plane_up)
  scene_struct['directions']['below'] = tuple(-plane_up)

  # Add random jitter to lamp positions
  if args.key_light_jitter > 0:
    for i in range(3):
      bpy.data.objects['Lamp_Key'].location[i] += rand(args.key_light_jitter)
  if args.back_light_jitter > 0:
    for i in range(3):
      bpy.data.objects['Lamp_Back'].location[i] += rand(args.back_light_jitter)
  if args.fill_light_jitter > 0:
    for i in range(3):
      bpy.data.objects['Lamp_Fill'].location[i] += rand(args.fill_light_jitter)

  # Now make some random objects, return scene information
  scene_struct = add_two_objects(scene_struct, args, camera, objects_category, objects_id,relationship)

  
 
  # Render the scene and dump the scene data structure
  #scene_struct['objects'] = objects
  #scene_struct['relationships'] = compute_all_relationships(scene_struct)
  # Render scene
  while True:
    try:
      bpy.ops.render.render(write_still=True)
      break
    except Exception as e:
      print(e)

  # Save scene structure in json file
  with open(args.output_image_dir + "/" + output_image_id + ".json", 'w') as f:
    json.dump(scene_struct, f, indent=2)

  if output_blendfile is not None:
    bpy.ops.wm.save_as_mainfile(filepath=output_blendfile)

def add_two_objects(scene_struct, args, camera, objects_category, objects_id, relationship):
  
  """
  Add random objects to the current blender scene
  """

  # Get the path of the objects to add to the scene
  obj1_path = args.models_dir + "/" + objects_category[0] + "/" +  objects_id[0]  + "/models/model_normalized.obj"
  obj2_path = args.models_dir + "/" + objects_category[1] + "/" +  objects_id[1]  + "/models/model_normalized.obj"
  
  scene_objects = []

  # Import Object 1 in the scene in the center position with random z orientation
  imported_object = bpy.ops.import_scene.obj(filepath=obj1_path)
  selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
  print(selected_objects)
  obj_object1 = selected_objects[0] 
  obj_object1.name = "Object1_" + relationship+ "_" + str(datetime.now())
  obj_object1.delta_rotation_euler =  Euler((0,0, math.radians(utils.rand_rotation())), 'XYZ')
  scene_objects.append(obj_object1)

  # Import Object 2 in the scene in the center position with random z orientation
  imported_object = bpy.ops.import_scene.obj(filepath=obj2_path)
  selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
  obj_object2 = selected_objects[0] 
  obj_object2.name = "Object2_" + relationship + "_" +  str(datetime.now())
  obj_object2.delta_rotation_euler =  Euler((0,0, math.radians(utils.rand_rotation())), 'XYZ')
  scene_objects.append(obj_object2)

  # Change z location to put objects in the floor
  
  bbverts_obj1 = [obj_object1.matrix_world@Vector(bbvert) for bbvert in obj_object1.bound_box]
  bbverts_obj2 = [obj_object2.matrix_world@Vector(bbvert) for bbvert in obj_object2.bound_box]
  min_z_obj1 = min([vec[2] for vec in bbverts_obj1])
  min_z_obj2 = min([vec[2] for vec in bbverts_obj2])
  obj_object1.location.z -= min_z_obj1
  obj_object2.location.z -= min_z_obj2  

  # Apply the relationshiop to the second object
  border_limit = args.border_limit
  if(relationship==LEFT):
    y_pos = -((obj_object1.dimensions.y) /2 + (obj_object2.dimensions.y)/2 + random.random()*0.3) 
    x_pos =  random.uniform(y_pos/border_limit, -y_pos/border_limit)
    obj_object2.location.y = y_pos
    obj_object2.location.x = x_pos
  elif(relationship==RIGHT):
    y_pos = ((obj_object1.dimensions.y) /2 + (obj_object2.dimensions.y)/2 + random.random()*0.3) 
    x_pos =  random.uniform(-y_pos/border_limit, y_pos/border_limit)
    obj_object2.location.y = y_pos
    obj_object2.location.x = x_pos
  elif(relationship==FRONT):
    x_pos = ((obj_object1.dimensions.y) /2 + (obj_object2.dimensions.y)/2 + random.random()*0.3) 
    y_pos = random.uniform(-x_pos/border_limit, x_pos/border_limit)
    obj_object2.location.y = y_pos
    obj_object2.location.x = x_pos
  elif(relationship==BEHIND):
    x_pos = -((obj_object1.dimensions.y) /2 + (obj_object2.dimensions.y)/2 + random.random()*0.3) 
    y_pos =  random.uniform(x_pos/border_limit, -x_pos/border_limit)
    obj_object2.location.y = y_pos
    obj_object2.location.x = x_pos
  elif(relationship==LEFT_BEHIND):
    y_pos = -((obj_object1.dimensions.y) /2 + (obj_object2.dimensions.y)/2 + random.random()*0.3) 
    x_pos =  random.uniform(y_pos*border_limit, y_pos/border_limit)
    obj_object2.location.y = y_pos
    obj_object2.location.x = x_pos
  elif(relationship==RIGHT_BEHIND):
    y_pos = ((obj_object1.dimensions.y) /2 + (obj_object2.dimensions.y)/2 + random.random()*0.3) 
    x_pos =  random.uniform(-y_pos/border_limit, -y_pos*border_limit)
    obj_object2.location.y = y_pos
    obj_object2.location.x = x_pos
  elif(relationship==LEFT_FRONT):
    y_pos = -((obj_object1.dimensions.y) /2 + (obj_object2.dimensions.y)/2 + random.random()*0.3) 
    x_pos =  random.uniform(-y_pos/border_limit, -y_pos*border_limit)
    obj_object2.location.y = y_pos
    obj_object2.location.x = x_pos
  elif(relationship==RIGHT_FRONT):
    y_pos = ((obj_object1.dimensions.y) /2 + (obj_object2.dimensions.y)/2 + random.random()*0.3) 
    x_pos =  random.uniform(y_pos/border_limit, y_pos*border_limit)
    obj_object2.location.y = y_pos
    obj_object2.location.x = x_pos
  elif(relationship==ON):
    x_pos = random.uniform(-obj_object1.dimensions.x/2 , obj_object1.dimensions.x/2) 
    y_pos = random.uniform(-obj_object1.dimensions.y/2 , obj_object1.dimensions.y/2) 
    z_pos = (obj_object1.matrix_world @ obj_object1.dimensions)
    #obj_object2.location.y = y_pos
    #obj_object2.location.x = x_pos
    obj_object2.location.z += z_pos[2]


  ## Override context due to blender 
  for window in bpy.context.window_manager.windows:
    screen = window.screen

    for area in screen.areas:
        if area.type == 'VIEW_3D':
            override = {'window': window, 'screen': screen, 'area': area}
            bpy.ops.screen.screen_full_area(override)
            break


  # Get the 3d bounding box of the object and create the metadata
  objects_metadata = []
  for i, obj in enumerate(scene_objects):
    # Get 3d bounding box of the object
    bbverts = [obj.matrix_world@Vector(bbvert) for bbvert in obj.bound_box]
    bbox_3d_obj = [utils.get_camera_coords(camera, bbvert) for bbvert in bbverts]
    obj_metadata = {
      'id':str(uuid.uuid1()),
      'shapenet_id': objects_id[i],
      'category': objects_category[i],
      '3d_bbox': bbox_3d_obj,
    }
    objects_metadata.append(obj_metadata)

  relationships = compute_all_relationships(scene_objects,objects_metadata)
  metadata = {"objects":objects_metadata,
              "relationships":relationships}

  return metadata

  # Check that all objects are at least partially visible in the rendered image
  """ all_visible = check_visibility(blender_objects, args.min_pixels_per_object)
  if not all_visible:
    # If any of the objects are fully occluded then start over; delete all
    # objects from the scene and place them all again.
    print('Some objects are occluded; replacing objects')
    for obj in blender_objects:
      utils.delete_object(obj)
    return add_random_objects(scene_struct, num_objects, args, camera)"""

  return None, None

def compute_all_relationships(scene_objects,objects_metadata):
  """ Computes relationships between all pairs of objects in the scene.
  
  Returns a dictionary mapping string relationship names to lists of lists of
  integers, where output[rel][i] gives a list of object indices that have the
  relationship rel with object i. For example if j is in output['left'][i] then
  object j is left of object i. """

  all_relationships = []
  for i, obj1 in enumerate(scene_objects):
    for j, obj2 in enumerate(scene_objects):
      obj1_size = (obj1.matrix_world @ obj1.dimensions)
      obj2_size = (obj2.matrix_world @ obj2.dimensions)
      relationship = None
      if obj1==obj2:
        continue
      # Center in object 2, see position of obj1 relatively to obj2
      # BEHIND
      if(obj1.location.y-obj2.location.y >= (obj1.location.x-obj2.location.x)/args.border_limit and
        obj1.location.y-obj2.location.y <= -(obj1.location.x-obj2.location.x)/args.border_limit ):
        relationship = {"object":objects_metadata[i]["id"],
                        "subject":objects_metadata[j]["id"],
                        "predicate:":BEHIND
                       }
      # FRONT OF
      elif(obj1.location.y-obj2.location.y <= (obj1.location.x-obj2.location.x)/args.border_limit and
        obj1.location.y-obj2.location.y >= -(obj1.location.x-obj2.location.x)/args.border_limit ):
        relationship = {"object":objects_metadata[i]["id"],
                        "subject":objects_metadata[j]["id"],
                        "predicate:":FRONT
                       }
      # LEFT
      elif(obj1.location.y-obj2.location.y >= (obj1.location.x-obj2.location.x)/args.border_limit and
        obj1.location.y-obj2.location.y <= -(obj1.location.x-obj2.location.x)/args.border_limit ):
        relationship = {"object":objects_metadata[i]["id"],
                        "subject":objects_metadata[j]["id"],
                        "predicate:":LEFT
                       }
      # RIGHT
      elif(obj1.location.y-obj2.location.y <= (obj1.location.x-obj2.location.x)/args.border_limit and
        obj1.location.y-obj2.location.y >= -(obj1.location.x-obj2.location.x)/args.border_limit ):
        relationship = {"object":objects_metadata[i]["id"],
                        "subject":objects_metadata[j]["id"],
                        "predicate:":RIGHT
                       }
      # RIGHT_BEHIND
      elif(obj1.location.y-obj2.location.y >=  (obj1.location.x-obj2.location.x)/args.border_limit and
        obj1.location.y-obj2.location.y <= args.border_limit*(obj1.location.x-obj2.location.x) ):
        relationship = {"object":objects_metadata[i]["id"],
                        "subject":objects_metadata[j]["id"],
                        "predicate:":RIGHT_BEHIND
                       }
      # LEFT_BEHIND
      elif(obj1.location.y-obj2.location.y >=  -(obj1.location.x-obj2.location.x)/args.border_limit and
        obj1.location.y-obj2.location.y <= -args.border_limit*(obj1.location.x-obj2.location.x) ):
        relationship = {"object":objects_metadata[i]["id"],
                        "subject":objects_metadata[j]["id"],
                        "predicate:":LEFT_BEHIND
                       }
      # RIGHT_FRONT
      elif(obj1.location.y-obj2.location.y >=  -args.border_limit*(obj1.location.x-obj2.location.x) and
        obj1.location.y-obj2.location.y <= -(obj1.location.x-obj2.location.x)/args.border_limit):
        relationship = {"object":objects_metadata[i]["id"],
                        "subject":objects_metadata[j]["id"],
                        "predicate:":RIGHT_FRONT
                       }
      # LEFT_FRONT
      elif(obj1.location.y-obj2.location.y >= -args.border_limit*(obj1.location.x-obj2.location.x)and
        obj1.location.y-obj2.location.y <= -(obj1.location.x-obj2.location.x)/args.border_limit):
        relationship = {"object":objects_metadata[i]["id"],
                        "subject":objects_metadata[j]["id"],
                        "predicate:":LEFT_FRONT
                       }
      # ON
      elif(obj1.location.z >= obj2_size[2]):
        relationship = {"object":objects_metadata[i]["id"],
                        "subject":objects_metadata[j]["id"],
                        "predicate:":ON
                        }
      # UNDER
      elif(obj1.location.z < obj2_size[2]):
        relationship = {"object":objects_metadata[i]["id"],
                        "subject":objects_metadata[j]["id"],
                        "predicate:":UNDER
                        }
      # Add the relationship to the array of relationships
      all_relationships.append(relationship)

  return all_relationships

def objects_overlap(obj1,obj2):

  #create bmesh objects
  bm1 = bmesh.new()
  bm2 = bmesh.new()

  #fill bmesh data from objects
  bm1.from_mesh(obj1.data)
  bm2.from_mesh(obj2.data)

  #fixed it here:
  #bm1.transform(obj1.matrix_world)
  #bm2.transform(obj2.matrix_world) 

  #make BVH tree from BMesh of objects
  obj_now_BVHtree = BVHTree.FromBMesh(bm1)
  obj_next_BVHtree = BVHTree.FromBMesh(bm2)           

  #get intersecting pairs
  inter = obj_now_BVHtree.overlap(obj_next_BVHtree)

  #if list is empty, no objects are touching
  if inter != []:
      print("obj1 and obj2 are touching!")
      return True
  else:
      print("obj1 and obj2 NOT touching!")
      return False

def add_random_table(args, scene_struct, camera, table_ids):
 
  # Get the path of the objects to add to the scene

  table_id = random.choice(table_ids)
  obj_path = args.models_dir + "/table/" +  table_id  + "/models/model_normalized.obj"
  

  # Import Object 1 in the scene in the center position with random z orientation
  imported_object = bpy.ops.import_scene.obj(filepath=obj_path)
  selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
  obj_object = selected_objects[0] 
  obj_object.name = "Table" + str(datetime.now())
  obj_object.delta_rotation_euler =  Euler((0,0, math.radians(utils.rand_rotation())), 'XYZ')


  # Change z location to put objects in the floor
  
  bbverts_obj = [obj_object.matrix_world@Vector(bbvert) for bbvert in obj_object.bound_box]
  min_z_obj = min([vec[2] for vec in bbverts_obj])
  obj_object.location.z -= min_z_obj  

  ## Override context due to blender 
  for window in bpy.context.window_manager.windows:
    screen = window.screen

    for area in screen.areas:
        if area.type == 'VIEW_3D':
            override = {'window': window, 'screen': screen, 'area': area}
            bpy.ops.screen.screen_full_area(override)
            break

  # Get the 3d bounding box of the object and create the metadata
  # Get 3d bounding box of the object
  bbverts = [obj_object.matrix_world@Vector(bbvert) for bbvert in obj_object.bound_box]
  bbox_3d_obj = [utils.get_camera_coords(camera, bbvert) for bbvert in bbverts]
  obj_metadata = {
    'id':str(uuid.uuid1()),
    'shapenet_id': table_id,
    'scene_object_name':os.name,
    'category': "Table",
    '3d_bbox': bbox_3d_obj,
  }
  scene_struct["objects"].append(obj_metadata) 



def main(args):
  ##
  obj1_path = '/home/leandro/clevr/clevr-dataset-gen/image_generation/mug.obj'
  obj2_path = '/home/leandro/clevr/clevr-dataset-gen/image_generation/mug.obj'

  scene_struct = {"objects":[],
                  "relationships":[]}

  render_scene(args, [models_category1,models_category2],[model1,model2],relationship,output_image_id=str(uuid.uuid1()))


  # # Read file with the 3d models list
  # try:
  #   with open(args.models_dir + "/models.json", "r") as read_file:
  #     models_dict = json.load(read_file)
  #   for models_category1 in models_dict:      
  #     for model1 in models_dict[models_category1]:
  #       for models_category2 in models_dict:      
  #         for model2 in models_dict[models_category2]:
  #           print(models_category1 + " (" +model1+") -> " + models_category2 + "("+model2+")")
  #           for relationship in relationships:
  #             render_scene(args, [models_category1,models_category2],[model1,model2],relationship,output_image_id=str(uuid.uuid1()))

    
  except FileNotFoundError:
    print("File \"" + args.models_dir + "/objects.json" +"\" was not found!")


if __name__ == '__main__':
  if INSIDE_BLENDER:
    # Run normally
    argv = utils.extract_args()
    args = parser.parse_args(argv)
    main(args)
  elif '--help' in sys.argv or '-h' in sys.argv:
    parser.print_help()
  else:
    print('This script is intended to be called from blender like this:')
    print()
    print('blender --background --python render_images.py -- [args]')
    print()
    print('You can also run as a standalone python script to view all')
    print('arguments like this:')
    print()
    print('python render_images.py --help')
    
"""
# Run Command
## blender
-b , --background, run in background
-P, --python , python file
"""
