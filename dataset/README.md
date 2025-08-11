
1. Download SRFUND dataset from: https://sprateam-ustc.github.io/SRFUND/download/
2. Save the dataset in ../../../Data/SRFUND
3. Run prepare_single_image.py to extract text info of a single image from the dataset
4. Run prepare_SRFUND.py to extract text info of the entire dataset
5. Run create_train_test_validation.py to create metadata.jsonl + the correct file structure for Donut fine tuning.


Donut metadata.jsonl:

Note: ground_truth_parse is the key value pairs extracted from prepare_SRFUND.py
''
{"file_name": {image_path0}, "ground_truth": "{"gt_parse": {ground_truth_parse}, ... {other_metadata_not_used} ... }"}
{"file_name": {image_path1}, "ground_truth": "{"gt_parse": {ground_truth_parse}, ... {other_metadata_not_used} ... }"}
''

Filestructure of data for Donut training:

''
dataset_name
├── test
│   ├── metadata.jsonl
│   ├── {image_path0}
│   ├── {image_path1}
│             .
│             .
├── train
│   ├── metadata.jsonl
│   ├── {image_path0}
│   ├── {image_path1}
│             .
│             .
└── validation
    ├── metadata.jsonl
    ├── {image_path0}
    ├── {image_path1}
              .
''