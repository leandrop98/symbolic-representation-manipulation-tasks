
import os, json
import cv2 as cv
import sys
import math
import numpy as np
path = "../output/images"

# Read all json files
def display_images():
    json_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.json')]
    all_rel_count = {}
    all_obj_count = {}
    for json_file in json_files:
        with open(path + "/" + json_file, 'r') as file:
            # Load json file
            data = json.load(file)

            for relationship in data["relationships"]:
                predicate = relationship['predicate']
                if predicate.lower() in all_rel_count:
                    all_rel_count[predicate.lower()] += 1
                else: 
                    all_rel_count[predicate.lower()] = 1
           
            for obj in data['objects']:
                cat = obj['category']
                if cat.lower() in all_obj_count:
                    all_obj_count[cat.lower()] += 1
                else: 
                    all_obj_count[cat.lower()] = 1
            print('all_obj_count: ',all_obj_count)
            print('all_rel_count:',all_rel_count)

def main(argv):
    display_images()
if __name__ == "__main__":
   main(sys.argv[1:])
   
