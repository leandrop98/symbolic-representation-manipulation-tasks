# Visually Perceiving Symbolic Representation for Manipulation Task in Robotics

This code was developed in the context of the master thesis with the title "Visually Perceiving Symbolic Representation for Manipulation Task in Robotics".
Here you can find the code used to generate the synthetic datasets used in this work. 


## 1. Generating Images

The code was developed in Ubuntu 18.04.5 LTS.

To generate the images you will need:

- [Blender 2.92](https://www.blender.org/download/)
- [Python 3](https://www.python.org/downloads/)

Firstly, download blender from the official link, then extract the file downloaded. Blender ships with its own installation of Python which is used to execute scripts that interact with Blender;

You'll need to add the `image_generation` directory to Python path of Blender's bundled Python. The easiest way to do this is by adding a `.pth` file to the `site-packages` directory of Blender's Python, like this:

```bash
echo $PWD/image_generation >> $BLENDER/$VERSION/python/lib/python3.5/site-packages/image_generation.pth
```
where `$BLENDER` is the directory where Blender is installed and `$VERSION` is your Blender version; for example on OSX you might run:

```bash
echo $PWD/image_generation >> /Applications/blender/blender.app/Contents/Resources/2.78/python/lib/python3.5/site-packages/image_generation.pth
```
**Note: Replace `python3.5`  with the current python version in your blender.**

You can then render images by running the following commands:

```bash
cd image_generation
blender --background --python render_images.py -- --delete_previous_images True --use_gpu 1 --num_images 5000
```

On OSX the `blender` binary is located inside the blender.app directory; for convenience you may want to
add the following alias to your `~/.bash_profile` file:

```bash
alias blender='/Applications/blender/blender.app/Contents/MacOS/blender'
```

If you have an NVIDIA GPU with CUDA installed then you can use the GPU to accelerate rendering like this:

```bash
blender --background --python render_images.py -- --num_images 10 --use_gpu 1
```


To generate a dataset you can use the example below:

```bash
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

You must change the line 1188 with the model types you want to generate the dataset:

```
# Task 1
# models_type = ["Mug","Book","Bottle"]
# Task 2
models_type = ["Plate","Fork","Knife","Wine_Glass","Spoon"]
# Task 3
# models_type = ["Box"]
```
In this case the generated images will contain the objects "Plate", "Fork", "Knife", "Wine_Glass", "Spoon".

### Example of generated images

After the command terminates you should have a set of images like these:

![generated_images](https://user-images.githubusercontent.com/29043968/137180311-345492fd-bf71-45fd-98c0-9832fe3c9a48.png)

## 2. Neural Networks

The code regarding the neural networks, datasets used, and models trained are available in Google Drive. Click [here](https://drive.google.com/drive/folders/1CDvHaPUWd8XM5vNo7PhWHje4cXXTfdr3?usp=sharing) to go to Google Drive.

### Datasets

All the datasets used are available in the folder `data`.
There are 3 synthetic datasets that were generated for this thesis. These datasets contain the images and respective annotations. In these datasets the annotations correspond to the object bounding box, object category and the relationships between the objects. 

There are also 3 real world datasets that we captured and labeled manually. In these datasets only the object bounding box and category were labeled. 

The file `obj.txt` in each dataset contains all the object categories in the dataset. The file `rel.txt` contains all the relationships used in the dataset. The file `rel.txt` also exists in the real world datasets but it is not used however this must not be deleted. 

Before using a dataset for training it is necessary to prepare these datasets beforehand. For that use the file `DataPreparation.ipynb`, follow  the instructions in the file to use it. The file `test.pkl` and `train.pkl` must be generated. The file `prior.pkl` correspond to an attempt of using the probability of a triple subject-predicate-object appear in the dataset, however, this was not used in the thesis. 

### Object Detection

To train the Object Detection model you must go to the folder `ssd-object-detection`. Open the file `SSD_ObjectDetection_T1.ipnyb`. This file is prepared to use the dataset for the first task. Follow the instructions in the file to train and test your own dataset. You can also use one of the available datasets.

In the folder `ssd-object-detection/results` there are models trained with the available datasets. You can evaluate or test some images with the trained models.

To use your test dataset for relationship detection you must generate the `proposal.pkl` using the file `SSD_ObjectDetection_T1.ipnyb`.

### Relationship Detection

Our model for relationship detection is located in the folder `vrd-dsr-mine`. In the folder `vrd-dsr-mine/models` there are several models trained that you can use to test or evaluate the model. 

You can train the model by following the instructions in the file `RelationshipDetection.ipynb`.
You can also use this file to test one of the trained models.

If you have any doubts please refer to the source code. You also read the thesis paper. 

# Citation

If you use this work please cite:

