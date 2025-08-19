"""
Donut Single Image Inference
Copyright (c) 2022-present NAVER Corp.
MIT License
"""
import argparse
import json
import os
from pathlib import Path

import torch
from PIL import Image

from donut import DonutModel


def infer_single(args):
    """
    Perform inference on a single image using a pretrained Donut model.
    
    Args:
        args: Arguments containing model path, image path, task name, etc.
    
    Returns:
        dict: Inference result
    """
    # Load the pretrained model
    print(f"Loading model from: {args.pretrained_model_name_or_path}")
    pretrained_model = DonutModel.from_pretrained(args.pretrained_model_name_or_path)

    # Move model to GPU if available and use half precision for faster inference
    if torch.cuda.is_available():
        pretrained_model.half()
        pretrained_model.to("cuda")
        print("Using GPU for inference")
    else:
        print("Using CPU for inference")

    pretrained_model.eval()

    # Load and validate the input image
    if not os.path.exists(args.image_path):
        raise FileNotFoundError(f"Image file not found: {args.image_path}")
    
    print(f"Loading image from: {args.image_path}")
    image = Image.open(args.image_path)
    
    # Convert to RGB if necessary (in case of RGBA or grayscale images)
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # Prepare the prompt based on task type
    if args.task_name == "docvqa":
        if not args.question:
            raise ValueError("Question is required for docvqa task")
        prompt = f"<s_{args.task_name}><s_question>{args.question.lower()}</s_question><s_answer>"
        print(f"Using DocVQA prompt with question: {args.question}")
    else:
        # For fine-tuned models, use the task name that the model was trained on
        # Common task names: cord, rvlcdip, SRFUND, or your custom task name
        prompt = f"<s_{args.task_name}>"
        print(f"Using prompt for task: {args.task_name}")
    
    print(f"Full prompt: {prompt}")

    # Perform inference
    print("Starting inference...")
    result = pretrained_model.inference(image=image, prompt=prompt)
    output = result["predictions"][0]

    print("Inference completed!")
    print("Result:")
    print(json.dumps(output, indent=2, ensure_ascii=False))

    # Save result if output path is specified
    if args.output_path:
        os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
        with open(args.output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"Result saved to: {args.output_path}")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Donut model inference on a single image")
    
    # Required arguments
    parser.add_argument(
        "--pretrained_model_name_or_path", 
        type=str, 
        required=True,
        help="Path to the pretrained Donut model"
    )
    parser.add_argument(
        "--image_path", 
        type=str, 
        required=True,
        help="Path to the input image file"
    )
    parser.add_argument(
        "--task_name", 
        type=str, 
        required=True,
        help="Task name that your model was fine-tuned on (e.g., 'cord', 'docvqa', 'rvlcdip', 'SRFUND', or your custom task name)"
    )
    
    # Optional arguments
    parser.add_argument(
        "--question", 
        type=str, 
        default=None,
        help="Question for DocVQA task (required only for docvqa task)"
    )
    parser.add_argument(
        "--output_path", 
        type=str, 
        default=None,
        help="Path to save the inference result as JSON file"
    )
    
    args = parser.parse_args()

    # Validate arguments
    if args.task_name == "docvqa" and not args.question:
        parser.error("--question is required when --task_name is 'docvqa'")

    try:
        result = infer_single(args)
    except Exception as e:
        print(f"Error during inference: {str(e)}")
        exit(1)
