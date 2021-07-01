import torch
from torch.utils.data import Dataset
import json
import os
from PIL import Image
import glob, os
from torchvision import transforms, utils
from utils import transform
import torchvision.transforms.functional as FT

class ObjectsDataset(Dataset):
    """
    A PyTorch Dataset class to be used in a PyTorch DataLoader to create batches.
    """

    def __init__(self, data_folder, split):
        """
        :param data_folder: folder where data files are stored
        :param split: split, one of 'TRAIN' or 'TEST'
        """
        self.split = split.upper()

        assert self.split in {'TRAIN', 'TEST'}

        self.data_folder = data_folder

        # Read data files
        all_images = []
        all_files = []
        for j_file in glob.glob(data_folder + "/*.json"):
            with open(j_file) as jsonFile:
                jsonObject = json.load(jsonFile)
                all_files.append(jsonObject)
                jsonFile.close()
                all_images.append(data_folder + "/" + jsonObject['image_filename'])

        self.ground_truth = all_files
        self.images = all_images

        assert len(self.images) == len(self.ground_truth)

    def __getitem__(self, i):
        # Read image
        image = Image.open(self.images[i], mode='r')
        image = image.convert('RGB')

        # Read objects in this image (bounding boxes, labels, difficulties)
        ground_truth = self.ground_truth[i]
        boxes = []
        labels = []
        for obj in ground_truth['objects']:
            boxes.append(tuple(obj['2d_bbox'][0] + obj['2d_bbox'][1] ))
            labels.append(obj['category'])
        boxes = torch.FloatTensor(boxes)  # (n_objects, 4)
        # Apply transformations
        image, boxes, labels = transform(image, boxes, labels, split=self.split)
        
        return image, boxes, labels

    def __len__(self):
        return len(self.images)

 
    def collate_fn(self, batch):
        """
        Since each image may have a different number of objects, we need a collate function (to be passed to the DataLoader).
        This describes how to combine these tensors of different sizes. We use lists.
        Note: this need not be defined in this Class, can be standalone.
        :param batch: an iterable of N sets from __getitem__()
        :return: a tensor of images, lists of varying-size tensors of bounding boxes, labels, and difficulties
        """

        images = list()
        boxes = list()
        labels = list()

        for b in batch:
            images.append(b[0])
            boxes.append(b[1])
            labels.append(b[2])

        images = torch.stack(images, dim=0)

        return images, boxes, labels  # tensor (N, 3, 300, 300), 3 lists of N tensors each