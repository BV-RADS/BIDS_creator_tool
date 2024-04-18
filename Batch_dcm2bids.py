#!/usr/bin/env python3
import os
import subprocess
import sys
import argparse
from datetime import datetime
import pandas as pd
import glob

"""
Simplified DICOM Processing Script

This script is designed to process DICOM files, executing dcm2bids for each subject and session,
and maintaining a record of study dates.

Usage:
    python script_name.py [options]

Options:
    --dicomin         Specify the path to the DICOM input directory.
    --nobids          Skip the conversion to BIDS format.
"""

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Processes DICOM files, executing dcm2bids for each subject and session."
    )
    parser.add_argument(
        '--dicomin',
        default="sourcedata",
        help='Specify the path to the DICOM input directory. Default is "sourcedata".'
    )
    parser.add_argument(
        '--nobids',
        action='store_true',
        help='Skip the conversion to BIDS format.'
    )
    return parser.parse_args()

def process_sessions(sourcedata_dir, bidsdir_folder, dcm2bids_config):
    studies_file = os.path.join(bidsdir_folder, "studies.tsv")
    # Check if the file exists and write the header if it doesn't
    if not os.path.exists(studies_file):
        with open(studies_file, "w") as file:
            file.write("subject\tsession\tdate\n")

    subjects = sorted([d for d in os.listdir(sourcedata_dir) if os.path.isdir(os.path.join(sourcedata_dir, d))])
    
    for subject in subjects:
        subject_dir = os.path.join(sourcedata_dir, subject)
        sessions = sorted([d for d in os.listdir(subject_dir) if os.path.isdir(os.path.join(subject_dir, d))])
        session_number = 1
        
        for session_dir in sessions:
            date = session_dir  # Assuming the folder name is the date
            session_label = f'ses-{str(session_number).zfill(2)}'
            session_path = os.path.join(subject_dir, session_dir)
            dcm2bids_cmd = [
                "dcm2bids", "-d", session_path, "-p", subject,
                "-s", session_label, "-c", dcm2bids_config, "-o", bidsdir_folder
            ]
            print("Executing:", ' '.join(dcm2bids_cmd))
            result = subprocess.run(dcm2bids_cmd, capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            
            # Write this session's data to the studies.tsv file
            with open(studies_file, "a") as file:
                file.write(f"{subject}\t{session_label}\t{date}\n")
            
            session_number += 1

def main():
    args = parse_arguments()
    bidsfolder = os.path.dirname(os.path.realpath(__file__))
    os.chdir(bidsfolder)

    # Directory setup
    sourcedata_dir = os.path.abspath(args.dicomin)
    bidsdir_folder = os.path.join(bidsfolder, "BIDSDIR")
    dcm2bids_config = "dcm2bids_config.json"

    # BIDS directory setup
    if not os.path.exists(bidsdir_folder):
        os.makedirs(bidsdir_folder, exist_ok=True)
        subprocess.run(["dcm2bids_scaffold", "-o", bidsdir_folder])

    # dcm2bids step
    if not args.nobids:
        process_sessions(sourcedata_dir, bidsdir_folder, dcm2bids_config)

    print("Batch process completed.")

if __name__ == "__main__":
    main()
