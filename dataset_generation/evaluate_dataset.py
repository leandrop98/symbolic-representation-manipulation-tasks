
import os, json
import cv2 as cv
import sys
import math
import numpy as np
path = "../task3/images"

# Read all json files
json_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.json')]
all_rel_count = {}
all_obj_count = {}
count_img = 0
avg_obj = 0
avg_rel = 0
im_rel_count = 0
im_obj_count = 0
count_inside = 0
for json_file in json_files:
    with open(path + "/" + json_file, 'r') as file:
        count_img+=1
        # Load json file
        data = json.load(file)

        for relationship in data["relationships"]:
            predicate = relationship['predicate']
            if predicate.lower() == "inside":
                json_path = path + "/" + json_file
                print(json_path)
                os.remove(json_path)
                os.remove(json_path.split('.json')[0]+'.png')
            if predicate.lower() in all_rel_count:
                all_rel_count[predicate.lower()] += 1
            else: 
                all_rel_count[predicate.lower()] = 1
            im_rel_count+=1
                        
        for obj in data['objects']:
            cat = obj['category']
            if cat.lower() in all_obj_count:
                all_obj_count[cat.lower()] += 1
            else:
                all_obj_count[cat.lower()] = 1
            im_obj_count+=1

avg_obj = im_obj_count/count_img
avg_rel = im_rel_count/count_img
print('all_obj_count: ',all_obj_count)
print('all_rel_count:',all_rel_count)
print('count_img:', count_img)
print('avg_obj:', avg_obj)
print('avg_rel:', avg_rel)



