import re

from econuy.utils.operations import DATASETS

table_options = {
    name: re.sub(r"\([A-z0-9\-\,\s]+\)", "", metadata["description"]).strip()
    for name, metadata in DATASETS.items()
    if not metadata["disabled"] and not metadata["auxiliary"]
}
