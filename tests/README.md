Test utilities

This folder contains helper scripts for working with dummy data.

Primary script (creates real resources in OCI)
- `tests/create_dummy_oci_data.py`: Creates buckets and uploads dummy objects in your OCI account using local config or instance principals.

Args
- `--region`: OCI region (e.g., `us-ashburn-1`).
- `--compartment-id`: Target compartment OCID to create buckets in.
- `--namespace`: Object Storage namespace (optional; auto-detected if omitted).
- `--bucket-prefix`: Prefix for bucket names. Default `ods-dummy-`.
- `--bucket-count`: Number of buckets to create. Default 2.
- `--prefixes`: Comma-separated object prefixes (e.g., `dev/,prod/`). Default `dev/,prod/`.
- `--per-prefix`: Objects per prefix per bucket. Default 5.
- `--suffix`: Optional suffix for bucket names; default is epoch seconds.
- `--dry-run`: Show planned actions without creating resources.

Example
- `python tests/create_dummy_oci_data.py --region us-ashburn-1 --compartment-id ocid1.compartment.oc1..abc123 --bucket-count 2 --prefixes dev/,prod/ --per-prefix 3`
