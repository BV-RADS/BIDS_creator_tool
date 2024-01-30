# DICOM Sorter

A simple Python script to organize DICOM files into a structured directory hierarchy based on their metadata.

## Description

This script reads DICOM files from a specified input directory, extracts metadata such as Patient ID, Study Date, Series Number, and Series Description, and uses this information to organize the files into a structured directory hierarchy in a specified output directory.

## Features

- Reads DICOM files and extracts relevant metadata.
- Organizes DICOM files into a structured directory hierarchy based on their metadata.
- Skips non-DICOM files to avoid unnecessary processing.

## Installation

The script requires Python 3 and two Python packages: `tqdm` and `pydicom`. To install these dependencies, run the following command:

```bash
pip install tqdm pydicom
```

## Usage

```bash
python dicom_sorter.py --dicomin /path/to/unsorted/dicom/files --dicomout /path/to/sorted/dicom/files
```

### Arguments

- `--dicomin`: Path to the directory containing unsorted DICOM files.
- `--dicomout`: Path to the directory where the sorted DICOM files will be stored based on their metadata.

## Disclaimer

This script is provided "as is", without warranty of any kind. Use at your own risk.
