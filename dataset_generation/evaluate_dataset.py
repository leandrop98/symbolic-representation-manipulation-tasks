
import os, json
import cv2 as cv
import sys
import math
import numpy as np
path = "../task3/images"

# Read all json files
json_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.json')]
png_files = [png_file for png_file in os.listdir(path) if png_file.endswith('.png')]
for png in png_files:
    png_path = path + "/" + png
    json_path = png_path.split('.png')[0]+'.json'
    if (not os.path.isfile(json_path)):
        os.remove(png_path)
all_rel_count = {}
all_obj_count = {}
count_img = 0
avg_obj = 0
avg_rel = 0
im_rel_count = 0
im_obj_count = 0
count_inside = 0
mugs_to_delete = 0
img_to_delete = 0

for json_file in json_files:
    mugs_per_image = 0
    mug_upside_down_per_img = 0
    with open(path + "/" + json_file, 'r') as file:
        count_img+=1
        # Load json file
        data = json.load(file)
        json_path = path + "/" + json_file
        img_path = json_path.split('.json')[0]+'.png'
        if (not os.path.isfile(img_path)):
            os.remove(json_path)
        for relationship in data["relationships"]:
            predicate = relationship['predicate']
            if predicate.lower() == "inside":
                json_path = path + "/" + json_file
                os.remove(json_path)
                os.remove(json_path.split('.json')[0]+'.png')                
            if predicate.lower() in all_rel_count:
                all_rel_count[predicate.lower()] += 1
            else: 
                all_rel_count[predicate.lower()] = 1
            im_rel_count+=1

        list_cats=[]       
        for obj in data['objects']:
            cat = obj['category']
            list_cats.append(cat)
            if cat.lower() in all_obj_count:
                all_obj_count[cat.lower()] += 1
            else:
                all_obj_count[cat.lower()] = 1
            im_obj_count+=1
        if img_to_delete > 0:
            #if ("Mug" in list_cats and "Bottle" in list_cats and not "Mug_upside_down" in list_cats):
            os.remove(json_path)
            os.remove(json_path.split('.json')[0]+'.png')     
            img_to_delete -=1
        # if mug_upside_down_per_img > 1:
        #     if(os.path.isfile(json_path)):
        #         os.remove(json_path)
        #     os.remove(json_path.split('.json')[0]+'.png')           
   
avg_obj = im_obj_count/count_img
avg_rel = im_rel_count/count_img

print('\nall_obj_count:')
for key, obj_count in all_obj_count.items():
    print(key + ":" + str(obj_count))

print('\nall_rel_count:')
for key, rel_count in all_rel_count.items():
    print(key + ":" + str(rel_count))

print('\ncount_img:', count_img)
print('avg_obj:', avg_obj)
print('avg_rel:', avg_rel)


