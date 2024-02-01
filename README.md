# DICOM Sorting and Anonymization Tool

A Python script to organize and optionally anonymize DICOM files into a structured directory hierarchy based on their metadata.

## Description

This script reads DICOM files from a specified input directory (`--dicomin`), optionally anonymizes them based on the provided flags, and organizes the files into a structured directory hierarchy in a specified output directory (`--dicomout`), using metadata such as Patient ID, Study Date, Series Number, and Series Description.

## Features

- **Metadata Extraction**: Reads DICOM files and extracts relevant metadata.
- **Structured Organization**: Organizes DICOM files into a hierarchy based on their metadata.
- **Optional Anonymization**: Provides options to anonymize specific DICOM tags.
- **ID Correlation**: Allows for PatientID anonymization using an external correlation table.

## Installation

The script requires Python 3 and additional packages: `tqdm`, `pydicom`, and `pathvalidate`. Install these dependencies with:


```bash
pip install tqdm pydicom pathvalidate
```

## Usage

Basic usage for sorting DICOM files:

```bash
python dicom_sorting_anonimyzing_tool.py --dicomin /path/to/unsorted --dicomout /path/to/sorted
```

To also anonymize DICOM files (removing Patient Name and Date of Birth, but not Patient ID):

```bash
python dicom_sorting_anonimyzing_tool.py --dicomin /path/to/unsorted --dicomout /path/to/sorted --anonymize
```

To replace PatientID based on a correlation table:

```bash
python dicom_sorting_anonimyzing_tool.py --dicomin /path/to/unsorted --dicomout /path/to/sorted --anonymize --ID_correlation /path/to/ID_correlation.txt
```

### Arguments

- **`--dicomin`**: Path to the directory containing unsorted DICOM files.
- **`--dicomout`**: Path to the directory where the sorted DICOM files will be stored based on their metadata.
- **`--anonymize`**: (Optional) Anonymizes Patient Name and Date of Birth.
- **`--ID_correlation`**: (Optional) Path to a correlation file for anonymizing PatientID. The file should contain old and new IDs, separated by a comma, space, or tab.


## Anonymization Details
- The `--anonymize` flag will remove the Patient Name and Date of Birth but will not alter the Patient ID.
- Providing the `--ID_correlation` flag with an anonymizing table allows for the PatientID to be anonymized according to the table. If the ID is not found in the table, it will remain unchanged.

## Disclaimer

DICOM headers are complex and can be vendor-specific. While this tool aims to provide basic anonymization functionality, it does not guarantee full anonymization of all potentially identifiable information. Careful review of DICOM headers is necessary to ensure compliance with privacy standards and regulations.

