#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import pydicom
from pathvalidate import sanitize_filepath
from tqdm import tqdm
import re
import subprocess

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

date_counter = {}
sequence_counter = {}
image_counter = {}

def format_counter(counter, prefix, length):
    return f"{prefix}{counter:0{length}d}"

def get_date_id(patient_id, study_date):
    key = (patient_id, study_date)
    if key not in date_counter:
        date_counter[key] = len(date_counter) + 1
    return format_counter(date_counter[key], 'DAT', 4)

def get_sequence_id(patient_id, study_date, series_number):
    key = (patient_id, study_date, series_number)
    if key not in sequence_counter:
        sequence_counter[key] = len(sequence_counter) + 1
    return format_counter(sequence_counter[key], 'SEQ', 4)

def get_image_filename(directory):
    if directory not in image_counter:
        image_counter[directory] = 0
    image_counter[directory] += 1
    return f"IM{image_counter[directory]:06d}"

def copy_dicom_image(src_file, dest_base_dir, anonymize=False, id_map=None):
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

    patient_id = get_dicom_attribute(dataset, 'PatientID')
    study_date = get_dicom_attribute(dataset, 'StudyDate')
    series_number = get_dicom_attribute(dataset, 'SeriesNumber')

    dat_id = get_date_id(patient_id, study_date)
    seq_id = get_sequence_id(patient_id, study_date, series_number)

    dest_directory = sanitize_filepath(os.path.join(dest_base_dir, patient_id, "dicom" ,dat_id, seq_id), platform='auto')
    os.makedirs(dest_directory, exist_ok=True)
    image_filename = get_image_filename(dest_directory)
    dataset.save_as(os.path.join(dest_directory, image_filename))

def copy_directory(src_dir, dest_dir, anonymize, id_map):
    all_files = [os.path.join(root, file) for root, _, files in os.walk(src_dir) for file in files]
    for file in tqdm(all_files, desc="Processing", unit="file"):
        copy_dicom_image(file, dest_dir, anonymize, id_map)

def sort_dicom(input_dir, output_dir, anonymize, id_map):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    copy_directory(input_dir, output_dir, anonymize, id_map)

missing_ids = set()

def create_dicomdir_for_subjects(base_path):
    # List all subdirectories in the base directory which are expected to be patient IDs
    subjects = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
    for subject in subjects:
        dicom_dir = os.path.join(base_path, subject, "dicom")
        dicomdir_path = os.path.join(base_path, subject, "DICOMDIR")
        # Construct the command to create DICOMDIR, including the invent option
        command = [
            "dcmmkdir", "+r", "+id", dicom_dir, "+D", dicomdir_path, "-Pgp", "-A", "+I"
        ]
        print(f"Running command: {' '.join(command)}")  # Debugging output to see the command
        subprocess.run(command, check=True)  # Execute the command


def main():
    
    parser = argparse.ArgumentParser(
        description="This script organizes DICOM files into a structured directory format, optionally anonymizes them, and generates DICOMDIR files for each patient. "
                    "It is designed to handle unsorted DICOM files, apply optional anonymization to enhance privacy, and facilitate the creation of compliant DICOMDIR structures for improved data management.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--dicomin', 
        type=str, 
        required=True, 
        help='Path to the input directory containing unsorted DICOM files.'
    )
    parser.add_argument(
        '--dicomout', 
        type=str, 
        required=True, 
        help='Path to the output directory where structured and optionally anonymized DICOM files will be stored. '
             'This directory will also contain DICOMDIR files for each patient subdirectory.'
    )
    parser.add_argument(
        '--anonymize', 
        action='store_true', 
        help='If specified, anonymizes DICOM tags such as PatientName and PatientBirthDate to protect patient privacy.'
    )
    parser.add_argument(
        '--ID_correlation', 
        type=str, 
        help='Optional path to a correlation file mapping old PatientIDs to new PatientIDs for further anonymization.'
    )
    args = parser.parse_args()
    

    id_map = read_id_correlation(args.ID_correlation) if args.ID_correlation else None

    sort_dicom(args.dicomin, args.dicomout, args.anonymize, id_map)

    if missing_ids:
        log_file_path = 'missing_patient_ids.log'
        with open(log_file_path, 'w') as log_file:
            for missing_id in missing_ids:
                log_file.write(f'{missing_id}\n')
        print(f"Missing PatientIDs logged in '{log_file_path}'.")

    # After sorting, create DICOMDIR for each subject
    create_dicomdir_for_subjects(args.dicomout)

if __name__ == '__main__':
    main()
