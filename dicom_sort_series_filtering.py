#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import pydicom
import shutil
from pathvalidate import sanitize_filepath
from tqdm import tqdm
import re

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

def should_process_series(series_desc, series_num):
    # Debugging statements
    print(f"Checking Series: Description='{series_desc}', Number='{series_num}'")
    
    # Case-insensitive search for "T1", "T2", or "FLAIR"
    if series_num.endswith('1') and any(sub in series_desc.upper() for sub in ['T1', 'T2', 'FLAIR']):
        return True
    return False

def copy_or_move_dicom_image(src_file, dest_base_dir, pattern, anonymize=False, id_map=None, move=False, force=False):
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

    series_desc = get_dicom_attribute(dataset, 'SeriesDescription')
    series_num = get_dicom_attribute(dataset, 'SeriesNumber')

    if not should_process_series(series_desc, series_num):
        print(f"Skipping file '{src_file}' - Series criteria not met")
        return

    sop_instance_uid = get_dicom_attribute(dataset, 'SOPInstanceUID')
    filename = f"{sop_instance_uid}.dcm"
    
    for attribute in ['PatientID', 'StudyDate', 'SeriesNumber', 'SeriesDescription']:
        value = get_dicom_attribute(dataset, attribute)
        pattern = pattern.replace(f'%{attribute}%', value)

    dest_directory = sanitize_filepath(os.path.join(dest_base_dir, pattern), platform='auto')
    os.makedirs(dest_directory, exist_ok=True)
    
    dest_file_path = os.path.join(dest_directory, filename)
    
    if not force and os.path.exists(dest_file_path):
        print(f"Skipping file '{src_file}' - Destination file already exists and --force not specified")
        return
    
    if move:
        shutil.move(src_file, dest_file_path)
        print(f"Moved file '{src_file}' to '{dest_file_path}'")
    else:
        shutil.copy2(src_file, dest_file_path)
        print(f"Copied file '{src_file}' to '{dest_file_path}'")

def copy_directory(src_dir, dest_dir, pattern, anonymize, id_map, move, force):
    all_files = [os.path.join(root, file) for root, _, files in os.walk(src_dir) for file in files]
    for file in tqdm(all_files, desc="Processing", unit="file"):
        copy_or_move_dicom_image(file, dest_dir, pattern, anonymize, id_map, move, force)

def sort_dicom(input_dir, output_dir, anonymize, id_map, move, force):
    pattern = '%PatientID%/%SeriesDescription%'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    copy_directory(input_dir, output_dir, pattern, anonymize, id_map, move, force)

missing_ids = set()

def main():
    parser = argparse.ArgumentParser(description="This script copies and optionally anonymizes DICOM files into a structured directory. It can also replace PatientID based on a correlation file.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--dicomin', type=str, required=True, help='Path to the input directory containing unsorted DICOM files.')
    parser.add_argument('--dicomout', type=str, required=True, help='Path to the output directory where structured and optionally anonymized DICOM files will be stored.')
    parser.add_argument('--anonymize', action='store_true', help='If specified, anonymizes DICOM tags such as PatientName and PatientBirthDate.')
    parser.add_argument('--ID_correlation', type=str, help='Optional path to a correlation file mapping old PatientIDs to new PatientIDs. \nExpected format: oldID,newID per line.')
    parser.add_argument('--move', action='store_true', help='If specified, moves the files instead of copying them.')
    parser.add_argument('--force', action='store_true', help='If specified, overwrites existing files.')
    args = parser.parse_args()

    id_map = read_id_correlation(args.ID_correlation) if args.ID_correlation else None

    sort_dicom(args.dicomin, args.dicomout, args.anonymize, id_map, args.move, args.force)

    if missing_ids:
        log_file_path = 'missing_patient_ids.log'
        with open(log_file_path, 'w') as log_file:
            for missing_id in missing_ids:
                log_file.write(f'{missing_id}\n')
        print(f"Missing PatientIDs logged in '{log_file_path}'.")

if __name__ == '__main__':
    main()
