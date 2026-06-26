import colorsys
from io import BytesIO

import numpy as np
import torch
from PIL import Image
from scipy import ndimage
from sklearn.cluster import KMeans
from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor

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

    def load_image(self, file_bytes: bytes) -> Image.Image:

        image = Image.open(BytesIO(file_bytes)).convert("RGB")

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
        detected = [CLOTHING_LABELS.get(label_id, f"Unknown({label_id}))") for label_id in unique_labels]
        print(f"Detected segments: {', '.join(detected)}")

        return mask.astype(np.uint8), segmentation


    def clean_mask(self, mask: np.ndarray, min_region_size: int = 500) -> np.array:
        
        labeled, num_features = ndimage.label(mask)

        if num_features == 0:
            print("Warning: No clothing regions found in mask")
            return mask
        
        cleaned_mask = np.zeros_like(mask)

        for i in range(1, num_features+1):
            region = labeled == i

            if np.sum(region) >= min_region_size:
                cleaned_mask[region] = 1

        original_pixels = np.sum(mask)
        cleaned_pixels = np.sum(cleaned_mask)

        removed = original_pixels - cleaned_pixels

        print(f"Mask cleaning: {original_pixels} -> {cleaned_pixels} pixels ({removed} removed)")

        return cleaned_mask


    def extract_garment_pixels(self, image: Image.Image, mask: np.ndarray) -> np.ndarray:

        img_array = np.array(image)

        garment_pixels = img_array[mask == 1]

        print(f"Extracted {len(garment_pixels)} garment pixels")

        return garment_pixels


    def run_kmeans(self, pixels: np.ndarray, k: int = 4) -> tuple[np.ndarray, np.ndarray]:

        if len(pixels) < k:
            raise ValueError(f"Not enough pixels ({len(pixels)}) for {k} clusters")
        
        max_pixels  = 5000

        if len(pixels) > max_pixels:
            indices = np.random.choice(len(pixels), max_pixels, replace=False)
            sample_pixels = pixels[indices]
        else:
            sample_pixels = pixels
        

        print(f"Running KMeans with k={k} on {len(sample_pixels)} pixels...")

        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)

        kmeans.fit(sample_pixels)

        labels = kmeans.predict(pixels)
        cluster_sizes = np.bincount(labels, minlength=k)
        centers = kmeans.cluster_centers_.astype(int)

        sorted_indices = np.argsort(cluster_sizes)[::-1]
        sorted_centers = centers[sorted_indices]
        sorted_sizes = cluster_sizes[sorted_indices]

        for i, (center, size) in enumerate(zip(sorted_centers, sorted_sizes)):
            pct = (size / len(labels)) * 100
            print(f"  Cluster {i+1}: RGB({center[0]}, {center[1]}, {center[2]}) - {pct:.1f}%")
        
        return sorted_centers, sorted_sizes

    def select_dominant_rgb(self, centers: np.ndarray, sizes: np.ndarray) -> tuple[int, int, int]:
        dominant  = centers[0]
        return int(dominant[0]), int(dominant[1]), int(dominant[2])


    def rgb_to_hsl(self, r:int, g:int, b:int) -> dict:

        # Normalize RGB to 0-1 range
        r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0

        h, lightness, s = colorsys.rgb_to_hls(r_norm, g_norm, b_norm)

        h_degrees = int(h * 360)
        
        return {
            "h": h_degrees,
            "s": round(s, 3),
            "l": round(lightness, 3)
        }

    def extract_colours(self, image: Image.Image, k: int = 4) -> dict:
        
        mask, segmentation = self.create_clothing_mask(image)
        cleaned_mask = self.clean_mask(mask)
        
        if np.sum(cleaned_mask) < 100:
            print("Warning: Very few clothing pixels detected")
            return {
                "cleaned_mask" : cleaned_mask,
                "primary_color": None,
                "dominant_rgb": None,
                "error": "Insufficient clothing pixels detected"
            }
        
    
        garment_pixels = self.extract_garment_pixels(image, cleaned_mask)  

        centers, sizes = self.run_kmeans(garment_pixels, k=k)

        r, g, b = self.select_dominant_rgb(centers, sizes)
        print(f"\nDominant color: RGB({r}, {g}, {b})")


        hsl = self.rgb_to_hsl(r, g, b)
        print(f"HSL: H={hsl['h']}°, S={hsl['s']:.1%}, L={hsl['l']:.1%}")

        return {
            "cleaned_mask" : cleaned_mask,
            "primary_color": hsl,
            "dominant_rgb": {"r": r, "g": g, "b": b},
            "all_clusters": [
                {"rgb": {"r": int(c[0]), "g": int(c[1]), "b": int(c[2])}, "percentage": round(s / sum(sizes) * 100, 1)}
                for c, s in zip(centers, sizes)
            ]
        }


    def pil_to_bytes(self, image: Image.Image, fmt: str = "PNG") -> bytes:
        buf = BytesIO()
        image.save(buf, format=fmt)
        return buf.getvalue()


    

    def process_upload(self, file_bytes:bytes) -> dict:
        
        image = self.load_image(file_bytes)
        res = self.extract_colours(image)

        cleaned_mask = res['cleaned_mask']

        img_array = np.array(image)
        masked_array = img_array.copy()
        masked_array[cleaned_mask == 0] = [255, 255, 255]  
        masked_img = Image.fromarray(masked_array)
     
        masked_bytes = self.pil_to_bytes(masked_img, fmt="JPEG")

        return {"masked_bytes": masked_bytes, "colours": res}


    
        
