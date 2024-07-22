#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import pydicom
from pathvalidate import sanitize_filepath
from tqdm import tqdm
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

def get_dicom_attribute(dataset, attribute):
    try:
        return str(getattr(dataset, attribute))
    except AttributeError:
        return 'UNKNOWN'

def read_id_correlation(file_path):
    id_map = {}
    if file_path:
        with open(file_path, 'r') as file:
            for line in file:
                parts = re.split(r',|\s|\t', line.strip())
                if len(parts) >= 2:
                    old_id, new_id = parts[0], parts[1]
                    id_map[old_id] = new_id
                else:
                    print(f"Invalid line format: {line}")
    return id_map

def anonymize_dicom_tags(dataset, id_map=None):
    if 'PatientBirthDate' in dataset:
        dataset.PatientBirthDate = ''
    if 'PatientName' in dataset:
        dataset.PatientName = 'ANONYMIZED'
    if 'PatientID' in dataset and id_map:
        old_id = dataset.PatientID
        if old_id in id_map:
            dataset.PatientID = id_map[old_id]
        else:
            missing_ids.add(old_id)
    return dataset

def generate_unique_filename(directory, filename):
    base_name, extension = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base_name}_{counter}{extension}"
        counter += 1
    return new_filename

def sanitize_series_description(description):
    description = description.replace(' ', '_').replace('*', '').replace('.', '_')
    invalid_chars = r'<>:"/\|?*'
    description = re.sub(f'[{re.escape(invalid_chars)}]', '', description)
    return sanitize_filepath(description, platform='auto')

def decompress_dataset(dataset):
    try:
        # Attempt to decompress the dataset
        dataset.decompress()
    except Exception as e:
        print(f"Error decompressing dataset: {str(e)}")
    return dataset

def copy_dicom_image(src_file, dest_base_dir, pattern, anonymize=False, id_map=None, decompress=False):
    non_dicom_extensions = ['.png', '.jpeg', '.jpg', '.gif', '.bmp']
    if any(src_file.lower().endswith(ext) for ext in non_dicom_extensions):
        return

    try:
        dataset = pydicom.dcmread(src_file)
    except:
        print(f'Not a DICOM file: {src_file}')
        return

    if anonymize or id_map:
        dataset = anonymize_dicom_tags(dataset, id_map)

    if decompress:
        dataset = decompress_dataset(dataset)

    for attribute in ['PatientID', 'StudyDate', 'SeriesNumber', 'SeriesDescription']:
        value = get_dicom_attribute(dataset, attribute)
        if attribute == 'SeriesDescription':
            value = sanitize_series_description(value)
        pattern = pattern.replace(f'%{attribute}%', value)

    dest_directory = sanitize_filepath(os.path.join(dest_base_dir, pattern), platform='auto')
    os.makedirs(dest_directory, exist_ok=True)
    
    unique_filename = generate_unique_filename(dest_directory, os.path.basename(src_file))
    dataset.save_as(os.path.join(dest_directory, unique_filename))

def process_file(file, dest_dir, pattern, anonymize, id_map, decompress):
    copy_dicom_image(file, dest_dir, pattern, anonymize, id_map, decompress)

def copy_directory(src_dir, dest_dir, pattern, anonymize, id_map, decompress):
    all_files = [os.path.join(root, file) for root, _, files in os.walk(src_dir) for file in files]
    
    num_cores = max(2, multiprocessing.cpu_count() // 2)
    with ProcessPoolExecutor(max_workers=num_cores) as executor:
        futures = [executor.submit(process_file, file, dest_dir, pattern, anonymize, id_map, decompress) for file in all_files]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing", unit="file"):
            future.result()  # To raise exceptions if any

def sort_dicom(input_dir, output_dir, anonymize, id_map, decompress):
    pattern = '%PatientID%/%StudyDate%/%SeriesDescription%'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    copy_directory(input_dir, output_dir, pattern, anonymize, id_map, decompress)

missing_ids = set()

def main():
    parser = argparse.ArgumentParser(description="This script copies, optionally anonymizes, and optionally decompresses DICOM files into a structured directory. It can also replace PatientID based on a correlation file.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--dicomin', type=str, required=True, help='Path to the input directory containing unsorted DICOM files.')
    parser.add_argument('--dicomout', type=str, required=True, help='Path to the output directory where structured and optionally anonymized DICOM files will be stored.')
    parser.add_argument('--anonymize', action='store_true', help='If specified, anonymizes DICOM tags such as PatientName and PatientBirthDate.')
    parser.add_argument('--ID_correlation', type=str, help='Optional path to a correlation file mapping old PatientIDs to new PatientIDs. \nExpected format: oldID,newID per line.')
    parser.add_argument('--decompress', action='store_true', help='If specified, decompresses DICOM files during processing.')
    args = parser.parse_args()

    id_map = read_id_correlation(args.ID_correlation) if args.ID_correlation else None

    sort_dicom(args.dicomin, args.dicomout, args.anonymize, id_map, args.decompress)

    if missing_ids:
        log_file_path = 'missing_patient_ids.log'
        with open(log_file_path, 'w') as log_file:
            for missing_id in missing_ids:
                log_file.write(f'{missing_id}\n')
        print(f"Missing PatientIDs logged in '{log_file_path}'.")

if __name__ == '__main__':
    main()
