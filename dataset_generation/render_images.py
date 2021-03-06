import requests
import math, sys, random, argparse, json, os, tempfile
from datetime import datetime as dt
from collections import Counter
#from mathutils.bvhtree import BVHTree
# import bpy, bmesh
import time
from mathutils import Euler
import math
from datetime import datetime
import uuid
import shutil
import operator

# Relationships
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

relationships = [LEFT,RIGHT,ON,FRONT,BEHIND,LEFT_BEHIND,RIGHT_BEHIND,LEFT_FRONT,RIGHT_FRONT,INSIDE,INSIDE_UP]

# Object Position States
UPRIGHT = 'upright'
UPSIDE_DOWN = 'upside_down'
LAYING = 'laying'

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
# parser.add_argument('--properties_json', default='data/properties.json',
#     help="JSON file defining objects, materials, sizes, and colors. " +
#          "The \"colors\" field maps from CLEVR color names to RGB values; " +
#          "The \"sizes\" field maps from CLEVR size names to scalars used to " +
#          "rescale object models; the \"materials\" and \"shapes\" fields map " +
#          "from CLEVR material and shape names to .blend files in the " +
#          "--object_material_dir and --shape_dir directories respectively.")
parser.add_argument('--models_dir', default='data/models',
    help="Directory where .obj files for object models are stored")


# Settings for objects
# parser.add_argument('--min_objects', default=3, type=int,
#     help="The minimum number of objects to place in each scene")
# parser.add_argument('--max_objects', default=10, type=int,
#     help="The maximum number of objects to place in each scene")
# parser.add_argument('--min_dist', default=0.25, type=float,
#     help="The minimum allowed distance between object centers")
# parser.add_argument('--margin', default=0.4, type=float,
#     help="Along all cardinal directions (left, right, front, back), all " +
#          "objects will be at least this distance apart. This makes resolving " +
#          "spatial relationships slightly less ambiguous.")
# parser.add_argument('--min_pixels_per_object', default=200, type=int,
#     help="All objects will have at least this many visible pixels in the " +
#          "final rendered images; this ensures that no objects are fully " +
#          "occluded by other objects.")
# parser.add_argument('--max_retries', default=50, type=int,
#     help="The number of times to try placing an object before giving up and " +
#          "re-placing all objects in the scene.")
parser.add_argument('--border_limit', default=4, type=float,
    help="The number to change the sensitivy of the relatioships. Higher number means the single "+
    "relationships are more narrow")
parser.add_argument('--radius_near_far', default=2, type=float,
    help="Limit of the radius of what is considered \"near\" or \"far\" from an object")

# Output settings
# parser.add_argument('--start_idx', default=0, type=int,
#     help="The index at which to start for numbering rendered images. Setting " +
#          "this to non-zero values allows you to distribute rendering across " +
#          "multiple machines and recombine the results later.")
parser.add_argument('--num_images', default=5, type=int,
    help="The number of images to render")
parser.add_argument('--filename_prefix', default='CLEVR',
    help="This prefix will be prepended to the rendered images and JSON files")
# parser.add_argument('--split', default='new',
#     help="Name of the split for which we are rendering. This will be added to " +
#          "the names of rendered images, and will also be stored in the JSON " +
#          "scene structure for each image.")
parser.add_argument('--output_image_dir', default='../output/images/',
    help="The directory where output images will be stored. It will be " +
         "created if it does not exist.")
parser.add_argument('--delete_previous_images', default=False,
    help="Delete previous generated images from the directory where output images will be stored.")
# parser.add_argument('--output_scene_dir', default='../output/scenes/',
#     help="The directory where output JSON scene structures will be stored. " +
#          "It will be created if it does not exist.")
# parser.add_argument('--output_scene_file', default='../output/CLEVR_scenes.json',
#     help="Path to write a single JSON file containing all scene information")
# parser.add_argument('--output_blend_dir', default='output/blendfiles',
#     help="The directory where blender scene files will be stored, if the " +
#          "user requested that these files be saved using the " +
#          "--save_blendfiles flag; in this case it will be created if it does " +
#          "not already exist.")
# parser.add_argument('--save_blendfiles', type=int, default=0,
#     help="Setting --save_blendfiles 1 will cause the blender scene file for " +
#          "each generated image to be stored in the directory specified by " +
#          "the --output_blend_dir flag. These files are not saved by default " +
#          "because they take up ~5-10MB each.")
# parser.add_argument('--version', default='1.0',
#     help="String to store in the \"version\" field of the generated JSON file")
# parser.add_argument('--license',
#     default="Creative Commons Attribution (CC-BY 4.0)",
#     help="String to store in the \"license\" field of the generated JSON file")
# parser.add_argument('--date', default=dt.today().strftime("%m/%d/%Y"),
#     help="String to store in the \"date\" field of the generated JSON file; " +
#          "defaults to today's date")

# Rendering options
parser.add_argument('--use_gpu', default=0, type=int,
    help="Setting --use_gpu 1 enables GPU-accelerated rendering using CUDA. " +
         "You must have an NVIDIA GPU with the CUDA toolkit installed for " +
         "to work.")
parser.add_argument('--width', default=300, type=int,
    help="The width (in pixels) for the rendered images")
parser.add_argument('--height', default=300, type=int,
    help="The height (in pixels) for the rendered images")
parser.add_argument('--key_light_jitter', default=1.0, type=float,
    help="The magnitude of random jitter to add to the key light position.")
parser.add_argument('--fill_light_jitter', default=1.0, type=float,
    help="The magnitude of random jitter to add to the fill light position.")
parser.add_argument('--back_light_jitter', default=1.0, type=float,
    help="The magnitude of random jitter to add to the back light position.")

parser.add_argument('--key_light_power', default=[200, 500], type=float,
    help="The magnitude of random power range to add to the key light.")
parser.add_argument('--fill_light_power', default=[200, 500], type=float,
    help="The magnitude of random power to add to the fill light.")
parser.add_argument('--back_light_power', default=[200, 500], type=float,
    help="The magnitude of random power range to add to the back light.")
parser.add_argument('--sunlight_power', default=[0, 0.3], type=float,
    help="The magnitude of random power range to add to the sun light.")

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
  render_args.engine = "CYCLES"
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
      cycles_preferences = bpy.context.preferences.addons['cycles'].preferences
      bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'
      bpy.context.preferences.addons['cycles'].preferences.compute_device = 'CUDA_MULTI_2'
      cuda_devices, opencl_devices = cycles_preferences.get_devices()
      gpu_device = None
      print("devices: ", cuda_devices, opencl_devices )
      for device in cycles_preferences.devices:
          device.use = False #reset all other devices
          if device.type == "CUDA" and device in cuda_devices:
              gpu_device = device

      bpy.context.scene.cycles.device = "GPU"
      bpy.context.preferences.addons["cycles"].preferences.compute_device_type = gpu_device.type
      gpu_device.use = True

  # Some CYCLES-specific stuff
  bpy.data.worlds['World'].cycles.sample_as_light = True
  bpy.context.scene.cycles.blur_glossy = 2.0
  bpy.context.scene.cycles.samples = args.render_num_samples
  bpy.context.scene.cycles.transparent_min_bounces = args.render_min_bounces
  bpy.context.scene.cycles.transparent_max_bounces = args.render_max_bounces



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

  # Add random rotation to the camera
  #bpy.data.objects['Camera'].location.x +=  #5*rand(args.camera_jitter)
  #delta_rotation_euler =  Euler((0,0, math.radians(rand_rotation())), 'XYZ')

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
  
  # Random lightning conditions
  sum_value = random.uniform(0.5,10) 
  lamp_objects = [o for o in bpy.data.objects
                if o.type == 'LIGHT']
  r = [random.random() for i in range(1,5)] # four values
  s = sum(r)
  r = [ (i/s)*sum_value for i in r ]
  for i, lamp in enumerate(lamp_objects):
    lamp.data.use_nodes = True
    lamp.data.node_tree.nodes['Emission'].inputs['Strength'].default_value = r[i]
    bpy.context.view_layer.update() 

  
  # Get bounding boxes of all objects
  for obj_struct in scene_struct['objects']:
    bbverts = [bpy.data.objects[obj_struct['scene_object_name']].matrix_world@Vector(bbvert) for bbvert in bpy.data.objects[obj_struct['scene_object_name']].bound_box]
    bbox_3d_obj = [utils.get_camera_coords(camera,bbvert) for bbvert in bbverts]
    obj_struct["3d_bbox"] = bbox_3d_obj
    all_x = [point[0] for point in bbox_3d_obj]
    all_y = [point[1] for point in bbox_3d_obj]

    # We only need bottom-left (top-left visually) and top-right (bottom-right visually)
    
    # (min(all_x),min(all_y)),(max(all_x),max(all_y))
    
    x0 = min(all_x)
    y0 = min(all_y)
    x1 = max(all_x)
    y1 = max(all_y)
    obj_struct["2d_bbox"] = [x0,y0,x1,y1] # this contain negative values in the bounding boxes, useful to check the object visibility

  scene_struct['image_filename'] =  os.path.basename(output_image_id+".png")
  scene_struct['relationships'] = compute_all_relationships(args,scene_struct)

  # Check if objects are visible in the picture?
  if check_visibility(args, scene_struct,100) is False:
    return False

  # Clean the negative values of the bounding boxes
  for obj_struct in scene_struct['objects']:
    x0 = obj_struct["2d_bbox"][0] if obj_struct["2d_bbox"][0] > 0 else 0 
    y0 = obj_struct["2d_bbox"][1] if obj_struct["2d_bbox"][1] > 0 else 0 
    x1 = obj_struct["2d_bbox"][2] if obj_struct["2d_bbox"][2] < args.width else args.width
    y1 = obj_struct["2d_bbox"][3] if obj_struct["2d_bbox"][3] < args.height else args.height
    obj_struct["2d_bbox"] = [x0,y0,x1,y1]


  if(objects_overlap(scene_struct,max_percentage = 10)):
    return False



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
  
  return True

def add_two_objects(args,scene_struct, objects_category, objects_path, relationship,table_height,table_limit_points):
  
  """
  Add two objects to the current blender scene
  """

  # Get the path of the objects to add to the scene
  obj1_path = objects_path[0] # args.models_dir + "/" + objects_category[0] + "/" +  objects_id[0]  + "/models/model_normalized.obj"
  obj2_path =  objects_path[1] # args.models_dir + "/" + objects_category[1] + "/" +  objects_id[1]  + "/models/model_normalized.obj"
  
  scene_objects = []

  # Import Object 1 in the scene in the center position with random z orientation
  if obj1_path.endswith(".obj"):
    imported_object = bpy.ops.import_scene.obj(filepath=obj1_path)
    selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
    obj_object1 = selected_objects[0] 
  elif obj1_path.endswith(".blend"):
    obj_object1 = append_object_to_scene(filepath=obj1_path)
  obj_object1.name = objects_category[0] + "_" + relationship+ "_" + str(datetime.now())
  obj_object1.delta_rotation_euler =  Euler((obj_object1.delta_rotation_euler[0],obj_object1.delta_rotation_euler[1], math.radians(rand_rotation())), 'XYZ')
  scene_objects.append(obj_object1)

  # Import Object 2 in the scene in the center position with random z orientation
  if obj2_path.endswith(".obj"):
    imported_object = bpy.ops.import_scene.obj(filepath=obj2_path)
    selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
    obj_object2 = selected_objects[0] 
  elif obj2_path.endswith(".blend"):
    obj_object2 = append_object_to_scene(filepath=obj2_path)
  obj_object2.name = objects_category[1] + "_" +relationship + "_" +  str(datetime.now())
  obj_object2.delta_rotation_euler =  Euler((obj_object2.delta_rotation_euler[0],obj_object2.delta_rotation_euler[1], math.radians(rand_rotation())), 'XYZ')
  scene_objects.append(obj_object2)

  bpy.context.view_layer.update() 
  


  bbverts_obj1 = [obj_object1.matrix_world@Vector(bbvert) for bbvert in obj_object1.bound_box]
  bbverts_obj2 = [obj_object2.matrix_world@Vector(bbvert) for bbvert in obj_object2.bound_box]
  min_z_obj1 = min([vec[2] for vec in bbverts_obj1])
  min_z_obj2 = min([vec[2] for vec in bbverts_obj2])

  #Put objects in the table
  obj_object1.location.z += -min_z_obj1 + table_height
  obj_object2.location.z += -min_z_obj2 + table_height

  bpy.context.view_layer.update() 
  
  bbverts_obj1 = [obj_object1.matrix_world@Vector(bbvert) for bbvert in obj_object1.bound_box]
  bbverts_obj2 = [obj_object2.matrix_world@Vector(bbvert) for bbvert in obj_object2.bound_box]

  # Get table limits with the object size so the object doesn't stay ouside of the table
  table_max_x = max([point[0]for point in table_limit_points]) - obj_object2.dimensions.x/2
  table_min_x = min([point[0]for point in table_limit_points]) + obj_object2.dimensions.x/2
  table_max_y = max([point[1]for point in table_limit_points]) - obj_object2.dimensions.y/2
  table_min_y = min([point[1]for point in table_limit_points]) + obj_object2.dimensions.y/2



  #  Dimensions of objects after rotation
  obj1_dimension_x = abs(max(bbvert [0] for bbvert in bbverts_obj1)-min(bbvert [0] for bbvert in bbverts_obj1))
  obj1_dimension_y = abs(max(bbvert [1] for bbvert in bbverts_obj1)-min(bbvert [1] for bbvert in bbverts_obj1)) 
  obj1_dimension_z = abs(max(bbvert [2] for bbvert in bbverts_obj1)-min(bbvert [2] for bbvert in bbverts_obj1))
  obj2_dimension_x = abs(max(bbvert [0] for bbvert in bbverts_obj2)-min(bbvert [0] for bbvert in bbverts_obj2)) 
  obj2_dimension_y = abs(max(bbvert [1] for bbvert in bbverts_obj2)-min(bbvert [1] for bbvert in bbverts_obj2))
  obj2_dimension_z = abs(max(bbvert [2] for bbvert in bbverts_obj2)-min(bbvert [2] for bbvert in bbverts_obj2))

  border_limit = args.border_limit
  inside_table = False

  # Minimal distance between the two objects
  min_dist_x = (obj1_dimension_x+ obj2_dimension_x)/2 # Minimum distance between two objects in X
  min_dist_y = (obj1_dimension_y + obj2_dimension_y)/2 # Minimum distance between two objects in Y

  # Set position states for the objects
  obj1_state = UPRIGHT
  obj2_state = UPRIGHT

  # Apply the relationshiop to the second object
  out_of_table = 0
  while(inside_table==False):
    if(relationship==LEFT):
      y_pos = random.uniform(-min_dist_y, table_min_y)
      x_pos =  random.uniform(y_pos/border_limit, -y_pos/border_limit)
      obj_object2.location.y = y_pos
      obj_object2.location.x = x_pos
    elif(relationship==RIGHT):
      y_pos = random.uniform(min_dist_y,table_max_y)
      x_pos =  random.uniform(-y_pos/border_limit, y_pos/border_limit)
      obj_object2.location.y = y_pos
      obj_object2.location.x = x_pos
    elif(relationship==FRONT):
      x_pos = random.uniform(min_dist_y, table_max_x)
      y_pos = random.uniform(-x_pos/border_limit, x_pos/border_limit)
      obj_object2.location.y = y_pos
      obj_object2.location.x = x_pos
    elif(relationship==BEHIND):
      x_pos =  random.uniform(-min_dist_y, table_min_x)
      y_pos =  random.uniform(x_pos/border_limit, -x_pos/border_limit)
      obj_object2.location.y = y_pos
      obj_object2.location.x = x_pos
    elif(relationship==LEFT_BEHIND):
      y_pos = random.uniform(-min_dist_y, table_min_y)
      x_pos = random.uniform(min(y_pos*border_limit,-min_dist_x), y_pos/border_limit)
      obj_object2.location.y = y_pos
      obj_object2.location.x = x_pos
    elif(relationship==RIGHT_BEHIND):
      y_pos = random.uniform(min_dist_y, table_max_y)
      x_pos =  random.uniform(min(-y_pos/border_limit,-min_dist_x), -y_pos*border_limit)
      obj_object2.location.y = y_pos
      obj_object2.location.x = x_pos
    elif(relationship==LEFT_FRONT):
      y_pos = random.uniform(-min_dist_y, table_min_y)
      x_pos =  random.uniform(max(-y_pos/border_limit,min_dist_x), -y_pos*border_limit)
      obj_object2.location.y = y_pos
      obj_object2.location.x = x_pos
    elif(relationship==RIGHT_FRONT):
      y_pos = random.uniform(min_dist_y, random.random())
      x_pos =  random.uniform(max(y_pos/border_limit,min_dist_x), y_pos*border_limit)
      obj_object2.location.y = y_pos
      obj_object2.location.x = x_pos
    elif(relationship==ON):
      x_pos = 0
      y_pos = 0 
      #obj_object2.location.y = y_pos
      #obj_object2.location.x = x_pos
      obj_object2.location.z += obj1_dimension_z
    elif(relationship==UNDER):
      x_pos = 0
      y_pos = 0 
      #obj_object2.location.y = y_pos
      #obj_object2.location.x = x_pos
      obj_object1.location.z += obj2_dimension_z
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
      obj_object2.delta_rotation_euler =  Euler((obj_object2.delta_rotation_euler[0],3.14, obj_object2.delta_rotation_euler[2]), 'XYZ')
      bpy.context.view_layer.update() 
      bbverts_obj1 = [obj_object1.matrix_world@Vector(bbvert) for bbvert in obj_object1.bound_box]
      max_z_obj1 = max([vec[2] for vec in bbverts_obj1])
      bbverts_obj2 = [obj_object2.matrix_world@Vector(bbvert) for bbvert in obj_object2.bound_box]
      max_z_obj2 = max([vec[2] for vec in bbverts_obj2])
      obj_object2.location.z = max_z_obj1-(max_z_obj2 - obj_object2.location.z)+0.05
      obj2_state = UPSIDE_DOWN
    
    all_x = [point[0] for point in table_limit_points]
    all_y = [point[1] for point in table_limit_points]

    bpy.context.view_layer.update() 
  
    # Check if the 2nd object is inside the table
    if (obj_object2.location.x<=table_max_x and obj_object2.location.x>=table_min_x and obj_object2.location.y<=table_max_y and obj_object2.location.y>table_min_y):
      inside_table = True
    if out_of_table > 10:
      return False
    out_of_table+=1

  bpy.context.view_layer.update()

  ## Override context due to blender 
  for window in bpy.context.window_manager.windows:
    screen = window.screen

    for area in screen.areas:
        if area.type == 'VIEW_3D':
            override = {'window': window, 'screen': screen, 'area': area}
            bpy.ops.screen.screen_full_area(override)
            break
        
      

  cat_apenddix1 = ''
  cat_apenddix2 = ''

  if (obj1_state == UPSIDE_DOWN and objects_category[0] == 'Mug'):
    cat_apenddix1 = '_' + UPSIDE_DOWN

  if (obj2_state == UPSIDE_DOWN and objects_category[1] == 'Mug'):
    cat_apenddix2 = '_' + UPSIDE_DOWN

  obj1_metadata = {
    'id':str(uuid.uuid1()),
    'scene_object_name':obj_object1.name,
    'category': objects_category[0]+ cat_apenddix1,
    'state':obj1_state,
    '3d_bbox': None, # It has to be calculated later with the camera information
    'model_path':obj1_path
  }

  obj2_metadata = {
    'id':str(uuid.uuid1()),
    'scene_object_name':obj_object2.name,
    'category': objects_category[1] + cat_apenddix2,
    'state':obj2_state,
    '3d_bbox': None, # It has to be calculated later with the camera information
    'model_path':obj2_path
  }
  scene_struct['objects'].extend([obj1_metadata,obj2_metadata])
  # Keep track of the desired relationships
  scene_struct['desired_relationships'].append({"subject":obj1_metadata["id"],
                          "object":obj2_metadata["id"],
                          "predicate":relationship
                        })
  scene_struct['relationships'] = compute_all_relationships(args,scene_struct)
  return scene_struct

def add_object_with_relationship(args,scene_struct,reference_object ,object_category, object_path, relationship,table_height,table_limit_points):
  
  """
  Add two objects to the current blender scene
  """
  bpy.context.view_layer.update()

  # Get the path of the objects to add to the scene
  obj2_path =  object_path # args.models_dir + "/" + objects_category[1] + "/" +  objects_id[1]  + "/models/model_normalized.obj"
  
  scene_objects = []

  # Object 1 is the reference object
  obj_object1 = bpy.context.scene.objects[reference_object['scene_object_name']]


  # Import Object 2 in the scene in the center position with random z orientation
  if obj2_path.endswith(".obj"):
    imported_object = bpy.ops.import_scene.obj(filepath=obj2_path)
    selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
    obj_object2 = selected_objects[0] 
  elif obj2_path.endswith(".blend"):
    obj_object2 = append_object_to_scene(filepath=obj2_path)
  obj_object2.name = object_category + "_" +relationship + "_" +  str(datetime.now())
  obj_object2.delta_rotation_euler =  Euler((obj_object2.delta_rotation_euler[0],obj_object2.delta_rotation_euler[1], math.radians(rand_rotation())), 'XYZ')
  scene_objects.append(obj_object2)


  
 

  bpy.context.view_layer.update()
   

  bbverts_obj1 = [obj_object1.matrix_world@Vector(bbvert) for bbvert in obj_object1.bound_box]
  bbverts_obj2 = [obj_object2.matrix_world@Vector(bbvert) for bbvert in obj_object2.bound_box]
  min_z_obj2 = min([vec[2] for vec in bbverts_obj2])

  #Put objects in the table
  obj_object2.location.z += -min_z_obj2 + table_height
  bpy.context.view_layer.update() 
  
  bbverts_obj1 = [obj_object1.matrix_world@Vector(bbvert) for bbvert in obj_object1.bound_box]
  bbverts_obj2 = [obj_object2.matrix_world@Vector(bbvert) for bbvert in obj_object2.bound_box]
  

  # Get table limits with the object size so the object doesn't stay ouside of the table
  table_max_x = max([point[0]for point in table_limit_points]) - obj_object2.dimensions.x/2
  table_min_x = min([point[0]for point in table_limit_points]) + obj_object2.dimensions.x/2
  table_max_y = max([point[1]for point in table_limit_points]) - obj_object2.dimensions.y/2
  table_min_y = min([point[1]for point in table_limit_points]) + obj_object2.dimensions.y/2



  #  Dimensions of objects after rotation
  obj1_dimension_x = abs(max(bbvert [0] for bbvert in bbverts_obj1)-min(bbvert [0] for bbvert in bbverts_obj1))
  obj1_dimension_y = abs(max(bbvert [1] for bbvert in bbverts_obj1)-min(bbvert [1] for bbvert in bbverts_obj1)) 
  obj1_dimension_z = abs(max(bbvert [2] for bbvert in bbverts_obj1)-min(bbvert [2] for bbvert in bbverts_obj1))
  obj2_dimension_x = abs(max(bbvert [0] for bbvert in bbverts_obj2)-min(bbvert [0] for bbvert in bbverts_obj2)) 
  obj2_dimension_y = abs(max(bbvert [1] for bbvert in bbverts_obj2)-min(bbvert [1] for bbvert in bbverts_obj2))
  obj2_dimension_z = abs(max(bbvert [2] for bbvert in bbverts_obj2)-min(bbvert [2] for bbvert in bbverts_obj2))

  max_z_obj1 = max(bbvert [2] for bbvert in bbverts_obj1)

  border_limit = args.border_limit
  inside_table = False

  # Minimal distance between the two objects
  min_dist_x = (obj1_dimension_x+ obj2_dimension_x)/2 # Minimum distance between two objects in X
  min_dist_y = (obj1_dimension_y + obj2_dimension_y)/2 # Minimum distance between two objects in Y

  # Set position states for the object
  obj2_state = UPRIGHT

  out_of_table = 0
  # Apply the relationshiop to the second object
  while(inside_table==False):
    if(relationship==LEFT):
      y_pos = random.uniform(-min_dist_y, table_min_y)
      x_pos =  random.uniform(y_pos/border_limit, -y_pos/border_limit)
      obj_object2.location.y = y_pos
      obj_object2.location.x = x_pos
    elif(relationship==RIGHT):
      y_pos = random.uniform(min_dist_y,table_max_y)
      x_pos =  random.uniform(-y_pos/border_limit, y_pos/border_limit)
      obj_object2.location.y = y_pos
      obj_object2.location.x = x_pos
    elif(relationship==FRONT):
      x_pos = random.uniform(min_dist_y, table_max_x)
      y_pos = random.uniform(-x_pos/border_limit, x_pos/border_limit)
      obj_object2.location.y = y_pos
      obj_object2.location.x = x_pos
    elif(relationship==BEHIND):
      x_pos =  random.uniform(-min_dist_y, table_min_x)
      y_pos =  random.uniform(x_pos/border_limit, -x_pos/border_limit)
      obj_object2.location.y = y_pos
      obj_object2.location.x = x_pos
    elif(relationship==LEFT_BEHIND):
      y_pos = random.uniform(-min_dist_y, table_min_y)
      x_pos = random.uniform(min(y_pos*border_limit,-min_dist_x), y_pos/border_limit)
      obj_object2.location.y = y_pos
      obj_object2.location.x = x_pos
    elif(relationship==RIGHT_BEHIND):
      y_pos = random.uniform(min_dist_y, table_max_y)
      x_pos =  random.uniform(min(-y_pos/border_limit,-min_dist_x), -y_pos*border_limit)
      obj_object2.location.y = y_pos
      obj_object2.location.x = x_pos
    elif(relationship==LEFT_FRONT):
      y_pos = random.uniform(-min_dist_y, table_min_y)
      x_pos =  random.uniform(max(-y_pos/border_limit,min_dist_x), -y_pos*border_limit)
      obj_object2.location.y = y_pos
      obj_object2.location.x = x_pos
    elif(relationship==RIGHT_FRONT):
      y_pos = random.uniform(min_dist_y, random.random())
      x_pos =  random.uniform(max(y_pos/border_limit,min_dist_x), y_pos*border_limit)
      obj_object2.location.y = y_pos
      obj_object2.location.x = x_pos
    elif(relationship==ON):
      x_pos = 0
      y_pos = 0 
      #obj_object2.location.y = y_pos
      #obj_object2.location.x = x_pos
      bpy.context.view_layer.update() 
      obj_object2.location.z = max_z_obj1 + abs(min_z_obj2)
    elif(relationship==UNDER):
      x_pos = 0
      y_pos = 0 
      #obj_object2.location.y = y_pos
      #obj_object2.location.x = x_pos
      obj_object1.location.z += obj2_dimension_z
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
      obj_object2.delta_rotation_euler =  Euler((obj_object2.delta_rotation_euler[0],3.14, obj_object2.delta_rotation_euler[2]), 'XYZ')
      bpy.context.view_layer.update() 
      bbverts_obj1 = [obj_object1.matrix_world@Vector(bbvert) for bbvert in obj_object1.bound_box]
      max_z_obj1 = max([vec[2] for vec in bbverts_obj1])
      bbverts_obj2 = [obj_object2.matrix_world@Vector(bbvert) for bbvert in obj_object2.bound_box]
      max_z_obj2 = max([vec[2] for vec in bbverts_obj2])
      obj_object2.location.z = max_z_obj1-(max_z_obj2 - obj_object2.location.z)+0.05
      obj2_state = UPSIDE_DOWN
    
    all_x = [point[0] for point in table_limit_points]
    all_y = [point[1] for point in table_limit_points]

    bpy.context.view_layer.update() 
    
    # Check if the 2nd object is inside the table
    if (obj_object2.location.x<=table_max_x and obj_object2.location.x>=table_min_x and obj_object2.location.y<=table_max_y and obj_object2.location.y>table_min_y):
      inside_table = True
    if out_of_table > 10:
      return False
    out_of_table+=1

  bpy.context.view_layer.update()

  ## Override context due to blender 
  for window in bpy.context.window_manager.windows:
    screen = window.screen

    for area in screen.areas:
        if area.type == 'VIEW_3D':
            override = {'window': window, 'screen': screen, 'area': area}
            bpy.ops.screen.screen_full_area(override)
            break

  cat_appendix = ''
  if (obj2_state == UPSIDE_DOWN and object_category == 'Mug'):
    cat_appendix = '_' + UPSIDE_DOWN

  obj2_metadata = {
    'id':str(uuid.uuid1()),
    'scene_object_name':obj_object2.name,
    'category': object_category + cat_appendix,
    'state':obj2_state,
    '3d_bbox': None, # It has to be calculated later with the camera information
    'model_path':obj2_path
  }
  scene_struct['objects'].extend([obj2_metadata])
  # Keep track of the desired relationships
  scene_struct['desired_relationships'].append({"object":reference_object["id"],
                          "subject":obj2_metadata["id"],
                          "predicate":relationship
                        })
  scene_struct['relationships'] = compute_all_relationships(args,scene_struct)
  return scene_struct

def compute_all_relationships(args,scene_struct):
  """ Computes relationships between all pairs of objects in the scene."""
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
     

      # INSIDE
      if(min_y_obj1>min_y_obj2 and max_y_obj1<max_y_obj2 and min_x_obj1>min_x_obj2 and max_x_obj1<max_x_obj2 
      and (max_z_obj2-min_z_obj2) + (max_z_obj1-min_z_obj1) > 0.0001 + abs(max(max_z_obj1,max_z_obj2) - min(min_z_obj1,min_z_obj2)) and
      obj1_struct["category"] !='Table' and obj2_struct["category"]!='Table' ): # height of both objects must be higher that the distances of extremes of both objects 
        all_relationships.extend([{"subject":obj1_struct["id"],
                      "object":obj2_struct["id"],
                      "predicate":INSIDE
        }])
        if(abs(max_z_obj2-max_z_obj1)<0.1):
           all_relationships.append({"subject":obj2_struct["id"],
                      "object":obj1_struct["id"],
                      "predicate":ON
          })
      # ON
      elif((abs(min_z_obj1 - max_z_obj2) <= 0.001) 
        and (max_z_obj2-min_z_obj2) + (max_z_obj1-min_z_obj1) - abs(max(max_z_obj1,max_z_obj2) - min(min_z_obj1,min_z_obj2)) <0.001 ):
        all_relationships.extend([{"subject":obj1_struct["id"],
                        "object":obj2_struct["id"],
                        "predicate":ON
                        }])
      # UNDER
      elif(abs(min_z_obj2 - max_z_obj1 )<= 0.001):
        all_relationships.extend([{"subject":obj1_struct["id"],
                        "object":obj2_struct["id"],
                        "predicate":UNDER
        }])

      
       

      if(obj1_struct["category"] !='Table' and obj2_struct["category"]!='Table' ):
        # NEAR
        if(math.sqrt(pow(obj1.location.x-obj2.location.x,2) + pow(obj1.location.y-obj2.location.y,2) + pow(obj1.location.z-obj2.location.z,2) ) <= args.radius_near_far ):
          all_relationships.extend([{"subject":obj1_struct["id"],
                        "object":obj2_struct["id"],
                        "predicate":NEAR
        }])

        # FAR
        elif(math.sqrt(pow(obj1.location.x-obj2.location.x,2) + pow(obj1.location.y-obj2.location.y,2) + pow(obj1.location.z-obj2.location.z,2) ) > args.radius_near_far ):
          all_relationships.extend([{"subject":obj1_struct["id"],
                        "object":obj2_struct["id"],
                        "predicate":FAR
        }])

        # BEHIND
        if(obj1.location.y-obj2.location.y >= (obj1.location.x-obj2.location.x)/args.border_limit and
          obj1.location.y-obj2.location.y <= -(obj1.location.x-obj2.location.x)/args.border_limit and max_x_obj1<=min_x_obj2):
                all_relationships.extend([{"subject":obj1_struct["id"],
                          "object":obj2_struct["id"],
                          "predicate":BEHIND
                        }])
        # FRONT OF
        elif(obj1.location.y-obj2.location.y <= (obj1.location.x-obj2.location.x)/args.border_limit and
          obj1.location.y-obj2.location.y >= -(obj1.location.x-obj2.location.x)/args.border_limit and min_x_obj1 >= max_x_obj2):
          all_relationships.extend( [{"subject":obj1_struct["id"],
                          "object":obj2_struct["id"],
                          "predicate":FRONT
                        }])
        # LEFT
        elif(obj1.location.y-obj2.location.y <= -abs(obj1.location.x-obj2.location.x)*args.border_limit and max_y_obj1<=min_y_obj2):
          all_relationships.extend([{"subject":obj1_struct["id"],
                          "object":obj2_struct["id"],
                          "predicate":LEFT
                        }])
        # RIGHT
        elif(obj1.location.y-obj2.location.y >= abs(obj1.location.x-obj2.location.x)*args.border_limit and min_y_obj1>=max_y_obj2):
          all_relationships.extend([{"subject":obj1_struct["id"],
                          "object":obj2_struct["id"],
                          "predicate":RIGHT
                        }])
        # RIGHT_BEHIND
        elif(obj1.location.y-obj2.location.y >=  -(obj1.location.x-obj2.location.x)/args.border_limit and
          obj1.location.y-obj2.location.y <= -args.border_limit*(obj1.location.x-obj2.location.x) 
          and min_y_obj1>=max_y_obj2 and max_x_obj1<=min_x_obj2 ):
          all_relationships.extend([{"subject":obj1_struct["id"],
                          "object":obj2_struct["id"],
                          "predicate":RIGHT_BEHIND
                        }])
        # LEFT_BEHIND
        elif(obj1.location.y-obj2.location.y >= args.border_limit*(obj1.location.x-obj2.location.x) and
          obj1.location.y-obj2.location.y <= (obj1.location.x-obj2.location.x)/args.border_limit and max_y_obj1<=min_y_obj2 and max_x_obj1<=min_x_obj2):
          all_relationships.extend([{"subject":obj1_struct["id"],
                          "object":obj2_struct["id"],
                          "predicate":LEFT_BEHIND
                        }])
        # RIGHT_FRONT
        elif(obj1.location.y-obj2.location.y >= (obj1.location.x-obj2.location.x)/args.border_limit and
          obj1.location.y-obj2.location.y <= (obj1.location.x-obj2.location.x)*args.border_limit and min_y_obj1>=max_y_obj2 and min_x_obj1 >= max_x_obj2):
          all_relationships.extend([{"subject":obj1_struct["id"],
                          "object":obj2_struct["id"],
                          "predicate":RIGHT_FRONT
                        }])
        # LEFT_FRONT
        elif(obj1.location.y-obj2.location.y >= -args.border_limit*(obj1.location.x-obj2.location.x)and
          obj1.location.y-obj2.location.y <= -(obj1.location.x-obj2.location.x)/args.border_limit and max_y_obj1<=min_y_obj2 and min_x_obj1 >= max_x_obj2):
          all_relationships.extend([{"subject":obj1_struct["id"],
                          "object":obj2_struct["id"],
                          "predicate":LEFT_FRONT
                        }])

  return all_relationships

def objects_overlap(scene_struct,max_percentage):
  """ Calculates the percentange of object intersecting other objects
  Returns true if there are objects intersecting more than the percentage defined.
  Return false if the objects intersect less than the percentage defined"""
  scene_objects = []
  for obj in scene_struct['objects']:
    scene_objects.append( bpy.context.scene.objects[obj['scene_object_name']])
  
  for obj1 in scene_objects:
    for obj2 in scene_objects:
      if obj1 == obj2:
        continue
      obj1_struct = [obj for obj in scene_struct['objects'] if obj['scene_object_name'] ==  obj1.name][0]
      obj2_struct = [obj for obj in scene_struct['objects'] if obj['scene_object_name'] ==  obj2.name][0]

      obj1_bbox = [obj1.matrix_world@Vector(bbvert) for bbvert in obj1.bound_box]
      obj2_bbox = [obj2.matrix_world@Vector(bbvert) for bbvert in obj2.bound_box]
      left_bottom1 = (max([p[0] for p in obj1_bbox]),min([p[1] for p in obj1_bbox]),min([p[2] for p in obj1_bbox]))
      top_right1 = (min([p[0] for p in obj1_bbox]),max([p[1] for p in obj1_bbox]),max([p[2] for p in obj1_bbox]))

      left_bottom2 = (max([p[0] for p in obj2_bbox]),min([p[1] for p in obj2_bbox]),min([p[2] for p in obj2_bbox]))
      top_right2 = (min([p[0] for p in obj2_bbox]),max([p[1] for p in obj2_bbox]),max([p[2] for p in obj2_bbox]))
      
      # If the objects are supposed to be inside each other the percentage is 50%
      for rel in scene_struct['desired_relationships']:
        if (rel['subject'] == obj1_struct['id'] and rel['object']==obj2_struct['id'] 
        and (rel['predicate'] == INSIDE_UP or rel['predicate'] == INSIDE)):
          max_percentage = 50

      x_dist = min(left_bottom1[0], left_bottom1[0])- max(top_right1[0], top_right1[0])
      y_dist =min(top_right1[1], top_right2[1])- max(left_bottom1[1], left_bottom2[1])
      z_dist = min(top_right1[2], top_right2[2])-max(left_bottom1[2], left_bottom2[2])
      if( x_dist > 0 and y_dist > 0 and z_dist > 0 ):
        inters_volume = x_dist * y_dist * z_dist
      else:
        inters_volume = 0
      
      obj1_vol = abs(top_right1[0]-left_bottom1[0]) * abs(top_right1[1]-left_bottom1[1]) * abs(top_right1[2]-left_bottom1[2])
      obj2_vol = abs(top_right2[0]-left_bottom2[0]) * abs(top_right2[1]-left_bottom2[1]) * abs(top_right2[2]-left_bottom2[2])
      
      percentage = (inters_volume/(obj1_vol + obj2_vol))*100
      if (inters_volume == 0):
        print(obj1.name + " doesn't intersect " + obj2.name)
      else:
        print(str(percentage) + "%  : "+ obj1.name + "intersect " + obj2.name)
      if percentage > max_percentage:
        return True
      
  return False
      
      # percentage_visible = (inters_area/object_area)*100
      # print(obj['category'] +" is "+ str(percentage_visible) + "%% in the image")
      # if (percentage_visible<min_visible_percentage_per_object):
      #   print("Objects are not visible!")
      #   return False

def add_random_table(args, scene_struct, table_model_paths):
 
  # Get the path of the objects to add to the scene
  obj_path = random.choice(table_model_paths)
  

  # Import Object 1 in the scene in the center position with random z orientation
  imported_object = bpy.ops.import_scene.obj(filepath=obj_path)
  selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
  obj_object = selected_objects[0] 
  obj_object.name = "Table"
  #obj_object.delta_rotation_euler =  Euler((0,0, math.radians(rand_rotation())), 'XYZ')
  
  # Change table scale
  obj_object.scale.x=10
  obj_object.scale.y=10
  obj_object.scale.z=10
  bpy.context.view_layer.update() 

  # Change z location to put table in the floor
  
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
    'model_path':obj_path
  }
  scene_struct["objects"].append(obj_metadata) 

  table_points = []
  all_y = [point[1] for point in bbverts_obj]
  all_z = [point[2] for point in bbverts_obj]
 
  table_limit_points = [point[1] for point in list( sorted(zip(all_z, bbverts_obj), reverse=True)[:4])]


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

def check_visibility(args, scene_struct, min_visible_percentage_per_object):
  """
  Check whether all objects in the scene have some minimum number of visible
  pixels; to accomplish this we verify if all the vertices of the
  object bounding box are inside of the rendered image or not
  Returns True if all objects are visible and False otherwise.
  """
  width = args.width
  height = args.height
  for obj in scene_struct["objects"]:

    if obj['category'] is "Table":
      continue
    obj_bbox = obj['2d_bbox']
    object_area = abs(obj_bbox[0]- obj_bbox[2]) * abs(obj_bbox[1]- obj_bbox[3])
    l_obj =  [obj_bbox[0],obj_bbox[1]]
    r_obj = [obj_bbox[2],  obj_bbox[3]]
    l_img = (0,0)
    r_img = (width,height)
    x_dist = min(r_obj[0], r_img[0])- max(l_obj[0], l_img[0])
    y_dist = min(r_obj[1], r_img[1])-max(l_obj[1], l_img[1])
    
    if( x_dist > 0 and y_dist > 0 ):
      inters_area = x_dist * y_dist
    else:
      inters_area = 0

    if(object_area == 0):
      percentage_visible = 0
    else:
      percentage_visible = (inters_area/object_area+0.0000001)*100
    #print(obj['category'] +" is "+ str(percentage_visible) + "%% in the image")
    if (percentage_visible<min_visible_percentage_per_object):
      #print("Objects are not visible!")
      return False
  return True

def append_object_to_scene(filepath):
  ## Override context due to blender 
  for window in bpy.context.window_manager.windows:
    screen = window.screen

    for area in screen.areas:
        if area.type == 'VIEW_3D':
            override = {'window': window, 'screen': screen, 'area': area}
            bpy.ops.screen.screen_full_area(override)
            break

  inner_path = 'Object'
  with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
    # link object to scene collection
    for obj_name in data_from.objects:
      if obj_name is not None:
        if obj_name == "Light" or obj_name == "Camera":
          continue
        bpy.ops.wm.append(
          directory = os.path.join(filepath, inner_path),
          filename = obj_name
        )
        selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
        obj_object = selected_objects[0] 
        return obj_object

def select_first_two_models(models_type,relationship):
  # Apply restrictions to relationships with some objects
  models_1_type = models_type
  models_2_type = models_type


  if (relationship is ON):
    models_1_type = [model for model in models_type if model!='Bottle' and model != 'Wine_Glass' and model != "Fork"and model != "Knife"and model != "Spoon"] 
  
  if (relationship is INSIDE_UP):
    models_1_type = [model for model in models_type if model=='Bottle']
    models_2_type = [model for model in models_type if model=='Mug']
  
  if (relationship is INSIDE):# we can only have bottle inside mug
    models_1_type =  [model for model in models_type if model=='Mug']
    models_2_type = [model for model in models_type if model=='Bottle']

  if(len(models_1_type)==0):
    return None, None
  # Select 1st model
  model1_key = random.choice(models_1_type)

  # Restriction based on the first model selectes    
  if (model1_key=='Mug' and relationship is ON):
    models_2_type = [model for model in models_type if model!='Bottle'] # if base is mug can't have bottle ON
  
  # Select 2nd model
  model2_key = random.choice(models_2_type)

  
  return model1_key, model2_key

def select_model(reference_model_struct, models_type,relationship,scene_struct):
  # Apply restrictions to relationships with some objects
  
  reference_model = reference_model_struct['category']
  models_2_type = models_type


  if (relationship is ON and (reference_model is 'Bottle'
   or reference_model is 'Fork'
   or reference_model is 'Knife'
   or reference_model is 'Spoon'
   or reference_model is 'Wine_Glass')):
    return None

  if (relationship is INSIDE_UP and reference_model is not 'Bottle') :
    return None
  elif (relationship is INSIDE_UP and reference_model is 'Bottle'):
    models_2_type = [model for model in models_type if model=='Mug']
  
  if (relationship is INSIDE and reference_model is not 'Mug'): # we can only have bottle inside mug
    return None
  elif(relationship is INSIDE and reference_model is 'Mug'):
    models_2_type = [model for model in models_type if model=='Bottle']

  # 1st model is the reference
  model1_key = reference_model

  # Restriction based on the first model selectes    
  if (model1_key=='Mug' and relationship is ON):
    models_2_type = [model for model in models_type if model!='Bottle'] # if base is mug can't have bottle ON
  
  # Select 2nd model
  model2_key = random.choice(models_2_type)

  return  model2_key


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
          if file.endswith(".obj") or file.endswith(".blend"):
              model_path = os.path.join(root, file)
              models_3d[category].append(model_path)

  table_models_paths = models_3d["Table"]

  # Task 1
  # models_type = ["Mug","Book","Bottle"]
  # Task 2
  models_type = ["Plate","Fork","Knife","Wine_Glass","Spoon"]
  # Task 3
  # models_type = ["Box"]
  num_imgs_render = args.num_images
  # Generate images with mug, bottle and books
  num_objects_chosen = random.choice([2,3])    # Randomly choose 2 or 3 objects in the image
  print("num_objects_chosen: ", num_objects_chosen)
  while(num_imgs_render>0):
    num_objects = num_objects_chosen
    # Initialize scene struct
    scene_struct = {"objects":[], "relationships":[],'desired_relationships':[]}

    # Load the main blendfile
    bpy.ops.wm.open_mainfile(filepath='data/base_scene.blend')


    # Add random table
    scene_struct, table_height, table_limit_points = add_random_table(args,scene_struct,table_models_paths)
    
    model1_key = None
    model2_key = None
    while(model1_key is None and model2_key is None):
      relationship = random.choice(relationships)
      model1_key, model2_key = select_first_two_models(models_type,relationship)
      relationship = INSIDE_UP
    scene_struct = add_two_objects(args,scene_struct,[model1_key,model2_key],[random.choice(models_3d[model1_key]),random.choice(models_3d[model2_key])],relationship,table_height,table_limit_points)# Add two objects to the table with the relationship chosen
    if scene_struct is False:
      # bpy.ops.wm.quit_blender()
      continue
    num_objects = num_objects - 2  # 2 objects were added
    while(num_objects>0):
      # Add an object with the reference in an existing object
      # Choose another random relation for the objects
      model2_key = None
      while(model2_key is None):
        relationship = random.choice(relationships)
        reference_object = random.choice([obj for obj in scene_struct['objects'] if obj['category'] != 'Table'])
        # In case there is already something on the plate put it above the thing above the plate 
        if relationship is ON and reference_object['category'] == 'Plate':
          there_is_something_above = True
          while(there_is_something_above):
              there_is = False
              for rel in scene_struct['relationships']:
                if rel['object'] == reference_object['id'] and rel['predicate'] == ON:
                  for obj in scene_struct['objects']:
                    if obj['id'] == rel['subject']:
                      reference_object = obj
                      there_is = True
                      #give the object above as reference
              if there_is == False:
                there_is_something_above  = False

        model2_key = select_model(reference_object,models_type,relationship,scene_struct)
        #print("model2_key: ",model2_key)
      # Add the new objec
      #print("reference_object:\n",reference_object)
      scene_struct = add_object_with_relationship(args,scene_struct,reference_object,model2_key, random.choice(models_3d[model2_key]),relationship,table_height,table_limit_points)
      if (scene_struct is False):
        break
      else:
        num_objects = num_objects-1


    if (scene_struct is False):
      continue

    if render_scene(args,scene_struct,table_height):
      num_imgs_render -= 1 # if the image is rendered subtract
      num_objects_chosen = random.choice([2,3])    # Randomly choose 2 or 3 objects in the image

  #bpy.ops.wm.quit_blender()


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
