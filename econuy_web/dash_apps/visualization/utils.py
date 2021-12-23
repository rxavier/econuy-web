import re
from typing import Dict, List
from collections import Counter
from econuy import transform
from econuy.utils import datasets

import pandas as pd


def get_labels(tables: List[str]) -> List[str]:
    original_tables = datasets.original()
    original_tables = {k: v["description"] for k, v in original_tables.items()}
    custom_tables = datasets.custom()
    custom_tables = {k: v["description"] for k, v in custom_tables.items()}
    label_tables = []
    for table in tables:
        try:
            label_tables.append(original_tables[table])
        except KeyError:
            label_tables.append(custom_tables[table])
    label_tables = [re.sub(r" \(([^)]+)\)$", "", table) for table in label_tables]
    return label_tables


def dedup_colnames(
    dfs: List[pd.DataFrame], tables: List[str]
) -> Dict[str, pd.DataFrame]:
    label_tables = get_labels(tables)
    tables_nodup = []
    counter = Counter(label_tables)
    mod_counter = counter.copy()
    for table in label_tables:
        n = counter[table]
        if n > 1:
            if mod_counter[table] == counter[table]:
                tables_nodup.append(table)
            else:
                tables_nodup.append(f"{table} ({counter[table] - mod_counter[table]})")
            mod_counter[table] = mod_counter[table] - 1
        else:
            tables_nodup.append(table)

    indicator_names = [col for df in dfs for col in df.columns.get_level_values(0)]
    if len(indicator_names) > len(set(indicator_names)):
        for name, df in zip(tables_nodup, dfs):
            df.columns = df.columns.set_levels(
                f"{name} | " + df.columns.get_level_values(0), level=0
            )

    return dfs


def concat(dfs: List[pd.DataFrame]) -> List[pd.DataFrame]:
    freqs = [pd.infer_freq(df.index) for df in dfs]
    if all(freq == freqs[0] for freq in freqs):
        combined = pd.concat(dfs, axis=1)
    else:
        for freq_opt in ["A-DEC", "A", "Q-DEC", "Q", "M", "2W-SUN", "W-SUN"]:
            if freq_opt in freqs:
                output = []
                for df in dfs:
                    freq_df = pd.infer_freq(df.index)
                    if freq_df == freq_opt:
                        df_match = df.copy()
                    else:
                        type_df = df.columns.get_level_values("Tipo")[0]
                        unit_df = df.columns.get_level_values("Unidad")[0]
                        if type_df == "Stock":
                            df_match = transform.resample(
                                df, rule=freq_opt, operation="last"
                            )
                        elif type_df == "Flujo" and not any(
                            x in unit_df for x in ["%", "=", "Cambio"]
                        ):
                            df_match = transform.resample(
                                df, rule=freq_opt, operation="sum"
                            )
                        else:
                            df_match = transform.resample(
                                df, rule=freq_opt, operation="mean"
                            )
                    output.append(df_match)
                combined = pd.concat(output, axis=1)
                break
            else:
                continue

    return combined
