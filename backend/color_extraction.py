"""
Phase 2: Color Extraction using SegFormer and KMeans
Steps 1-9 implementation for testing.

Usage:
    python color_extraction.py <image_path>
    python color_extraction.py test_shirt.jpg
"""

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


# SegFormer clothing segmentation labels (mattmdjaga/segformer_b2_clothes)
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

# Labels that represent actual clothing items (for color extraction)
GARMENT_LABEL_IDS = {4, 5, 6, 7, 8, 17}  # Upper-clothes, Skirt, Pants, Dress, Belt, Scarf

    


class ColorExtractor:
    """Extracts dominant colors from clothing items using SegFormer segmentation."""
    
    def __init__(self, model_name: str = "mattmdjaga/segformer_b2_clothes"):
        """Initialize the SegFormer model and processor."""
        
        print(f"Loading SegFormer model: {model_name}")
        self.processor = SegformerImageProcessor.from_pretrained(model_name)
        self.model = SegformerForSemanticSegmentation.from_pretrained(model_name)
        self.model.eval()
        
        # Use MPS if available (Apple Silicon), else CPU
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")
        
        self.model.to(self.device)
        print(f"Model loaded on device: {self.device}")
    
    def load_image(self, image_path: str) -> Image.Image:
        """Step 1: Load image from path."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        image = Image.open(path).convert("RGB")
        print(f"Loaded image: {path.name} ({image.size[0]}x{image.size[1]})")
        return image
    
    def create_clothing_mask(self, image: Image.Image) -> np.ndarray:
        """Step 2: Run SegFormer to create clothing mask."""
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        logits = outputs.logits
        upsampled = torch.nn.functional.interpolate(
            logits,
            size=image.size[::-1],  # (height, width)
            mode="bilinear",
            align_corners=False
        )
        
        segmentation = upsampled.argmax(dim=1).cpu().numpy()[0]
        
        # Create binary mask for clothing items
        mask = np.isin(segmentation, list(GARMENT_LABEL_IDS))
        
        # Log detected segments
        unique_labels = np.unique(segmentation)
        detected = [CLOTHING_LABELS.get(l, f"Unknown({l})") for l in unique_labels]
        print(f"Detected segments: {', '.join(detected)}")
        
        return mask.astype(np.uint8), segmentation
    
    def clean_mask(self, mask: np.ndarray, min_region_size: int = 500) -> np.ndarray:
        """Step 3: Clean mask by removing small noisy regions."""
        # Label connected components
        labeled, num_features = ndimage.label(mask)
        
        if num_features == 0:
            print("Warning: No clothing regions found in mask")
            return mask
        
        # Remove small regions
        cleaned_mask = np.zeros_like(mask)
        for i in range(1, num_features + 1):
            region = labeled == i
            if np.sum(region) >= min_region_size:
                cleaned_mask[region] = 1
        
        original_pixels = np.sum(mask)
        cleaned_pixels = np.sum(cleaned_mask)
        removed = original_pixels - cleaned_pixels
        print(f"Mask cleaning: {original_pixels} -> {cleaned_pixels} pixels ({removed} removed)")
        
        return cleaned_mask
    
    def extract_garment_pixels(self, image: Image.Image, mask: np.ndarray) -> np.ndarray:
        """Steps 5-6: Keep garment pixels only and convert to RGB array."""
        img_array = np.array(image)
        
        # Apply mask to get only garment pixels
        garment_pixels = img_array[mask == 1]
        
        print(f"Extracted {len(garment_pixels)} garment pixels")
        return garment_pixels
    
    def run_kmeans(self, pixels: np.ndarray, k: int = 4) -> tuple[np.ndarray, np.ndarray]:
        """Step 7: Run KMeans clustering on masked pixels."""
        if len(pixels) < k:
            raise ValueError(f"Not enough pixels ({len(pixels)}) for {k} clusters")
        
        # Subsample if too many pixels (for speed)
        max_pixels = 50000
        if len(pixels) > max_pixels:
            indices = np.random.choice(len(pixels), max_pixels, replace=False)
            sample_pixels = pixels[indices]
        else:
            sample_pixels = pixels
        
        print(f"Running KMeans with k={k} on {len(sample_pixels)} pixels...")
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(sample_pixels)
        
        # Get cluster centers and their sizes
        labels = kmeans.predict(pixels)
        cluster_sizes = np.bincount(labels, minlength=k)
        centers = kmeans.cluster_centers_.astype(int)
        
        # Sort by cluster size (largest first)
        sorted_indices = np.argsort(cluster_sizes)[::-1]
        sorted_centers = centers[sorted_indices]
        sorted_sizes = cluster_sizes[sorted_indices]
        
        for i, (center, size) in enumerate(zip(sorted_centers, sorted_sizes)):
            pct = (size / len(labels)) * 100
            print(f"  Cluster {i+1}: RGB({center[0]}, {center[1]}, {center[2]}) - {pct:.1f}%")
        
        return sorted_centers, sorted_sizes
    
    def select_dominant_rgb(self, centers: np.ndarray, sizes: np.ndarray) -> tuple[int, int, int]:
        """Step 8: Select largest cluster as dominant RGB."""
        dominant = centers[0]
        return int(dominant[0]), int(dominant[1]), int(dominant[2])
    
    def rgb_to_hsl(self, r: int, g: int, b: int) -> dict:
        """Step 9: Convert dominant RGB to HSL."""
        # Normalize RGB to 0-1 range
        r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
        
        # Convert to HLS (Python's colorsys uses HLS, not HSL)
        h, l, s = colorsys.rgb_to_hls(r_norm, g_norm, b_norm)
        
        # Convert h to degrees (0-360)
        h_degrees = int(h * 360)
        
        return {
            "h": h_degrees,
            "s": round(s, 3),
            "l": round(l, 3)
        }
    
    def extract_colors(self, image_path: str, k: int = 4) -> dict:
        """
        Main extraction pipeline (Steps 1-9).
        
        Returns:
            dict with primary_color (HSL) and dominant_rgb
        """
        # Step 1: Load image
        image = self.load_image(image_path)
        
        # Step 2: Create clothing mask
        mask, segmentation = self.create_clothing_mask(image)
        
        # Step 3: Clean mask
        cleaned_mask = self.clean_mask(mask)
        
        # Check if we have enough clothing pixels
        if np.sum(cleaned_mask) < 100:
            print("Warning: Very few clothing pixels detected")
            return {
                "primary_color": None,
                "dominant_rgb": None,
                "error": "Insufficient clothing pixels detected"
            }
        
        # Steps 5-6: Extract garment pixels
        garment_pixels = self.extract_garment_pixels(image, cleaned_mask)
        
        # Step 7: Run KMeans
        centers, sizes = self.run_kmeans(garment_pixels, k=k)
        
        # Step 8: Select dominant RGB
        r, g, b = self.select_dominant_rgb(centers, sizes)
        print(f"\nDominant color: RGB({r}, {g}, {b})")
        
        # Step 9: Convert to HSL
        hsl = self.rgb_to_hsl(r, g, b)
        print(f"HSL: H={hsl['h']}°, S={hsl['s']:.1%}, L={hsl['l']:.1%}")
        
        return {
            "primary_color": hsl,
            "dominant_rgb": {"r": r, "g": g, "b": b},
            "all_clusters": [
                {"rgb": {"r": int(c[0]), "g": int(c[1]), "b": int(c[2])}, "percentage": round(s / sum(sizes) * 100, 1)}
                for c, s in zip(centers, sizes)
            ]
        }
    
    def save_debug_images(self, image_path: str, output_dir: str = ".") -> None:
        """Save debug visualization images."""
        image = self.load_image(image_path)
        mask, segmentation = self.create_clothing_mask(image)
        cleaned_mask = self.clean_mask(mask)
        
        output_path = Path(output_dir)
        base_name = Path(image_path).stem
        
        # Save mask visualization
        mask_img = Image.fromarray((cleaned_mask * 255).astype(np.uint8))
        mask_img.save(output_path / f"{base_name}_mask.png")
        print(f"Saved: {base_name}_mask.png")
        
        # Save masked image (clothing only)
        img_array = np.array(image)
        masked_array = img_array.copy()
        masked_array[cleaned_mask == 0] = [255, 255, 255]  # White background
        masked_img = Image.fromarray(masked_array)
        masked_img.save(output_path / f"{base_name}_masked.png")
        print(f"Saved: {base_name}_masked.png")
        
        # Save full segmentation visualization
        colors = np.random.randint(0, 255, (len(CLOTHING_LABELS), 3), dtype=np.uint8)
        colors[0] = [0, 0, 0]  # Background is black
        seg_colored = colors[segmentation]
        seg_img = Image.fromarray(seg_colored)
        seg_img.save(output_path / f"{base_name}_segmentation.png")
        print(f"Saved: {base_name}_segmentation.png")


def main():
    if len(sys.argv) < 2:
        print("Usage: python color_extraction.py <image_path> [--debug]")
        print("\nExample:")
        print("  python color_extraction.py shirt.jpg")
        print("  python color_extraction.py shirt.jpg --debug")
        sys.exit(1)
    
    image_path = sys.argv[1]
    debug_mode = "--debug" in sys.argv
    
    extractor = ColorExtractor()
    
    if debug_mode:
        print("\n--- Debug Mode: Saving visualization images ---\n")
        extractor.save_debug_images(image_path)
    
    print("\n--- Color Extraction ---\n")
    result = extractor.extract_colors(image_path)
    
    print("\n--- Final Result ---")
    print(f"""
{{
  "primary_color": {result.get('primary_color')},
  "dominant_rgb": {result.get('dominant_rgb')}
}}
""")
    
    if result.get('all_clusters'):
        print("All detected color clusters:")
        for i, cluster in enumerate(result['all_clusters']):
            rgb = cluster['rgb']
            print(f"  {i+1}. RGB({rgb['r']}, {rgb['g']}, {rgb['b']}) - {cluster['percentage']}%")


if __name__ == "__main__":
    main()
