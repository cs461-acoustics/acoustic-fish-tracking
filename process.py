import os
import json
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter

def label_studio_to_pixels(ls_x, ls_y, img_w, img_h):
    return int((ls_x / 100.0) * img_w), int((ls_y / 100.0) * img_h)

def create_density_map(shape, dots, sigma=4):
    density = np.zeros(shape, dtype=np.float32)
    for x, y in dots:
        if 0 <= y < shape[0] and 0 <= x < shape[1]:
            density[y, x] = 1.0
    if np.sum(density) > 0:
        density = gaussian_filter(density, sigma=sigma, mode='constant')
    return density

def process_and_slice(json_path, image_dir, output_dir, tile_size=256, overlap=100):
    os.makedirs(os.path.join(output_dir, 'images'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'density_maps'), exist_ok=True)
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    tile_counter = 0
    step = tile_size - overlap # e.g., 156 pixels
    
    for item in data:
        img_name = os.path.basename(item['file_upload'])
        img_path = os.path.join(image_dir, img_name)
        
        # Fallback Strategy for Label Studio Hashes
        if not os.path.exists(img_path) and '-' in img_name:
            stripped_name = img_name.split('-', 1)[1]
            fallback_path = os.path.join(image_dir, stripped_name)
            if os.path.exists(fallback_path):
                img_path = fallback_path
                img_name = stripped_name
                    
        if not os.path.exists(img_path):
            print(f"Skipping {img_name}: file not found.")
            continue
            
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        h, w = img.shape
        
        # Parse dots
        raw_dots = []
        annotations = item.get('annotations', [])
        if isinstance(annotations, list) and len(annotations) > 0:
            annotations = annotations[0]
        for result in annotations.get('result', []):
            if result['type'] == 'keypointlabels':
                ls_x = result['value']['x']
                ls_y = result['value']['y']
                px_x, px_y = label_studio_to_pixels(ls_x, ls_y, w, h)
                raw_dots.append((px_x, px_y))

        print(f"Matched {img_name} ({w}x{h}): Processing {len(raw_dots)} fish dots...")

        # Create a grid of top-left coordinates to guarantee we cover the whole image
        y_positions = list(range(0, max(1, h - tile_size + 1), step))
        if y_positions[-1] + tile_size < h: 
            y_positions.append(h - tile_size) # Snaps to the very bottom edge if left out
            
        x_positions = list(range(0, max(1, w - tile_size + 1), step))
        if x_positions[-1] + tile_size < w: 
            x_positions.append(w - tile_size) # Snaps to the very right edge if left out

        # Loop through our guaranteed grid positions
        for y in y_positions:
            # Drop the tile ONLY if it falls almost entirely into the absolute bottom black bar
            if y > int(h * 0.90): 
                continue
                
            for x in x_positions:
                # Crop exactly a 512x512 tile
                tile_img = img[y:y+tile_size, x:x+tile_size]
                
                # Filter dots belonging strictly to this window step
                tile_dots = [
                    (dx - x, dy - y) 
                    for (dx, dy) in raw_dots 
                    if x <= dx < x + tile_size and y <= dy < y + tile_size
                ]
                
                # Generate density map
                tile_density = create_density_map((tile_size, tile_size), tile_dots)
                
                # Save out the training assets
                base_fn = f"tile_{tile_counter:04d}"
                cv2.imwrite(os.path.join(output_dir, 'images', f"{base_fn}.png"), tile_img)
                np.save(os.path.join(output_dir, 'density_maps', f"{base_fn}.npy"), tile_density)
                
                tile_counter += 1

    print(f"\nSuccess! Generated a total of {tile_counter} training pairs.")

# --- RUN SCRIPT ---
process_and_slice('project_annotations.json', './training_data', './processed_dataset')
