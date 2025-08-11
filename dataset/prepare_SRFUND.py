import json
import os

def extract_data_from_json(json_file_path):
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    
    extracted_data = {}
    
    for png_filename, annotations in data.items():
        print(f"\nProcessing: {png_filename}")
        
        # Initialize storage for this PNG file
        extracted_data[png_filename] = {
            'texts': [],
            'labels': [],
            'relations': []
        }
        
        # Extract data from each annotation
        for annotation in annotations:
            text = annotation.get('text', '')

            label = annotation.get('label', '')
            
            linking = annotation.get('linking', [])
            
            extracted_data[png_filename]['texts'].append({
                'id': annotation.get('id'),
                'text': text
            })
            
            extracted_data[png_filename]['labels'].append({
                'id': annotation.get('id'),
                'label': label
            })
            
            # Process relations (linking)
            for relation in linking:
                if isinstance(relation, list) and len(relation) == 2:
                    extracted_data[png_filename]['relations'].append({
                        'from_id': relation[0],
                        'to_id': relation[1]
                    })
    
    return extracted_data

def print_extracted_data(extracted_data, limit_files=3):
    """
    Print the extracted data in a readable format
    """
    file_count = 0
    for png_filename, data in extracted_data.items():
        if file_count >= limit_files:
            print(f"\n... and {len(extracted_data) - limit_files} more files")
            break
            
        print(f"\n{'='*50}")
        print(f"FILE: {png_filename}")
        print(f"{'='*50}")
        
        # Print texts
        print(f"\nTEXTS ({len(data['texts'])} items):")
        for i, text_data in enumerate(data['texts'][:5]):  
            print(f"  {i+1}. ID: {text_data['id']} | Text: '{text_data['text']}' ")
        if len(data['texts']) > 5:
            print(f"  ... and {len(data['texts']) - 5} more texts")
        
        # Print labels
        print(f"\nLABELS ({len(data['labels'])} items):")
        label_counts = {}
        for label_data in data['labels']:
            label = label_data['label']
            label_counts[label] = label_counts.get(label, 0) + 1
        for label, count in label_counts.items():
            print(f"  {label}: {count}")
        
        # Print relations
        print(f"\nRELATIONS ({len(data['relations'])} items):")
        for i, relation in enumerate(data['relations'][:5]): 
            print(f"  {i+1}. {relation['from_id']} -> {relation['to_id']}")
        if len(data['relations']) > 5:
            print(f"  ... and {len(data['relations']) - 5} more relations")
        
        file_count += 1

def get_all_png_filenames(json_file_path):
    """
    Get all PNG filenames from the JSON file
    """
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    
    return list(data.keys())

def map_to_key_value_pairs(extracted_data):
    """
    Map the extracted data to key-value pairs based on labels
    Returns: dict with PNG filenames as keys and mapped data as values
    """
    mapped_data = {}
    
    for png_filename, data in extracted_data.items():
        # Create dictionaries to store texts by their labels
        headers = []
        questions = []
        answers = []
        others = []
        
        # Create a mapping from ID to text for easy lookup
        id_to_text = {text['id']: text['text'] for text in data['texts']}
        
        # Group texts by labels
        for label_data in data['labels']:
            text_id = label_data['id']
            label = label_data['label'].lower()
            text_content = id_to_text.get(text_id, '')
            
            if 'header' in label:
                headers.append({'id': text_id, 'text': text_content})
            elif 'question' in label:
                questions.append({'id': text_id, 'text': text_content})
            elif 'answer' in label:
                answers.append({'id': text_id, 'text': text_content})
            else:
                others.append({'id': text_id, 'text': text_content, 'label': label})
        
        # Create key-value pairs using relations
        key_value_pairs = []
        seen_pairs = set()  # To track unique pairs and avoid duplicates
        
        # Use relations to map question -> answer
        for relation in data['relations']:
            from_id = relation['from_id']
            to_id = relation['to_id']
            
            from_text = id_to_text.get(from_id, '')
            to_text = id_to_text.get(to_id, '')
            
            # Find labels for these IDs
            from_label = next((l['label'] for l in data['labels'] if l['id'] == from_id), '')
            to_label = next((l['label'] for l in data['labels'] if l['id'] == to_id), '')
            
            # Create a unique identifier for this pair
            pair_key = (from_id, to_id)
            
            if pair_key not in seen_pairs:
                seen_pairs.add(pair_key)
                
                if 'question' in from_label.lower() and 'answer' in to_label.lower():
                    key_value_pairs.append({
                        'type': 'question_answer',
                        'key': from_text,
                        'value': to_text,
                        'key_id': from_id,
                        'value_id': to_id
                    })
                elif 'header' in from_label.lower() and 'question' in to_label.lower():
                    key_value_pairs.append({
                        'type': 'header_question',
                        'key': from_text,
                        'value': to_text,
                        'key_id': from_id,
                        'value_id': to_id
                    })
        
        mapped_data[png_filename] = {
            'headers': headers,
            'questions': questions,
            'answers': answers,
            'others': others,
            'key_value_pairs': key_value_pairs
        }
    

    return mapped_data

def print_mapped_data(mapped_data, limit_files=2):
    """
    Print the mapped data in a readable format
    """
    file_count = 0
    for png_filename, data in mapped_data.items():
        if file_count >= limit_files:
            print(f"\n... and {len(mapped_data) - limit_files} more files")
            break
            
        print(f"\n{'='*60}")
        print(f"FILE: {png_filename}")
        print(f"{'='*60}")
        
        # Print headers
        print(f"\nHEADERS ({len(data['headers'])} items):")
        for header in data['headers'][:3]:
            print(f"  ID {header['id']}: '{header['text']}'")
        
        # Print questions
        print(f"\nQUESTIONS ({len(data['questions'])} items):")
        for question in data['questions'][:3]:
            print(f"  ID {question['id']}: '{question['text']}'")
        
        # Print answers
        print(f"\nANSWERS ({len(data['answers'])} items):")
        for answer in data['answers'][:3]:
            print(f"  ID {answer['id']}: '{answer['text']}'")
        
        # Print others
        print(f"\nOTHERS ({len(data['others'])} items):")
        for other in data['others'][:3]:
            print(f"  ID {other['id']} ({other['label']}): '{other['text']}'")
        
        # Print key-value pairs
        print(f"\nKEY-VALUE PAIRS ({len(data['key_value_pairs'])} items):")
        for kv in data['key_value_pairs']:
            print(f"  {kv['type']}: '{kv['key']}' -> '{kv['value']}'")
        
        file_count += 1

def save_individual_json_files(mapped_data, output_folder_path):
    """
    Save key-value pairs for each PNG to separate JSON files
    Args:
        mapped_data: The output from map_to_key_value_pairs
        output_folder_path: Folder path where to save individual JSON files
    """
    import os
    
    # Create directory if it doesn't exist
    os.makedirs(output_folder_path, exist_ok=True)
    
    saved_files = []
    
    for png_filename, data in mapped_data.items():
        # Create key-value pairs for this specific PNG
        png_key_value_pairs = {}
        
        for kv_pair in data['key_value_pairs']:
            key = kv_pair['key']
            value = kv_pair['value']
            
            # Handle duplicate keys by appending a counter
            original_key = key
            counter = 1
            while key in png_key_value_pairs:
                key = f"{original_key}_{counter}"
                counter += 1
            
            png_key_value_pairs[key] = value
        
        # Create output file path
        json_filename = png_filename.replace('.png', '.json')
        output_file_path = os.path.join(output_folder_path, json_filename)
        
        # Save to JSON file
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(png_key_value_pairs, f, indent=2, ensure_ascii=False)
        
        saved_files.append(output_file_path)
        print(f"Saved {len(png_key_value_pairs)} key-value pairs for {png_filename} to: {output_file_path}")
    
    print(f"\nTotal: {len(saved_files)} JSON files saved to {output_folder_path}")
    return saved_files

if __name__ == "__main__":
    json_file_path = '../../../Data/SRFUND/dataset/instance__annotation/en.json'
    json_output_folder_path = '../../../Data/SRFUND/donut_format/individual_jsons/'

    # Extract all data
    print("Extracting all data...")
    all_data = extract_data_from_json(json_file_path)
    print_extracted_data(all_data, limit_files=2)
    
    # Map to key-value pairs
    print("\n\nMapping to key-value pairs...")
    mapped_data = map_to_key_value_pairs(all_data)
    print_mapped_data(mapped_data, limit_files=2)
    
    # Save individual JSON files for each PNG
    print("\n\nSaving individual JSON files...")
    save_individual_json_files(mapped_data, json_output_folder_path)
     
    # Get all PNG filenames
    print("\n\nAll PNG filenames:")
    png_filenames = get_all_png_filenames(json_file_path)
    for i, filename in enumerate(png_filenames[:10]):  # Show first 10
        print(f"{i+1}. {filename}")
    print(f"... Total: {len(png_filenames)} PNG files") 
    
    
    
