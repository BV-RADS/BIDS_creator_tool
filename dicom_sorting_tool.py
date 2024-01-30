#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import pydicom
import shutil
from pathvalidate import sanitize_filepath
from tqdm import tqdm

def get_dicom_attribute(dataset, attribute):
    try:
        return str(getattr(dataset, attribute))
    except AttributeError:
        return 'UNKNOWN'

def copy_dicom_image(src_file, dest_base_dir, pattern):
    # Skip known non-DICOM file extensions
    non_dicom_extensions = ['.png', '.jpeg', '.jpg', '.gif', '.bmp']
    if any(src_file.lower().endswith(ext) for ext in non_dicom_extensions):
        return

    try:
        dataset = pydicom.dcmread(src_file)
    except:
        print(f'Not a DICOM file: {src_file}')
        return
        return

    # Replace placeholders in the pattern with actual metadata
    for attribute in ['PatientID', 'StudyDate', 'SeriesNumber', 'SeriesDescription']:
        value = get_dicom_attribute(dataset, attribute)
        pattern = pattern.replace(f'%{attribute}%', value)

    # Sanitize the file path
    dest_directory = sanitize_filepath(os.path.join(dest_base_dir, pattern), platform='auto')
    os.makedirs(dest_directory, exist_ok=True)
    shutil.copy2(src_file, os.path.join(dest_directory, os.path.basename(src_file)))

def copy_directory(src_dir, dest_dir, pattern):
    all_files = [os.path.join(root, file) for root, _, files in os.walk(src_dir) for file in files]
    for file in tqdm(all_files, desc="Processing", unit="file"):
        copy_dicom_image(file, dest_dir, pattern)


def sort_dicom(input_dir, output_dir):
    pattern = '%PatientID%/%StudyDate%/%SeriesNumber%_%SeriesDescription%'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    copy_directory(input_dir, output_dir, pattern)

def main():
    parser = argparse.ArgumentParser(description='Copy DICOM files into a structured directory')
    parser.add_argument('--dicomin', type=str, required=True, help='Path to the directory with unsorted DICOM files')
    parser.add_argument('--dicomout', type=str, required=True, help='Path to the directory where copied DICOM files will be stored')
    args = parser.parse_args()

    sort_dicom(args.dicomin, args.dicomout)

if __name__ == '__main__':
    main()
