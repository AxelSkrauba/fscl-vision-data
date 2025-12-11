# test_region_-_misiones_ar_dataset

Wildlife image dataset from Test Region - Misiones AR. Prepared for few-shot classification with FSCL-Vision framework.

## Overview

- **Total Images**: 19
- **Total Species**: 2
- **Source**: iNaturalist
- **Created**: 2025-12-11T10:18:06.091867
- **Pipeline Version**: 1.0.0

## Species Included

- **Turdus rufiventris** (Rufous-bellied Thrush): 9 images
- **Ramphastos toco** (Toco Toucan): 10 images

## Directory Structure

```
test_region_-_misiones_ar_dataset/
├── images/
│   ├── {species_id}/
│   │   ├── {obs_id}_{photo_id}.jpg
│   │   └── {obs_id}_{photo_id}.json
│   └── ...
├── species_manifest.json
├── dataset_metadata.yaml
├── statistics.json
└── README.md
```

## Usage

### Loading the Dataset

```python
import json
from pathlib import Path

dataset_path = Path("test_region_-_misiones_ar_dataset")

# Load manifest
with open(dataset_path / "species_manifest.json") as f:
    manifest = json.load(f)

# Iterate over species
for species_id, species_data in manifest["classes"].items():
    print(f"{species_data['name']}: {species_data['count']} images")
    
    for img in species_data["images"]:
        img_path = dataset_path / "images" / species_id / img["filename"]
        # Load and process image...
```

## License & Attribution

Images are sourced from iNaturalist and retain their original licenses.
Each image's metadata JSON file contains license and attribution information.

**Important**: Check individual image licenses before commercial use.

## Citation

If you use this dataset, please cite:
- iNaturalist (https://www.inaturalist.org)
- Individual photographers (see image metadata)
- FSCL-Vision project
