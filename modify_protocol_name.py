#!/usr/bin/env python
import os
import argparse
import pydicom
from tqdm import tqdm
import multiprocessing
import logging

# Set up basic logging (errors will be printed to stderr)
logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')

def process_file(file_path):
    """
    Opens a DICOM file, appends the immediate parent folder's basename to the Protocol Name,
    and saves the modified file in-place.
    """
    try:
        # Use force=True to try to read files that might not strictly conform to DICOM standards
        ds = pydicom.dcmread(file_path, force=True)
    except Exception as e:
        logging.error(f"Error reading file '{file_path}': {e}")
        return file_path, False

    try:
        # Get the immediate parent folder's basename
        parent_folder = os.path.basename(os.path.dirname(file_path))
        # Get the current Protocol Name (if not present, default to empty string)
        current_protocol = getattr(ds, "ProtocolName", "")
        # Append with a space separator if ProtocolName already exists
        new_protocol = f"{parent_folder}".strip() if current_protocol else parent_folder
        ds.ProtocolName = new_protocol

        # Save the modified DICOM file in place
        ds.save_as(file_path)
        return file_path, True
    except Exception as e:
        logging.error(f"Error processing file '{file_path}': {e}")
        return file_path, False

def main():
    parser = argparse.ArgumentParser(
        description="Recursively append the immediate parent folder's basename to the "
                    "DICOM tag Protocol Name (0018,1030) in every file found. "
                    "All files are treated as DICOM files."
    )
    parser.add_argument("dicom_folder", type=str, help="Path to the root folder containing DICOM files")
    args = parser.parse_args()

    # Walk the directory tree and collect all files (regardless of extension)
    all_files = []
    for dirpath, _, filenames in os.walk(args.dicom_folder):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            all_files.append(file_path)

    total_files = len(all_files)
    if total_files == 0:
        print("No files found in the specified folder.")
        return

    print(f"Found {total_files} files. Processing...")

    success_count = 0
    failure_count = 0

    # Process files in parallel using a multiprocessing Pool and display progress with tqdm
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        results = list(tqdm(pool.imap_unordered(process_file, all_files), total=total_files))

    for _, success in results:
        if success:
            success_count += 1
        else:
            failure_count += 1

    print(f"\nProcessing completed. Successes: {success_count}, Failures: {failure_count}")

if __name__ == "__main__":
    multiprocessing.freeze_support()  # For Windows support
    main()
