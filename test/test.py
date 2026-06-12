from platform import processor
import sys
import colorsys
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
from scipy import ndimage
from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
import torch


CLOTHING_LABELS = {
    0: "Background",
    1: "Hat",
    2: "Hair",
    3: "Sunglasses",
    4: "Upper-clothes",
    5: "Skirt",
    6: "Pants",
    7: "Dress",
    8: "Belt",
    9: "Left-shoe",
    10: "Right-shoe",
    11: "Face",
    12: "Left-leg",
    13: "Right-leg",
    14: "Left-arm",
    15: "Right-arm",
    16: "Bag",
    17: "Scarf",
}


GARMENT_LABEL_IDS = {4, 5, 6, 7, 8, 17}


class ColorExtractor:
    
    def __init__(self, model_name: str = "mattmdjaga/segformer_b2_clothes"):
        print(f"Loading SegFormer model: {model_name}")
        
        self.processor = SegformerImageProcessor.from_pretrained(model_name)
        self.model = SegformerForSemanticSegmentation.from_pretrained(model_name)

        self.model.eval()

        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")
        
        self.model.to(self.device)
        print(f"Model loaded on device: {self.device}")

    def load_image(self, image_path: str) -> Image.Image:
        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        image = Image.open(path).convert("RGB")

        print(f"Loaded image: {path.name} ({image.size[0]}x{image.size[1]})")
        return image
    
    def create_clothing_mask(self, image: Image.Image):
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
        
       
        logits = outputs.logits
        
        unsampled = torch.nn.functional.interpolate(
            logits, 
            size = image.size[::-1],
            mode = 'bilinear',
            align_corners = False
        )
    

        segmentation = unsampled.argmax(dim=1).cpu().numpy()[0]

        
        
        mask = np.isin(segmentation, list(GARMENT_LABEL_IDS))

        unique_labels = np.unique(segmentation)
        detected = [CLOTHING_LABELS.get(l, f"Unknown({l}))") for l in unique_labels]
        print(f"Detected segments: {', '.join(detected)}")

        return mask.astype(np.uint8), segmentation



def main():
    
    extractor = ColorExtractor()
    print(extractor.create_clothing_mask(extractor.load_image("./shirt.jpg")))

if __name__ == "__main__":
    main()