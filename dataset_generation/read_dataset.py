
import os, json
import pandas as pd
import cv2 as cv
import sys
import numpy as np
path = "../output/images"

# Read all json files
json_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.json')]
for json_file in json_files:
    with open(path + "/" + json_file, 'r') as file:
        # Load json file
        data = json.load(file)
        # Load 
        img = cv.imread(cv.samples.findFile(path + "/" + data["image_filename"]))
        if img is None:
            sys.exit("Could not read the image.")

        height, width = img.shape[:2]

        # Draw 3d bounding box
        # for obj in data["objects"]:
        #     for point in obj['3d_bbox']:
        #         if(point[0]<width and point[1] < height):
        #             cv.circle(img, (point[0],point[1]), radius=0, color=(0, 0, 255), thickness=4)
        
        # Draw 2d bounding box
        for obj in data["objects"]:
            cv.rectangle(img,obj['2d_bbox'][0],obj['2d_bbox'][1],(0,0,250),2)


        # Resize the image to add some text
        blank_image = np.zeros((height,width+300,3), np.uint8)
        blank_image[:,:] = (255,255,255)
        l_img = blank_image.copy()                    # (600, 900, 3)
        l_img[0:height, 0:width] = img.copy()
        img = l_img
        text_position = 20
        cv.putText(img,"Relationships:", (width + 10, text_position), fontFace = cv.FONT_HERSHEY_SIMPLEX, fontScale=0.7,color= (0,0,0),thickness=2)
        text_position = 40
        for relationship in data["relationships"]:
            # Write some Text
            for obj in data["objects"]:
                if obj["id"] == relationship["subject"]:
                    subject = obj["category"]
                if obj["id"] == relationship["object"]:
                    object = obj["category"]
            cv.putText(img,object + "-" + relationship["predicate"]+"-" + subject, (width + 10,text_position), fontFace = cv.FONT_HERSHEY_SIMPLEX, fontScale=0.5,color = (0,0,0),lineType=1)
            text_position += 15




        cv.imshow("Display window", img)
        k = cv.waitKey(0)
