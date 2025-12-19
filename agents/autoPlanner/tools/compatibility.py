import pandas as pd
from agents.autoPlanner.tools.machine_processing import check_newest_machine_layout

#----------------------------------------------#
# Mold-Machine compatibility matrix calculator #
#----------------------------------------------#

def create_mold_machine_compatibility_matrix(
        machineInfo_df: pd.DataFrame,
        moldInfo_df: pd.DataFrame,
        validate_data: bool = True) -> pd.DataFrame:
    """
    Create a binary compatibility matrix between molds and machines based on tonnage.

    Parameters
    ----------
    machineInfo_df : pd.DataFrame
        Machine data including 'machineTonnage' and 'machineCode'.
    moldInfo_df : pd.DataFrame
        Mold data including 'moldNo' and 'machineTonnage' (may contain multiple values separated by '/').
    validate_data : bool, default True
        Whether to validate input data and print summary statistics.

    Returns
    -------
    pd.DataFrame
        Binary compatibility matrix:
            - Index: moldNo
            - Columns: machineCode
            - Values: 1 if compatible, 0 if not
    """
    try:
        # 1. Process mold data (split tonnage list)
        mold_info_df = moldInfo_df.copy()
        mold_info_df["machineTonnage"] = mold_info_df["machineTonnage"].astype(str).str.split("/")

        # 2. Process machine data
        machine_info_df = check_newest_machine_layout(machineInfo_df)
        machine_info_df["machineTonnage"] = machine_info_df["machineTonnage"].astype(str)

        # 3. Check for missing data
        if validate_data:
          machine_missing = machine_info_df['machineTonnage'].isna().sum()
          mold_missing = moldInfo_df['machineTonnage'].isna().sum()

          if machine_missing > 0:
              print(f"Warning: {machine_missing} machines have no tonnage information")

          if mold_missing > 0:
              print(f"Warning: {mold_missing} molds have no tonnage information")

          # Check for empty data
          if machine_info_df.empty:
              raise ValueError("Machine data is empty")

          if moldInfo_df.empty:
              raise ValueError("Mold data is empty")

        # 4. Expand molds by tonnage
        tonnage_expanded_df = mold_info_df.explode("machineTonnage", ignore_index=True)

        # 5. Group machines by tonnage and merge
        machine_grouped = (
            machine_info_df.groupby("machineTonnage")["machineCode"]
            .unique()
            .reset_index()
        )
        merged_df = tonnage_expanded_df.merge(
            machine_grouped, on="machineTonnage", how="left"
        ).dropna(subset=["machineCode"])

        if merged_df.empty:
            print("⚠️ No mold-machine compatibility found based on tonnage.")
            return pd.DataFrame()

        # 6. Expand multiple compatible machines per mold-tonnage
        machine_expanded_df = merged_df.explode("machineCode", ignore_index=True)

        # 7. Build binary compatibility matrix
        compatibility_matrix = (
            machine_expanded_df.assign(value=1)
            .pivot_table(index="moldNo", columns="machineCode", values="value", fill_value=0).astype(int)
        )

        return compatibility_matrix

    except Exception as e:
        raise RuntimeError(f"Error creating mold-machine compatibility matrix: {e}")