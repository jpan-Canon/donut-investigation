import os
import json
import random
from PIL import Image
import numpy as np

def resize_image(image_path, target_size=(2560, 1920)):
    """
    Resize and pad an image to fit the target size while maintaining aspect ratio
    
    Args:
        image_path: Path to the input image
        target_size: Tuple of (width, height) for the target size
        
    Returns:
        PIL Image object with the resized and padded image
    """
    target_width, target_height = target_size
    
    # Open the image
    with Image.open(image_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        orig_width, orig_height = img.size
        
        # Calculate the scaling factor to fit within target size
        scale_factor = min(target_width / orig_width, target_height / orig_height)
        
        # New dimensions
        new_width = int(orig_width * scale_factor)
        new_height = int(orig_height * scale_factor)
        
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create a new image with target size and padd with white background
        padded_img = Image.new('RGB', target_size, (255, 255, 255))

        #Center original image
        pad_x = (target_width - new_width) // 2
        pad_y = (target_height - new_height) // 2
        
        # Paste the resized image onto the padded background
        padded_img.paste(img_resized, (pad_x, pad_y))
        
        return padded_img

def create_metadata_files(jsons_folder_path, images_folder_path, output_folder_path, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, resize_images=True, target_size=(2560, 1920)):
    """
    Create train/test/validation metadata.jsonl files from JSON mappings
    
    Args:
        jsons_folder_path: Path to folder containing individual JSON files
        images_folder_path: Path to folder containing corresponding images
        output_folder_path: Path where to save the metadata files
        train_ratio: Proportion for training set (default 0.7)
        val_ratio: Proportion for validation set (default 0.15)
        test_ratio: Proportion for test set (default 0.15)
        resize_images: Whether to resize images during metadata creation (default True)
        target_size: Target size for image resizing (default (2560, 1920))
    """
    
    # Create output directories
    os.makedirs(os.path.join(output_folder_path, "train"), exist_ok=True)
    os.makedirs(os.path.join(output_folder_path, "test"), exist_ok=True)
    os.makedirs(os.path.join(output_folder_path, "validation"), exist_ok=True)
    
    # Get all JSON files
    json_files = []
    for filename in os.listdir(jsons_folder_path):
        if filename.endswith(".json"):
            json_files.append(filename)
    
    print(f"Found {len(json_files)} JSON files")
    
    # Set seed for reproducibility
    random.seed(123)
    random.shuffle(json_files)
    
    # Split indices
    total_files = len(json_files)
    train_count = int(total_files * train_ratio)
    val_count = int(total_files * val_ratio)
    test_count = total_files - train_count - val_count
    
    # Split the files
    train_files = json_files[:train_count]
    val_files = json_files[train_count:train_count + val_count]
    test_files = json_files[train_count + val_count:]
    
    print(f"Split: Train={len(train_files)}, Validation={len(val_files)}, Test={len(test_files)}")
    
    # Create metadata files
    datasets = [
        ("train", train_files),
        ("validation", val_files),
        ("test", test_files)
    ]
    
    for dataset_name, file_list in datasets:
        metadata_path = os.path.join(output_folder_path, dataset_name, "metadata.jsonl")
        
        print(f"\nCreating {dataset_name} metadata...")
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            for json_filename in file_list:
                json_path = os.path.join(jsons_folder_path, json_filename)
                
                try:
                    with open(json_path, 'r', encoding='utf-8') as json_file:
                        ground_truth_parse = json.load(json_file)
                    
                    image_filename = json_filename.replace('.json', '.png')
                    

                    image_path = os.path.join(images_folder_path, image_filename)
                    if not os.path.exists(image_path):
                        print(f"Warning: Image {image_filename} not found, skipping...")
                        continue
                    
                    
                    metadata_entry = {
                        "file_name": image_filename,
                        "ground_truth": json.dumps({"gt_parse": ground_truth_parse})
                    }
                    

                    f.write(json.dumps(metadata_entry) + "\n")
                    
                except Exception as e:
                    print(f"Error processing {json_filename}: {e}")
                    continue
        
        print(f"Saved {dataset_name} metadata to: {metadata_path}")
    
    return {
        "train_count": len(train_files),
        "validation_count": len(val_files), 
        "test_count": len(test_files),
        "total_count": total_files
    }

def copy_images_to_splits(jsons_folder_path, images_folder_path, output_folder_path):
    """
    Copy images to their respective train/test/validation folders based on existing metadata files
    """
    import shutil
    
    datasets = ["train", "validation", "test"]
    
    for dataset_name in datasets:
        metadata_path = os.path.join(output_folder_path, dataset_name, "metadata.jsonl")
        dataset_images_path = os.path.join(output_folder_path, dataset_name)
        
        if not os.path.exists(metadata_path):
            print(f"Metadata file not found: {metadata_path}")
            continue
            
        os.makedirs(dataset_images_path, exist_ok=True)
        
        print(f"\nCopying images for {dataset_name}...")
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    image_filename = entry["file_name"]
                    
                    source_path = os.path.join(images_folder_path, image_filename)
                    dest_path = os.path.join(dataset_images_path, image_filename)
                    
                    if os.path.exists(source_path):
                        # Resize and pad the image before saving
                        resized_img = resize_image(source_path, target_size=(2560, 1920))
                        resized_img.save(dest_path, 'PNG', quality=95)
                    else:
                        print(f"Warning: Source image not found: {source_path}")
                        
                except Exception as e:
                    print(f"Error copying image: {e}")
                    continue
        
        print(f"Images copied to: {dataset_images_path}")

if __name__ == "__main__":
    jsons_folder_path = "../../../Data/SRFUND/donut_format/individual_jsons/"
    images_folder_path = "../../../Data/SRFUND/dataset/images/"
    output_folder_path = "../../../Data/SRFUND/donut_format/"
    
    
    print("Creating metadata files...")
    results = create_metadata_files(
        jsons_folder_path=jsons_folder_path,
        images_folder_path=images_folder_path,
        output_folder_path=output_folder_path,
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        resize_images=True,
        target_size=(2560, 1920)
    )
    
    print(f"\nDataset split summary:")
    print(f"Training: {results['train_count']} files")
    print(f"Validation: {results['validation_count']} files") 
    print(f"Test: {results['test_count']} files")
    print(f"Total: {results['total_count']} files")
    
    print(f"\nCopying images into splits...")
    copy_images_to_splits(jsons_folder_path, images_folder_path, output_folder_path)