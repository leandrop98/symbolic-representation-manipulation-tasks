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
import shutil
import operator

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
INSIDE = "inside"
OUTSIDE = "outside"
INSIDE_UP = "inside_up"

relationships = [LEFT,RIGHT,UNDER,ON,FRONT,BEHIND,LEFT_BEHIND,RIGHT_BEHIND,LEFT_FRONT,RIGHT_FRONT,INSIDE,INSIDE_UP]
relationships = [LEFT,RIGHT,FRONT,BEHIND,LEFT_BEHIND,RIGHT_BEHIND,LEFT_FRONT,RIGHT_FRONT]


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
parser.add_argument('--radius_near_far', default=2, type=float,
    help="The number to change the radius of what is consideres near or far from an object")

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
parser.add_argument('--delete_previous_images', default=False,
    help="Delete previous generated images from the directory where output images will be stored.")
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
parser.add_argument('--camera_jitter', default=1.0, type=float,
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

def rand_rotation():
  """ Returns a random rotation between 0 and 360 degrees """
  return random.random()*360

#render scene function
def render_scene(args,scene_struct,table_height,
    output_index=0,
    output_split='none',
    output_scene='render_json',
    output_blendfile=None):

  output_image_id = str(uuid.uuid1())
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



  # Put a plane on the ground so we can compute cardinal directions
  #bpy.ops.mesh.primitive_plane_add(size=5)
  #plane = bpy.context.scene.view_layers[0].objects.active 

  # Make light and camre point to the center of the table
  bpy.data.objects['Direction_Object'].location.z += table_height


  def rand(L):
    return 2*L * random.random() - L

  # Put the lamps and the camera above the table
  bpy.data.objects['Lamp_Key'].location.z += table_height
  bpy.data.objects['Lamp_Back'].location.z += table_height
  bpy.data.objects['Lamp_Fill'].location.z += table_height
  bpy.data.objects['Camera'].location.z += table_height
  
  # Add random jitter to camera position
  if args.camera_jitter > 0:
    # X-position of the camera is translated in proximity of the table and objects
    bpy.data.objects['Camera'].location.x +=  random.uniform(-5,10*args.camera_jitter)#5*rand(args.camera_jitter)
    
    # Y-position of the camera is translated in rotation
    bpy.data.objects['Camera'].location.y +=  random.uniform(-args.camera_jitter,args.camera_jitter)#5*rand(args.camera_jitter)
    
    # Z-Position, camera has to be above table
    z_jitter = 2*rand(args.camera_jitter)
    while(bpy.data.objects['Camera'].location.z  + z_jitter < table_height):
      z_jitter = 2 *rand(args.camera_jitter)
    bpy.data.objects['Camera'].location.z += z_jitter


  camera = bpy.data.objects['Camera']

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
  
  bpy.context.view_layer.update() 



  # Check if objects are visible in the picture?
  #check_visibility(scene_struct,100)

  
  # Get bounding boxes of all objects
  for obj_struct in scene_struct['objects']:
    bbverts = [bpy.data.objects[obj_struct['scene_object_name']].matrix_world@Vector(bbvert) for bbvert in bpy.data.objects[obj_struct['scene_object_name']].bound_box]
    bbox_3d_obj = [utils.get_camera_coords(camera,bbvert) for bbvert in bbverts]
    obj_struct["3d_bbox"] = bbox_3d_obj
    all_x = [point[0] for point in bbox_3d_obj]
    all_y = [point[1] for point in bbox_3d_obj]

    # We only need top-left and bottom-right
    obj_struct["2d_bbox"] = [(min(all_x),max(all_y)),(max(all_x),min(all_y))]

  scene_struct['image_filename'] =  os.path.basename(output_image_id+".png")
  scene_struct['relationships'] = compute_all_relationships(args,scene_struct)

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

def add_two_objects(args,scene_struct, objects_category, objects_path, relationship,table_height,table_limit_points):
  
  """
  Add two objects to the current blender scene
  """

  # Get the path of the objects to add to the scene
  obj1_path = objects_path[0] # args.models_dir + "/" + objects_category[0] + "/" +  objects_id[0]  + "/models/model_normalized.obj"
  obj2_path =  objects_path[1] # args.models_dir + "/" + objects_category[1] + "/" +  objects_id[1]  + "/models/model_normalized.obj"
  
  scene_objects = []

  # Import Object 1 in the scene in the center position with random z orientation
  imported_object = bpy.ops.import_scene.obj(filepath=obj1_path)
  selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
  obj_object1 = selected_objects[0] 
  obj_object1.name = "Object1_" + relationship+ "_" + str(datetime.now())
  obj_object1.delta_rotation_euler =  Euler((0,0, math.radians(rand_rotation())), 'XYZ')
  scene_objects.append(obj_object1)

  # Import Object 2 in the scene in the center position with random z orientation
  imported_object = bpy.ops.import_scene.obj(filepath=obj2_path)
  selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
  obj_object2 = selected_objects[0] 
  obj_object2.name = "Object2_" + relationship + "_" +  str(datetime.now())
  obj_object2.delta_rotation_euler =  Euler((0,0, math.radians(rand_rotation())), 'XYZ')
  scene_objects.append(obj_object2)

  bpy.context.view_layer.update() 
  # Change z location to put objects in the table
  
  bbverts_obj1 = [obj_object1.matrix_world@Vector(bbvert) for bbvert in obj_object1.bound_box]
  bbverts_obj2 = [obj_object2.matrix_world@Vector(bbvert) for bbvert in obj_object2.bound_box]
  min_z_obj1 = min([vec[2] for vec in bbverts_obj1])
  min_z_obj2 = min([vec[2] for vec in bbverts_obj2])

  obj_object1.location.z += -min_z_obj1 + table_height
  obj_object2.location.z += -min_z_obj2 + table_height

  max_x = max([point[0]for point in table_limit_points])
  min_x = min([point[0]for point in table_limit_points])
  max_y = max([point[1]for point in table_limit_points])
  min_y = min([point[1]for point in table_limit_points])

  # Apply the relationshiop to the second object
  border_limit = args.border_limit
  if(relationship==LEFT):
    y_pos = -((obj_object1.dimensions.y) /2 + (obj_object2.dimensions.y)/2) + random.random()*min_y
    x_pos =  random.uniform(y_pos/border_limit, -y_pos/border_limit)
    obj_object2.location.y = y_pos
    obj_object2.location.x = x_pos
  elif(relationship==RIGHT):
    y_pos = ((obj_object1.dimensions.y) /2 + (obj_object2.dimensions.y)/2) + random.random()*max_y
    x_pos =  random.uniform(-y_pos/border_limit, y_pos/border_limit)
    obj_object2.location.y = y_pos
    obj_object2.location.x = x_pos
  elif(relationship==FRONT):
    x_pos = ((obj_object1.dimensions.y) /2 + (obj_object2.dimensions.y)/2) + random.random()*max_x
    y_pos = random.uniform(-x_pos/border_limit, x_pos/border_limit)
    obj_object2.location.y = y_pos
    obj_object2.location.x = x_pos
  elif(relationship==BEHIND):
    x_pos = -((obj_object1.dimensions.y) /2 + (obj_object2.dimensions.y)/2) + random.random()*min_x
    y_pos =  random.uniform(x_pos/border_limit, -x_pos/border_limit)
    obj_object2.location.y = y_pos
    obj_object2.location.x = x_pos
  elif(relationship==LEFT_BEHIND):
    y_pos = -((obj_object1.dimensions.y) /2 + (obj_object2.dimensions.y)/2) + random.random()*max_y 
    x_pos =  random.uniform(y_pos*border_limit, y_pos/border_limit)
    obj_object2.location.y = y_pos
    obj_object2.location.x = x_pos
  elif(relationship==RIGHT_BEHIND):
    y_pos = ((obj_object1.dimensions.y) /2 + (obj_object2.dimensions.y)/2) + random.random()*max_y
    x_pos =  random.uniform(-y_pos/border_limit, -y_pos*border_limit)
    obj_object2.location.y = y_pos
    obj_object2.location.x = x_pos
  elif(relationship==LEFT_FRONT):
    y_pos = -((obj_object1.dimensions.y) /2 + (obj_object2.dimensions.y)/2) + random.random()*min_y
    x_pos =  random.uniform(-y_pos/border_limit, -y_pos*border_limit)
    obj_object2.location.y = y_pos
    obj_object2.location.x = x_pos
  elif(relationship==RIGHT_FRONT):
    y_pos = ((obj_object1.dimensions.y) /2 + (obj_object2.dimensions.y)/2) + random.random()*max_y
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
  elif(relationship==INSIDE):
    x_pos = 0
    y_pos = 0
    obj_object2.location.y = y_pos
    obj_object2.location.x = x_pos
    obj_object2.location.z += 0.1
  elif(relationship==INSIDE_UP):
    z_pos = (obj_object1.matrix_world @ obj_object1.dimensions)
    obj_object2.location.y = 0
    obj_object2.location.x = 0
    obj_object2.delta_rotation_euler =  Euler((0,3.14, 0), 'XYZ')
    bpy.context.view_layer.update() 
    bbverts_obj1 = [obj_object1.matrix_world@Vector(bbvert) for bbvert in obj_object1.bound_box]
    max_z_obj1 = max([vec[2] for vec in bbverts_obj1])
    bbverts_obj2 = [obj_object2.matrix_world@Vector(bbvert) for bbvert in obj_object2.bound_box]
    max_z_obj2 = max([vec[2] for vec in bbverts_obj2])
    obj_object2.location.z = max_z_obj1-(max_z_obj2 - obj_object2.location.z)+0.1
  
  #check_position_validity(scene_struct,obj_object2,table_limit_points)

  ## Override context due to blender 
  for window in bpy.context.window_manager.windows:
    screen = window.screen

    for area in screen.areas:
        if area.type == 'VIEW_3D':
            override = {'window': window, 'screen': screen, 'area': area}
            bpy.ops.screen.screen_full_area(override)
            break

  obj1_metadata = {
    'id':str(uuid.uuid1()),
    'scene_object_name':obj_object1.name,
    'category': objects_category[0],
    '3d_bbox': None, # It has to be calculated later with the camera information
  }
  obj2_metadata = {
    'id':str(uuid.uuid1()),
    'scene_object_name':obj_object2.name,
    'category': objects_category[1],
    '3d_bbox': None, # It has to be calculated later with the camera information
  }
  scene_struct['objects'].extend([obj1_metadata,obj2_metadata])

  return scene_struct

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

def add_object(args,scene_struct, object_subject, object_predicate_category,object_predicate_id, relationship,table_height):
    
  """
  Add one object to the current blender scene with a relationship to another object in the scene
  """

  # Get the path of the object to add to the scene
  obj2_path = args.models_dir + "/" +object_predicate_category+ "/" +  object_predicate_id + "/models/model_normalized.obj"
  
  scene_objects = []

  # Import Object 1 in the scene in the center position with random z orientation
  obj_object1 = object_subject

  # Import Object 2 in the scene in the center position with random z orientation
  imported_object = bpy.ops.import_scene.obj(filepath=obj2_path)
  selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
  obj_object2 = selected_objects[0] 
  obj_object2.name = "Object2_" + relationship + "_" +  str(datetime.now())
  obj_object2.delta_rotation_euler =  Euler((0,0, math.radians(rand_rotation())), 'XYZ')
  scene_objects.append(obj_object2)

  # Change z location to put objects in the floor
  
  bbverts_obj1 = [obj_object1.matrix_world@Vector(bbvert) for bbvert in obj_object1.bound_box]
  bbverts_obj2 = [obj_object2.matrix_world@Vector(bbvert) for bbvert in obj_object2.bound_box]
  min_z_obj1 = min([vec[2] for vec in bbverts_obj1])
  min_z_obj2 = min([vec[2] for vec in bbverts_obj2])
  obj_object1.location.z += -min_z_obj1 + table_height
  obj_object2.location.z += -min_z_obj2 + table_height

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
  elif(relationship==INSIDE):
    x_pos = 0
    y_pos = 0
    z_pos = (obj_object1.matrix_world @ obj_object1.dimensions)
    obj_object2.location.y = y_pos
    obj_object2.location.x = x_pos
    obj_object2.location.z += z_pos[2]


  ## Override context due to blender 
  for window in bpy.context.window_manager.windows:
    screen = window.screen

    for area in screen.areas:
        if area.type == 'VIEW_3D':
            override = {'window': window, 'screen': screen, 'area': area}
            bpy.ops.screen.screen_full_area(override)
            break

  obj1_metadata = {
    'id':str(uuid.uuid1()),
    'shapenet_id': object_predicate_id,
    'scene_object_name': obj_object1.name,
    'category': object_predicate_category,
    '3d_bbox': None, # It has to be calculated later with the camera information
  }
  scene_struct['objects'].extend([obj1_metadata])

  return scene_struct

def compute_all_relationships(args,scene_struct):
  """ Computes relationships between all pairs of objects in the scene.
  
  Returns a dictionary mapping string relationship names to lists of lists of
  integers, where output[rel][i] gives a list of object indices that have the
  relationship rel with object i. For example if j is in output['left'][i] then
  object j is left of object i. """
  bpy.context.view_layer.update() 
  all_relationships = []
  for obj1_struct in scene_struct['objects']:
    for obj2_struct in scene_struct['objects']:
      if obj1_struct==obj2_struct:
        continue
      obj1 = bpy.data.objects[obj1_struct['scene_object_name']]
      obj2 = bpy.data.objects[obj2_struct['scene_object_name']]

      obj1_size = (obj1.matrix_world @ obj1.dimensions)
      obj2_size = (obj2.matrix_world @ obj2.dimensions)
      obj1_bbox = [bpy.data.objects[obj1_struct['scene_object_name']].matrix_world@Vector(bbvert) for bbvert in bpy.data.objects[obj1_struct['scene_object_name']].bound_box]
      obj2_bbox = [bpy.data.objects[obj2_struct['scene_object_name']].matrix_world@Vector(bbvert) for bbvert in bpy.data.objects[obj2_struct['scene_object_name']].bound_box]
      min_z_obj1 = min([vec[2] for vec in obj1_bbox])
      min_z_obj2 =  min([vec[2] for vec in obj2_bbox])
      max_z_obj1 = max([vec[2] for vec in obj1_bbox])
      max_z_obj2 =  max([vec[2] for vec in obj2_bbox])
      min_x_obj1 = min([vec[0] for vec in obj1_bbox])
      min_x_obj2 =  min([vec[0] for vec in obj2_bbox])
      max_x_obj1 = max([vec[0] for vec in obj1_bbox])
      max_x_obj2 =  max([vec[0] for vec in obj2_bbox])
      min_y_obj1 = min([vec[1] for vec in obj1_bbox])
      min_y_obj2 =  min([vec[1] for vec in obj2_bbox])
      max_y_obj1 = max([vec[1] for vec in obj1_bbox])
      max_y_obj2 =  max([vec[1] for vec in obj2_bbox])
      # Position of obj1 relatively to obj2
      print(obj1_struct['category'] + ": " + str(obj1.location))
      print(obj2_struct['category'] + ": " +  str(obj2.location))
      print(obj1.location.y-obj2.location.y <= (obj1.location.x-obj2.location.x)/args.border_limit)
      print(obj1.location.y-obj2.location.y >= -(obj1.location.x-obj2.location.x)/args.border_limit)
    

      # INSIDE
      if(min_y_obj1>min_y_obj2 and max_y_obj1<max_y_obj2 and min_x_obj1>min_x_obj2 and max_x_obj1<max_x_obj2 
      and (max_z_obj2-min_z_obj2) + (max_z_obj1-min_z_obj1) > 0.0001 + abs(max(max_z_obj1,max_z_obj2) - min(min_z_obj1,min_z_obj2)) and
      obj1_struct["category"] !='Table' and obj2_struct["category"]!='Table' ): # height of both objects must be higher that the distances of extremes of both objects 
        all_relationships.extend([{"object":obj1_struct["id"],
                      "subject":obj2_struct["id"],
                      "predicate":INSIDE
        }])
        if(abs(max_z_obj2-max_z_obj1)<0.1):
           all_relationships.append({"object":obj2_struct["id"],
                      "subject":obj1_struct["id"],
                      "predicate":ON
          })
      # ON
      elif((abs(min_z_obj1 - max_z_obj2) <= 0.001) 
        and (max_z_obj2-min_z_obj2) + (max_z_obj1-min_z_obj1) - abs(max(max_z_obj1,max_z_obj2) - min(min_z_obj1,min_z_obj2)) <0.001 ):
        all_relationships.extend([{"object":obj1_struct["id"],
                        "subject":obj2_struct["id"],
                        "predicate":ON
                        }])
      # UNDER
      elif(abs(min_z_obj2 - max_z_obj1 )<= 0.001):
        all_relationships.extend([{"object":obj1_struct["id"],
                        "subject":obj2_struct["id"],
                        "predicate":UNDER
        }])

      
       

      if(obj1_struct["category"] !='Table' and obj2_struct["category"]!='Table' ):
        # NEAR
        if(math.sqrt(pow(obj1.location.x-obj2.location.x,2) + pow(obj1.location.y-obj2.location.y,2) + pow(obj1.location.z-obj2.location.z,2) ) <= args.radius_near_far ):
          all_relationships.extend([{"object":obj1_struct["id"],
                        "subject":obj2_struct["id"],
                        "predicate":NEAR
        }])

        # FAR
        elif(math.sqrt(pow(obj1.location.x-obj2.location.x,2) + pow(obj1.location.y-obj2.location.y,2) + pow(obj1.location.z-obj2.location.z,2) ) > args.radius_near_far ):
          all_relationships.extend([{"object":obj1_struct["id"],
                        "subject":obj2_struct["id"],
                        "predicate":FAR
        }])

        # BEHIND
        if(obj1.location.y-obj2.location.y > abs(obj1.location.x-obj2.location.x)*args.border_limit and max_x_obj1<min_x_obj2):
                all_relationships.extend([{"object":obj1_struct["id"],
                          "subject":obj2_struct["id"],
                          "predicate":BEHIND
                        }])
        # FRONT OF
        elif(obj1.location.y-obj2.location.y <= (obj1.location.x-obj2.location.x)/args.border_limit and
          obj1.location.y-obj2.location.y >= -(obj1.location.x-obj2.location.x)/args.border_limit and min_x_obj1 > max_x_obj2):
          all_relationships.extend( [{"object":obj1_struct["id"],
                          "subject":obj2_struct["id"],
                          "predicate":FRONT
                        }])
        # LEFT
        elif(obj1.location.y-obj2.location.y >= (obj1.location.x-obj2.location.x)/args.border_limit and
          obj1.location.y-obj2.location.y <= -(obj1.location.x-obj2.location.x)/args.border_limit and max_y_obj1<min_y_obj2):
          all_relationships.extend([{"object":obj1_struct["id"],
                          "subject":obj2_struct["id"],
                          "predicate":LEFT
                        }])
        # RIGHT
        elif(obj1.location.x-obj2.location.x <= (obj1.location.y-obj2.location.y)/args.border_limit and
          obj1.location.x-obj2.location.x >= -(obj1.location.y-obj2.location.y)/args.border_limit):
          all_relationships.extend([{"object":obj1_struct["id"],
                          "subject":obj2_struct["id"],
                          "predicate":RIGHT
                        }])
        # RIGHT_BEHIND
        elif(obj1.location.y-obj2.location.y >=  (obj1.location.x-obj2.location.x)/args.border_limit and
          obj1.location.y-obj2.location.y <= args.border_limit*(obj1.location.x-obj2.location.x) 
          and min_y_obj1>max_y_obj2 and max_x_obj1<min_x_obj2 ):
          all_relationships.extend([{"object":obj1_struct["id"],
                          "subject":obj2_struct["id"],
                          "predicate":RIGHT_BEHIND
                        }])
        # LEFT_BEHIND
        elif(obj1.location.y-obj2.location.y >=  -(obj1.location.x-obj2.location.x)/args.border_limit and
          obj1.location.y-obj2.location.y <= -args.border_limit*(obj1.location.x-obj2.location.x)and max_y_obj1<min_y_obj2 and max_x_obj1<min_x_obj2):
          all_relationships.extend([{"object":obj1_struct["id"],
                          "subject":obj2_struct["id"],
                          "predicate":LEFT_BEHIND
                        }])
        # RIGHT_FRONT
        elif(obj1.location.y-obj2.location.y >=  -args.border_limit*(obj1.location.x-obj2.location.x) and
          obj1.location.y-obj2.location.y <= -(obj1.location.x-obj2.location.x)/args.border_limit and min_y_obj1>max_y_obj2 and min_x_obj1 > max_x_obj2):
          all_relationships.extend([{"object":obj1_struct["id"],
                          "subject":obj2_struct["id"],
                          "predicate":RIGHT_FRONT
                        }])
        # LEFT_FRONT
        elif(obj1.location.y-obj2.location.y >= -args.border_limit*(obj1.location.x-obj2.location.x)and
          obj1.location.y-obj2.location.y <= -(obj1.location.x-obj2.location.x)/args.border_limit and max_y_obj1<min_y_obj2 and min_x_obj1 > max_x_obj2):
          all_relationships.extend([{"object":obj1_struct["id"],
                          "subject":obj2_struct["id"],
                          "predicate":LEFT_FRONT
                        }])




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

def add_random_table(args, scene_struct, table_model_paths):
 
  # Get the path of the objects to add to the scene
  obj_path = random.choice(table_model_paths)
  

  # Import Object 1 in the scene in the center position with random z orientation
  imported_object = bpy.ops.import_scene.obj(filepath=obj_path)
  selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
  obj_object = selected_objects[0] 
  obj_object.name = "Table"
  obj_object.delta_rotation_euler =  Euler((0,0, math.radians(rand_rotation())), 'XYZ')
  
  # Change table scale
  obj_object.scale.x=10
  obj_object.scale.y=10
  obj_object.scale.z=10
  bpy.context.view_layer.update() 

  # Change z location to put table in the floodr
  
  bbverts_obj = [obj_object.matrix_world@Vector(bbvert) for bbvert in obj_object.bound_box]
  min_z_obj = min([vec[2] for vec in bbverts_obj])
  obj_object.location.z -= min_z_obj  
  bpy.context.view_layer.update() 
  
  # Get table height
  bbverts_obj = [obj_object.matrix_world@Vector(bbvert) for bbvert in obj_object.bound_box]
  max_z_obj = max([vec[2] for vec in bbverts_obj])


  table_height = max_z_obj

  ## Override context due to blender 
  for window in bpy.context.window_manager.windows:
    screen = window.screen

    for area in screen.areas:
        if area.type == 'VIEW_3D':
            override = {'window': window, 'screen': screen, 'area': area}
            bpy.ops.screen.screen_full_area(override)
            break

  obj_metadata = {
    'id':str(uuid.uuid1()),
    'scene_object_name':obj_object.name,
    'category': "Table",
    '3d_bbox': None, # It has to be calculated later with the camera information
  }
  scene_struct["objects"].append(obj_metadata) 

  table_points = []
  all_y = [point[1] for point in bbverts_obj]
  all_z = [point[2] for point in bbverts_obj]
 
  table_limit_points = list( sorted(zip(all_z, bbverts_obj), reverse=True)[:4])
#   print(top_points)
#   all_y = [point[1][1] for point in top_points]
#   print(all_y)
#   y_max_index, y_max = max(enumerate(all_y), key=operator.itemgetter(1))
# top_points[y_max_index]
#   draw_bounding_box_points(bbverts_obj)


  return scene_struct, table_height,table_limit_points

def draw_bounding_box_points(bb_verts):
  for bbvert in bb_verts:
    # Create an empty mesh and the object.
    mesh = bpy.data.meshes.new('Basic_Sphere')
    basic_sphere = bpy.data.objects.new("Basic_Sphere", mesh)

    # Add the object into the scene.
    bpy.context.collection.objects.link(basic_sphere)

    # Select the newly created object
    bpy.context.view_layer.objects.active = basic_sphere
    basic_sphere.select_set(True)
    basic_sphere.dimensions = (0.1,0.1,0.1)
    basic_sphere.location = bbvert

    # Construct the bmesh sphere and assign it to the blender mesh.
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, diameter=1)
    bm.to_mesh(mesh)
    bm.free()



def check_visibility(scene_struct, min_pixels_per_object):
  """
  Check whether all objects in the scene have some minimum number of visible
  pixels; to accomplish this we assign random (but distinct) colors to all
  objects, and render using no lighting or shading or antialiasing; this
  ensures that each object is just a solid uniform color. We can then count
  the number of pixels of each color in the output image to check the visibility
  of each object.
  Returns True if all objects are visible and False otherwise.
  """
  f, path = tempfile.mkstemp(suffix='.png')
  object_colors = render_shadeless(scene_struct, path=path)
  img = bpy.data.images.load(path)
  p = list(img.pixels)
  color_count = Counter((p[i], p[i+1], p[i+2], p[i+3])
                        for i in range(0, len(p), 4))
  os.remove(path)
  print("Number of colors: ", len(color_count))
  if len(color_count) != len(scene_struct['objects']) + 1:
    return False
  print(color_count.most_common())
  for _, count in color_count.most_common():
    if count < min_pixels_per_object:
      return False
  return True

def render_shadeless(scene_struct, path='flat.png'):
  """
  Render a version of the scene with shading disabled and unique materials
  assigned to all objects, and return a set of all colors that should be in the
  rendered image. The image itself is written to path. This is used to ensure
  that all objects will be visible in the final rendered scene.
  """
  render_args = bpy.context.scene.render

  # Cache the render args we are about to clobber
  old_filepath = render_args.filepath
  old_engine = render_args.engine
  old_use_antialiasing = render_args.simplify_gpencil_antialiasing
  old_filter_size = render_args.filter_size

  # Override some render settings to have flat shading
  render_args.filepath = path
  render_args.engine = 'BLENDER_EEVEE'
  render_args.simplify_gpencil_antialiasing = False
  render_args.filter_size = 0


  # Move the lights and ground to layer 2 so they don't render
  # Create a new collection and link it to the scene.
  coll2 = bpy.data.collections.new("Collection 2")
  bpy.context.scene.collection.children.link(coll2)
  # Link active object to the new collection
  bpy.data.objects['Lamp_Key'].hide_render= True
  bpy.data.objects['Lamp_Fill'].hide_render= True
  bpy.data.objects['Lamp_Back'].hide_render= True
  #bpy.data.objects['Area'].hide_render= True
  bpy.data.objects['Plane'].hide_render= True
  bpy.data.lights['Area.002'].use_shadow = False


  # Add random shadeless materials to all objects
 
  object_colors = set()
  old_materials = []
  for i, scene_struct_obj in enumerate(scene_struct['objects']):
    print(scene_struct_obj)
    obj = bpy.data.objects[scene_struct_obj['scene_object_name']]
    obj.select_set(True) # 2.8+

    old_materials.append(obj.data.materials[0])
    for window in bpy.context.window_manager.windows:
      screen = window.screen

    for area in screen.areas:
        if area.type == 'VIEW_3D':
            override = {'window': window, 'screen': screen, 'area': area}
            bpy.ops.screen.screen_full_area(override)
            break

    cont = bpy.context.area.type

    print(str(cont))
    mat = bpy.data.materials.new(name="Material")
    #mat = bpy.data.materials['Material']
    mat.name = 'Material_%d' % i
    while True:
      r, g, b = [random.random() for _ in range(3)]
      if (r, g, b) not in object_colors: break
    object_colors.add((r, g, b))
    mat.diffuse_color = [r, g, b,1]
    obj.cycles_visibility.shadow = False
    mat.shadow_method = 'NONE' # make object shadeless
    obj.data.materials[0] = mat
    obj.active_material.shadow_method = 'NONE'

  # Render the scene
  bpy.ops.render.render(write_still=True)

  # Undo the above; first restore the materials to objects
  # for mat, scene_struct_obj in zip(old_materials, scene_struct['objects']):
  #   obj = bpy.data.objects[scene_struct_obj['scene_object_name']]
  #   obj.data.materials[0] = mat

  # # Move the lights and ground back to layer 0
  # utils.set_layer(bpy.data.objects['Lamp_Key'], 0)
  # utils.set_layer(bpy.data.objects['Lamp_Fill'], 0)
  # utils.set_layer(bpy.data.objects['Lamp_Back'], 0)
  # utils.set_layer(bpy.data.objects['Ground'], 0)

  # # Set the render settings back to what they were
  # render_args.filepath = old_filepath
  # render_args.engine = old_engine
  # render_args.simplify_gpencil_antialiasing = old_use_antialiasing
  # render_args.filter_size = old_filter_size

  return object_colors

def main(args):
  
  
  # Delete previous generated images 
  if(args.delete_previous_images):
    shutil.rmtree(args.output_image_dir, ignore_errors=True)
  
  # Read all 3D models

  models_3d = {}

  categories = []
  for elem in os.listdir(args.models_dir+ "/"):
    if os.path.isdir(args.models_dir+ "/" + elem):
      categories.append(elem)
      
  for category in categories:
    models_3d[category] = []
    for root, dirs, files in os.walk(args.models_dir + "/" + category + "/"):
      for file in files:
          if file.endswith(".obj"):
              model_path = os.path.join(root, file)
              models_3d[category].append(model_path)

  table_models_paths = models_3d["Table"]


  
  with open(args.models_dir+ "/"+'config.json') as json_file:
    config_models = json.load(json_file)
 
  models_type = list(config_models.keys())


  # Generate images with mug, bottle and books
  for i in range(1):
    
    # Initialize scene struct
    scene_struct = {"objects":[], "relationships":[]}

    # Load the main blendfile
    bpy.ops.wm.open_mainfile(filepath='data/base_scene.blend')

    # Add random table
    scene_struct, table_height, table_limit_points = add_random_table(args,scene_struct,table_models_paths)
    
    model1_key = random.choice(models_type)
    model2_key = random.choice(models_type)

    if (config_models[model1_key]["have_inside"] == False or config_models[model2_key]["be_inside"] == False):
      possible_relationships = [rel for rel in relationships if rel!=INSIDE and rel !=INSIDE_UP]
    else:
      possible_relationships = relationships

    relationship = random.choice(possible_relationships)
    scene_struct = add_two_objects(args,scene_struct,[model1_key,model2_key],[random.choice(models_3d[model1_key]),random.choice(models_3d[model2_key])],RIGHT,table_height,table_limit_points)
    render_scene(args,scene_struct,table_height)
    bpy.ops.wm.quit_blender()

    ### !!!!!! Things to do !!!!!!
    # Make 3d models good!
    # Create configuration file for the object type
    #     - # Read JSON file with models configuration
    #     - Define if model can have things inside or not 
    #     - Use that information to generate images and relationships
    #Put object based of the tables size ?????????
    #Check if all object are visible in the image if not, generate again or apply zoom out until its visible
    #############################

  # TASKS


  # Organization task, pencils inside cup, books, pencil outside cup

  # Generate images with cubes and stacking cubes

  # Render scene...


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
  #
  #
  # except FileNotFoundError:
  #   print("File \"" + args.models_dir + "/objects.json" +"\" was not found!")



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
