
import os, json
import cv2 as cv
import sys
import math
import numpy as np
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 

path = "../task1_3/images"
# Label map
voc_labels = [x.strip() for x in open(f'obj.txt').readlines()]
label_map = {k: v + 1 for v, k in enumerate(voc_labels)}
rev_label_map = {v: k for k, v in label_map.items()}  # Inverse mapping

# Color map for bounding boxes of detected objects from https://sashat.me/2017/01/11/list-of-20-simple-distinct-colors/
# List of colors
distinct_colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080', '#ffffff', '#000000']

label_color_map = {k: distinct_colors[i] for i, k in enumerate(label_map.keys())}

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

            font = ImageFont.truetype("./calibri.ttf", 15)

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
                    cat = obj['category'].lower()

                    h = label_color_map[cat.lower()].replace('#','')
                    label_color = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                    cv.rectangle(img,(obj['2d_bbox'][0],obj['2d_bbox'][1]),
                    (obj['2d_bbox'][2], obj['2d_bbox'][3]),label_color,2)
                    
                    #cv.putText(img,obj['category'],(obj['2d_bbox'][0], obj['2d_bbox'][3]+20), fontFace = font, fontScale=0.5,color= (0,0,255),thickness=1)
                    
                    text_size = font.getsize(cat.upper())
                    textbox_location_1 = (int(obj['2d_bbox'][0]), int(obj['2d_bbox'][1] - text_size[1])-5)
                    textbox_location_2 = (int(obj['2d_bbox'][0] + text_size[0] + 10),int(obj['2d_bbox'][1]))
                    text_location = (int(obj['2d_bbox'][0] + 2.), int(obj['2d_bbox'][1])-4)

                    
                    cv.rectangle(img,textbox_location_1,textbox_location_2, label_color,-1)
                    cv.putText(img,obj['category'],text_location, fontFace = cv.FONT_HERSHEY_TRIPLEX                           , fontScale=0.5,color= (255,255,255),thickness=1)


            # Resize the image to add the relationships text

            # Set number of columns
            columns_number = math.ceil(len(data["relationships"])/10)
            
            # Resize display are to write the relationships
            blank_image = np.zeros((height,width+(350*2),3), np.uint8)
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
                cv.putText(img,subject + "-" + relationship["predicate"]+"-" + object, (width + 10+ (350*column),text_position), fontFace = cv.FONT_HERSHEY_SIMPLEX, fontScale=0.5,color = (0,0,0),lineType=1)
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
                    cv.putText(img,obj['category'] + " is " + obj["state"], (width + 10 +  (350*column),text_position), fontFace = cv.FONT_HERSHEY_SIMPLEX, fontScale=0.5,color = (0,0,0),lineType=1)
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
    print(argv)

    display_images(bbox2d,bbox3d)
if __name__ == "__main__":
   main(sys.argv[1:])
   
