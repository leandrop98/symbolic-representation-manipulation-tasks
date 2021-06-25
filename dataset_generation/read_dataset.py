
import os, json
import pandas as pd
import cv2 as cv
import sys
import numpy as np
import math

path = "../output/images"

# Read all json files
def display_images(bbox2d,bbox3d):
    json_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.json')]
    for json_file in json_files:
        with open(path + "/" + json_file, 'r') as file:
            # Load json file
            data = json.load(file)
            # Load image
            img = cv.imread(cv.samples.findFile(path + "/" + data["image_filename"]))
            if img is None:
                sys.exit("Could not read the image.")

            height, width = img.shape[:2]

            if(bbox3d):
                # Draw 3d bounding box (uncomment to draw 3d bounding box)
                for obj in data["objects"]:
                    cv.line(img,(obj['3d_bbox'][0][0],obj['3d_bbox'][0][1]),(obj['3d_bbox'][1][0],obj['3d_bbox'][1][1]),color=(0, 255, 0))
                    cv.line(img,(obj['3d_bbox'][1][0],obj['3d_bbox'][1][1]),(obj['3d_bbox'][2][0],obj['3d_bbox'][2][1]),color=(0, 255, 0))
                    cv.line(img,(obj['3d_bbox'][2][0],obj['3d_bbox'][2][1]),(obj['3d_bbox'][3][0],obj['3d_bbox'][3][1]),color=(0, 255, 0))
                    cv.line(img,(obj['3d_bbox'][3][0],obj['3d_bbox'][3][1]),(obj['3d_bbox'][0][0],obj['3d_bbox'][0][1]),color=(0, 255, 0))
                    
                    cv.line(img,(obj['3d_bbox'][4][0],obj['3d_bbox'][4][1]),(obj['3d_bbox'][5][0],obj['3d_bbox'][5][1]),color=(0, 255, 0))
                    cv.line(img,(obj['3d_bbox'][5][0],obj['3d_bbox'][5][1]),(obj['3d_bbox'][6][0],obj['3d_bbox'][6][1]),color=(0, 255, 0))
                    cv.line(img,(obj['3d_bbox'][6][0],obj['3d_bbox'][6][1]),(obj['3d_bbox'][7][0],obj['3d_bbox'][7][1]),color=(0, 255, 0))
                    cv.line(img,(obj['3d_bbox'][7][0],obj['3d_bbox'][7][1]),(obj['3d_bbox'][4][0],obj['3d_bbox'][4][1]),color=(0, 255, 0))
                    
                    cv.line(img,(obj['3d_bbox'][0][0],obj['3d_bbox'][0][1]),(obj['3d_bbox'][4][0],obj['3d_bbox'][4][1]),color=(0, 255, 0))
                    cv.line(img,(obj['3d_bbox'][1][0],obj['3d_bbox'][1][1]),(obj['3d_bbox'][5][0],obj['3d_bbox'][5][1]),color=(0, 255, 0))
                    cv.line(img,(obj['3d_bbox'][2][0],obj['3d_bbox'][2][1]),(obj['3d_bbox'][6][0],obj['3d_bbox'][6][1]),color=(0, 255, 0))
                    cv.line(img,(obj['3d_bbox'][3][0],obj['3d_bbox'][3][1]),(obj['3d_bbox'][7][0],obj['3d_bbox'][7][1]),color=(0, 255, 0))
            if(bbox2d):
                #Draw 2d bounding box
                for obj in data["objects"]:
                    cv.rectangle(img,obj['2d_bbox'][0],obj['2d_bbox'][1],(0,0,250),2)
                    cv.putText(img,obj['category'],(obj['2d_bbox'][0][0], obj['2d_bbox'][0][1]+20), fontFace = cv.FONT_HERSHEY_SIMPLEX, fontScale=0.5,color= (0,0,255),thickness=1)

            # Resize the image to add the relationships text

            # Set number of columns
            columns_number = math.ceil(len(data["relationships"])/10)
            
            # Resize display are to write the relationships
            blank_image = np.zeros((height,width+(250*2),3), np.uint8)
            blank_image[:,:] = (255,255,255)
            l_img = blank_image.copy()                
            l_img[0:height, 0:width] = img.copy()
            img = l_img
            text_position = 20

            # Write the relationships
            column = 0
            cv.putText(img,"Relationships:", (width + 10, text_position), fontFace = cv.FONT_HERSHEY_SIMPLEX, fontScale=0.7,color= (0,0,0),thickness=2)
            text_position = 40
            line = 0
            for relationship in data["relationships"]:
                # Write some Text
                for obj in data["objects"]:
                    if obj["id"] == relationship["subject"]:
                        subject = obj["category"]
                    if obj["id"] == relationship["object"]:
                        object = obj["category"]
                cv.putText(img,object + "-" + relationship["predicate"]+"-" + subject, (width + 10+ (200*column),text_position), fontFace = cv.FONT_HERSHEY_SIMPLEX, fontScale=0.5,color = (0,0,0),lineType=1)
                text_position += 15
                
                # Add 1 line
                line+=1
                # CHange columns to write the relationships
                if line >=10:
                    column+=1
                    line=0
                    text_position = 40



            text_position += 15
            for obj in data['objects']:
                if 'state' in obj:
                    cv.putText(img,obj['category'] + " is " + obj["state"], (width + 10 +  (200*column),text_position), fontFace = cv.FONT_HERSHEY_SIMPLEX, fontScale=0.5,color = (0,0,0),lineType=1)
                    text_position += 15

            cv.putText(img,  data["image_filename"], (10,10), fontFace = cv.FONT_HERSHEY_SIMPLEX, fontScale=0.3,color = (0,0,0),lineType=1)



            cv.imshow("Display window", img)
            k = cv.waitKey(0)

def main(argv):
    bbox2d = False
    bbox3d = False
    for arg in argv:
        if (arg == "bbox2d"):
            bbox2d = True
        if (arg == "bbox3d"):
            bbox3d = True

    display_images(bbox2d,bbox3d)
if __name__ == "__main__":
   main(sys.argv[1:])
   
