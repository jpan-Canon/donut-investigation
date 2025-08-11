import json
import os

def extract_specific_png_data(json_file_path, png_filename):
    """
    Extract text data for a specific PNG file from the JSON dataset
    """
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    
    if png_filename not in data:
        print(f"PNG file '{png_filename}' not found in the dataset")
        return None
    
    annotations = data[png_filename]
    
    texts = []
    labels = []
    relations = []
    
    for annotation in annotations:
        # Extract text information
        texts.append({
            'id': annotation.get('id'),
            'text': annotation.get('text', ''),
            'lines': annotation.get('lines', [])
        })
        
        # Extract label information
        labels.append({
            'id': annotation.get('id'),
            'label': annotation.get('label', '')
        })
        
        # Extract relations
        linking = annotation.get('linking', [])
        for relation in linking:
            if isinstance(relation, list) and len(relation) == 2:
                relations.append({
                    'from_id': relation[0],
                    'to_id': relation[1]
                })
    
    return {
        'texts': texts,
        'labels': labels,
        'relations': relations
    }


def map_key_value_pairs(specific_data, png_filename="specific_file"):
    """
    Map the extracted data from a specific PNG to key-value pairs based on labels
    Returns: dict with the PNG filename as key and mapped data as value
    """
    # Create dictionaries to store texts by their labels
    headers = []
    questions = []
    answers = []
    others = []
    
    # Create a mapping from ID to text for easy lookup
    id_to_text = {text['id']: text['text'] for text in specific_data['texts']}
    
    # Group texts by labels
    for label_data in specific_data['labels']:
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
    seen_pairs = set()  # track unique pairs and avoid duplicates
    
    # Use relations to map question -> answer and header -> question
    for relation in specific_data['relations']:
        from_id = relation['from_id']
        to_id = relation['to_id']
        
        from_text = id_to_text.get(from_id, '')
        to_text = id_to_text.get(to_id, '')
        
        # Find labels for these IDs
        from_label = next((l['label'] for l in specific_data['labels'] if l['id'] == from_id), '')
        to_label = next((l['label'] for l in specific_data['labels'] if l['id'] == to_id), '')
        
        
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
    
    mapped_data = {
        png_filename: {
            'headers': headers,
            'questions': questions,
            'answers': answers,
            'others': others,
            'key_value_pairs': key_value_pairs
        }
    }
    
    return mapped_data

def print_mapped_data(mapped_data, limit_files=2):
    """
    Print the mapped data in a readable format
    """
    for png_filename, data in mapped_data.items():
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

def save_key_value_pairs_to_json(mapped_data, output_file_path):
    """
    Save key-value pairs to a JSON file in the format {"key": "value"}
   
    """
    
    all_key_value_pairs = {}
    
    for png_filename, data in mapped_data.items():
        for kv_pair in data['key_value_pairs']:
            key = kv_pair['key']
            value = kv_pair['value']
            
            # Handle duplicate keys by appending a counter
            original_key = key
            counter = 1
            while key in all_key_value_pairs:
                key = f"{original_key}_{counter}"
                counter += 1
            
            all_key_value_pairs[key] = value
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    
    # Save to JSON file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(all_key_value_pairs, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved {len(all_key_value_pairs)} key-value pairs to: {output_file_path}")
    return all_key_value_pairs


if __name__ == "__main__":
    json_file_path = '../../../Data/SRFUND/dataset/instance__annotation/en.json'
    json_output_folder_path = '../../../Data/SRFUND/donut_format_single/'

    # Extract data for a specific PNG
    print("\n\nExtracting data for specific PNG:")
    specific_png = "0000971160.png"
    specific_data = extract_specific_png_data(json_file_path, specific_png)
    if specific_data:
        print(f"PNG: {specific_png}")
        print(f"Texts: {len(specific_data['texts'])}")
        print(f"Labels: {len(specific_data['labels'])}")
        print(f"Relations: {len(specific_data['relations'])}")
    
        print("\nFirst 3 texts:")
        for text in specific_data['texts'][:3]:
            print(f"  ID {text['id']}: '{text['text']}'")
        
        print("\nFirst 3 labels:")
        for label in specific_data['labels'][:3]:
            print(f"  ID {label['id']}: {label['label']}")
        
        print("\nFirst 3 relations:")
        for relation in specific_data['relations'][:3]:
            print(f"  {relation['from_id']} -> {relation['to_id']}") 

        print("\n\nMapping to key-value pairs...")
        mapped_data = map_key_value_pairs(specific_data, specific_png)
        print_mapped_data(mapped_data, limit_files=2)
        
        # Save key-value pairs to JSON
        output_json_path = f"{json_output_folder_path}{specific_png.replace('.png', '')}.json"
        save_key_value_pairs_to_json(mapped_data, output_json_path)
