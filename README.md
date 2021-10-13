# Dataset Generation


Example code to generate a dataset:
```
blender --background --python render_images.py -- --delete_previous_images True --use_gpu 1 --num_images 5000
```

### Usage


```
usage: render_images.py [-h] [--base_scene_blendfile BASE_SCENE_BLENDFILE] [--models_dir MODELS_DIR] [--border_limit BORDER_LIMIT] [--radius_near_far RADIUS_NEAR_FAR]
                        [--num_images NUM_IMAGES] [--filename_prefix FILENAME_PREFIX] [--output_image_dir OUTPUT_IMAGE_DIR] [--delete_previous_images DELETE_PREVIOUS_IMAGES]
                        [--use_gpu USE_GPU] [--width WIDTH] [--height HEIGHT] [--key_light_jitter KEY_LIGHT_JITTER] [--fill_light_jitter FILL_LIGHT_JITTER]
                        [--back_light_jitter BACK_LIGHT_JITTER] [--key_light_power KEY_LIGHT_POWER] [--fill_light_power FILL_LIGHT_POWER] [--back_light_power BACK_LIGHT_POWER]
                        [--sunlight_power SUNLIGHT_POWER] [--camera_jitter CAMERA_JITTER] [--render_num_samples RENDER_NUM_SAMPLES] [--render_min_bounces RENDER_MIN_BOUNCES]
                        [--render_max_bounces RENDER_MAX_BOUNCES] [--render_tile_size RENDER_TILE_SIZE]

optional arguments:
  -h, --help            show this help message and exit
  --base_scene_blendfile BASE_SCENE_BLENDFILE
                        Base blender file on which all scenes are based; includes ground plane, lights, and camera.
  --models_dir MODELS_DIR
                        Directory where .obj files for object models are stored
  --border_limit BORDER_LIMIT
                        The number to change the sensitivy of the relatioships. Higher number means the single relationships are more narrow
  --radius_near_far RADIUS_NEAR_FAR
                        Limit of the radius of what is considered "near" or "far" from an object
  --num_images NUM_IMAGES
                        The number of images to render
  --filename_prefix FILENAME_PREFIX
                        This prefix will be prepended to the rendered images and JSON files
  --output_image_dir OUTPUT_IMAGE_DIR
                        The directory where output images will be stored. It will be created if it does not exist.
  --delete_previous_images DELETE_PREVIOUS_IMAGES
                        Delete previous generated images from the directory where output images will be stored.
  --use_gpu USE_GPU     Setting --use_gpu 1 enables GPU-accelerated rendering using CUDA. You must have an NVIDIA GPU with the CUDA toolkit installed for to work.
  --width WIDTH         The width (in pixels) for the rendered images
  --height HEIGHT       The height (in pixels) for the rendered images
  --key_light_jitter KEY_LIGHT_JITTER
                        The magnitude of random jitter to add to the key light position.
  --fill_light_jitter FILL_LIGHT_JITTER
                        The magnitude of random jitter to add to the fill light position.
  --back_light_jitter BACK_LIGHT_JITTER
                        The magnitude of random jitter to add to the back light position.
  --key_light_power KEY_LIGHT_POWER
                        The magnitude of random power range to add to the key light.
  --fill_light_power FILL_LIGHT_POWER
                        The magnitude of random power to add to the fill light.
  --back_light_power BACK_LIGHT_POWER
                        The magnitude of random power range to add to the back light.
  --sunlight_power SUNLIGHT_POWER
                        The magnitude of random power range to add to the sun light.
  --camera_jitter CAMERA_JITTER
                        The magnitude of random jitter to add to the camera position
  --render_num_samples RENDER_NUM_SAMPLES
                        The number of samples to use when rendering. Larger values will result in nicer images but will cause rendering to take longer.
  --render_min_bounces RENDER_MIN_BOUNCES
                        The minimum number of bounces to use for rendering.
  --render_max_bounces RENDER_MAX_BOUNCES
                        The maximum number of bounces to use for rendering.
  --render_tile_size RENDER_TILE_SIZE
                        The tile size to use for rendering. This should not affect the quality of the rendered image but may affect the speed; CPU-based rendering may achieve better
                        performance using smaller tile sizes while larger tile sizes may be optimal for GPU-based rendering.
```
