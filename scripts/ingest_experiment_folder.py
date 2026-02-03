"""This script contains tools for taking an experiment folder and
tries to map all samples to datalab entries, across
potentially many different datalab instances.

It tends to need an extra massaging when working directly with
i11 data, which should be preserved as-is.

When given a filename with a log file e.g.:

file_number, sample_id, position, scan_time_seconds, description, spos_mm, time
1407334, LFV2, 4, 20.0, VT scan final file, 0.0, 2026-01-28 16:41:01.209000

It will try to match the sample_id to a datalab entry provided in a separate csv, with format:

sample_id, datalab_prefix, collection_id, creator_id
LFV2, grey, cy-43231, <long_user_id>

It will then attach the relevant scan data to the datalab entry and update the description,
adding it to a colleciton where requested.

It will also try to extract relevant metadata from the filename of the log, e.g., beam energies.

"""

import csv
from pathlib import Path
from datalab_api import DatalabClient

# ANSI color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

DATE = "2026-01-28"


def prepare_item_dict(scan_data, mapping):
    """
    Prepare datalab item dictionary from scan data and mapping.

    Args:
        scan_data: Dict with scan information (sample_id, description, etc.)
        mapping: Dict with mapping information (chemform, creator_id, etc.)

    Returns:
        Dict ready for datalab item creation
    """
    item_dict = {
        "name": scan_data["sample_id"],
        "type": "samples",
        "description": scan_data["description"],
        "creator_id": mapping["creator_id"],
        "date": DATE,
    }

    metadata = {}
    metadata["capillary_info"] = mapping.get("capillary_info")
    metadata["scan_time"] = mapping.get("scan_time")
    metadata["conditions"] = mapping.get("conditions")

    # Add metadata from mapping
    if mapping.get("chemform"):
        item_dict["chemform"] = mapping["chemform"]

    return item_dict, metadata


def get_scan_files(file_number, experiment_folder):
    """
    Get list of scan files for a given file number.

    Args:
        file_number: The scan file number
        experiment_folder: Path to experiment folder

    Returns:
        List of Path objects for files that exist
    """
    files = []

    # Only include summed file
    summed_file = experiment_folder / f"{file_number}_summed_mythen3.xye"
    if summed_file.exists():
        files.append(summed_file)

    return files


def load_sample_mapping(mapping_filename):
    """
    Load sample mapping from CSV file.

    Args:
        mapping_filename: Path to CSV mapping file

    Returns:
        Dict mapping sample_id to mapping data
    """
    sample_mapping = {}

    with open(mapping_filename, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_id = row["sample name"].strip()
            sample_mapping[sample_id] = {
                "refcode": row["datalab id"].strip()
                if row["datalab id"].strip()
                else None,
                "datalab_prefix": row["datalab prefix"].strip()
                if row["datalab prefix"].strip()
                else None,
                "chemform": row["chemistry"].strip()
                if row["chemistry"].strip()
                else None,
                "description": row["notes"].strip() if row["notes"].strip() else None,
                "name": row["name"].strip() if row["name"].strip() else None,
                "creator_id": row.get("datalab user", "").strip()
                if row.get("datalab user", "").strip()
                else None,
                "capillary_info": row.get("capillary_info", "").strip(),
                "scan_time": row.get("scan_time", "").strip(),
                "conditions": row.get("conditions", "").strip(),

            }

    return sample_mapping


def collect_scan_entries(
    log_filename,
    experiment_folder,
    sample_mapping,
    wavelength_angstrom: float,
    zero_error: float,
):
    """
    Parse log file and collect valid entries organized by prefix.

    Args:
        log_filename: Path to log file
        experiment_folder: Path to experiment folder
        sample_mapping: Dict of sample mappings
        wavelength_angstrom: Wavelength in Angstroms to attach to scan
        zero_error: Zero error value to attach to 2th values of scan

    Returns:
        Tuple of (entries_by_prefix dict, stats dict)
    """
    entries_by_prefix = {}
    stats = {
        "processed": 0,
        "matched": 0,
        "unmatched": 0,
        "no_file": 0,
    }

    experiment_code = experiment_folder.name

    with open(log_filename, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Skip header lines
            if "file_10number" in line or "file_number" in line:
                continue

            try:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 7:
                    continue

                file_number = parts[0]
                sample_id = parts[1]
                description = parts[4]

                stats["processed"] += 1

                # Match sample_id to mapping
                if sample_id not in sample_mapping:
                    print(
                        f"{YELLOW}⚠ {file_number:7s} | {sample_id:15s} | NO MATCH in mapping{RESET}"
                    )
                    stats["unmatched"] += 1
                    continue

                mapping = sample_mapping[sample_id]

                # Get scan files (only summed file)
                scan_files = get_scan_files(file_number, experiment_folder)
                if not scan_files:
                    print(
                        f"{YELLOW}⚠ {file_number:7s} | {sample_id:15s} | NO FILE{RESET}"
                    )
                    stats["no_file"] += 1
                    continue

                # Check for creator_id (MongoDB Object ID)
                if not mapping.get("creator_id"):
                    print(
                        f"{RED}⚠⚠⚠ {file_number:7s} | {sample_id:15s} | NO USER ID - CANNOT UPLOAD{RESET}"
                    )
                    stats["unmatched"] += 1
                    continue

                datalab_prefix = mapping["datalab_prefix"]
                if not datalab_prefix:
                    print(
                        f"{YELLOW}⚠ {file_number:7s} | {sample_id:15s} | NO PREFIX{RESET}"
                    )
                    continue

                stats["matched"] += 1

                # Prepare scan data
                scan_data = {
                    "sample_id": sample_id,
                    "description": description,
                }

                # Prepare entry
                entry = {
                    "file_number": file_number,
                    "sample_id": sample_id,
                    "scan_files": scan_files,
                    "existing_refcode": mapping.get("refcode"),
                }

                # Add wavelength metadata if available
                if wavelength_angstrom:
                    entry["wavelength_angstrom"] = wavelength_angstrom

                # Only prepare item_dict for new items (not updates)
                entry["item_dict"], entry["metadata"] = prepare_item_dict(scan_data, mapping)
                if entry.get("existing_refcode"):
                    entry.pop("item_dict")

                # Add to prefix group
                if datalab_prefix not in entries_by_prefix:
                    entries_by_prefix[datalab_prefix] = []
                entries_by_prefix[datalab_prefix].append(entry)

                # Show what we collected
                datalab_status = (
                    entry["existing_refcode"] if entry["existing_refcode"] else "new"
                )
                print(
                    f"{GREEN}✓ {file_number:7s} | {sample_id:15s} | {datalab_prefix:10s} | {datalab_status}{RESET}"
                )

            except Exception as e:
                print(f"{RED}✗ ERROR on line {line_num}: {e}{RESET}")
                continue

    return entries_by_prefix, stats


def process_log_file(
    log_filename, mapping_filename, wavelength_angstrom: float, zero_error: float
):
    """
    Process experiment log file and prepare data for datalab upload.

    Args:
        log_filename: Path to the scan log file
        mapping_filename: Path to the CSV mapping file
        wavelength_angstrom: Wavelength in Angstroms to attach to scan
        zero_error: Zero error value to attach to 2th values of scan

    """
    # Define datalab prefix to URL mapping
    prefix_to_url_mapping = {
        "grey": "https://datalab.odbx.science",
        "cliffe": "https://datalab.cliffegroup.co.uk",
        "mrlucsb": "https://datalab.mrl.ucsb.edu",
        "uh": "https://datalab.bocarslygroup.com",
        # Add more prefixes as needed
    }

    # Load sample mapping from CSV
    print(f"Reading mapping file: {mapping_filename}")
    try:
        sample_mapping = load_sample_mapping(mapping_filename)
        print(f"Successfully loaded {len(sample_mapping)} sample mappings")
    except Exception as e:
        print(f"{RED}Error reading mapping file: {e}{RESET}")
        return

    # Determine experiment folder
    log_path = Path(log_filename)
    experiment_folder = log_path.parent.parent  # Go up from processing/ to cy41066-2/
    experiment_code = experiment_folder.name

    print(f"Experiment folder: {experiment_folder}")

    # Collect and validate entries
    print(f"\nProcessing log file: {log_filename}\n")
    try:
        entries_by_prefix, stats = collect_scan_entries(
            log_filename,
            experiment_folder,
            sample_mapping,
            wavelength_angstrom,
            zero_error,
        )
    except Exception as e:
        print(f"{RED}Error reading log file: {e}{RESET}")
        return

    # Print collection summary
    print(f"\n{'=' * 60}")
    print(f"COLLECTION SUMMARY:")
    print(f"  Total scans: {stats['processed']}")
    print(f"  Matched with files: {stats['matched']}")
    print(f"  No mapping: {stats['unmatched']}")
    print(f"  No summed file: {stats['no_file']}")
    print(f"\nEntries by prefix:")
    for prefix, entries in entries_by_prefix.items():
        print(f"  {prefix}: {len(entries)} entries")
    print(f"{'=' * 60}")

    # Process entries by prefix
    print(f"\nProcessing uploads...\n")
    for prefix, entries in entries_by_prefix.items():

        url = prefix_to_url_mapping.get(prefix)
        if not url:
            print(
                f"{RED}✗ No URL mapping for prefix '{prefix}', skipping {len(entries)} entries{RESET}"
            )
            continue

        print(f"\n{GREEN}Processing {len(entries)} entries for {prefix} ({url}){RESET}")

        with DatalabClient(url) as client:
            client.authenticate()
            for entry in entries:
                try:
                    if entry["existing_refcode"]:
                        # For existing items, only attach files (don't overwrite metadata)
                        print(
                            f"  {GREEN}✓ Attaching to existing {entry['sample_id']} ({entry['existing_refcode']}){RESET}"
                        )
                        refcode = entry["existing_refcode"]
                        # Check refcode does exist
                        item = client.get_item(refcode=refcode)
                        item_id = item["item_id"]
                    else:
                        # Create new item with full metadata
                        item = client.create_item(
                            item_id=None, item_data=entry["item_dict"]
                        )
                        item_id = item["item_id"]
                        refcode = item["refcode"]
                        print(
                            f"  {GREEN}✓ Created {entry['sample_id']} ({item_id}: {refcode}){RESET}"
                        )

                    # Upload scan files
                    for scan_file in entry["scan_files"]:
                        file_resp = client.upload_file(item_id, scan_file)
                        file_id = file_resp["file_id"]
                        print(f"    📎 Uploaded {scan_file.name}")

                        # Create XRD data block with wavelength metadata
                        block_data = {}
                        block_data["file_id"] = file_id
                        block_data["wavelength"] = entry["wavelength_angstrom"]
                        block_data["title"] = (
                            f"Powder XRD: Diamond I11 {DATE} - ({experiment_code})"
                        )
                        block_data["freeform_comment"] = f"""
Diamond Light Source BAG I11 ({experiment_code})</br>
{DATE}</br>
Mythen Detector</br>
{entry['metadata']['capillary_info']}</br>
{entry['metadata']['scan_time']} min scan</br>
Zero-error: {zero_error:.8f}°</br>
Wavelength: {wavelength_angstrom:.8f} Å</br>
{entry['metadata']['conditions']}</br>
Scan number: {entry['file_number']}</br></br>
Please acknowledge the "Cambridge BAG for new materials characterisation and structure-property relationships for a zero-carbon future ({experiment_code})" in publications.
"""

                        block = client.create_data_block(
                            item_id, block_type="xrd",
                        )
                        client.update_data_block(
                            item_id, block["block_id"], "xrd", block_data
                        )
                        print(f"    Created XRD block for {scan_file.name}")
                        if "wavelength_angstrom" in entry:
                            print(f"    with λ = {entry['wavelength_angstrom']:.4f} Å")

                except Exception as e:
                    print(f"  {RED}✗ Failed {entry['sample_id']}: {e}{RESET}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest experiment folder log file into datalab instances."
    )
    parser.add_argument(
        "log_filename", type=str, help="Path to the log file containing scan data."
    )
    parser.add_argument(
        "mapping_filename",
        type=str,
        help="Path to the CSV file mapping sample IDs to datalab entries.",
    )

    parser.add_argument(
        "--wavelength_angstrom",
        type=float,
        help="Wavelength in Angstroms to attach to each scan (if applicable).",
    )

    parser.add_argument(
        "--zero_error",
        type=float,
        help="Zero error value to attach to 2th values of scan (if applicable)",
    )

    args = parser.parse_args()

    process_log_file(
        args.log_filename,
        args.mapping_filename,
        args.wavelength_angstrom,
        args.zero_error,
    )
