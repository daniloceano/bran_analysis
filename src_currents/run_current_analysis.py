#!/usr/bin/env python3
"""
run_currents_analysis.py

Script to apply the analysis module (analyze_currents.py) to the CSV data file and produce outputs
for each depth across all data and seasons (DJF, MAM, JJA, SON).

Outputs for each depth and period:
- A CSV distribution table
- A PNG wind rose plot
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from current_analysis import generate_current_distribution_table, plot_wind_rose


def run_analysis(
    input_csv: str = "BRAN_outputs/dados_u_v_Ubu.csv",
    output_dir: str = "BRAN_outputs/Ubu",
    seasons: list = [None, 'DJF', 'MAM', 'JJA', 'SON']
) -> None:
    """
    Load input data, compute speed and direction, then generate distribution tables and wind roses
    for each unique depth and each specified period (None for all data).

    Parameters:
    -----------
    input_csv : path to the CSV file (must include 'Time','u','v','st_ocean')
    output_dir: base directory for saving results
    seasons   : list of periods; None for full dataset or season codes
    """
    # ensure base output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # load and preprocess data
    df = pd.read_csv(input_csv, parse_dates=['Time'], index_col='Time')
    df['velocidade'] = np.sqrt(df['u'] ** 2 + df['v'] ** 2)
    df['direcao'] = (np.degrees(np.arctan2(df['v'], df['u'])) + 360) % 360

    # iterate over all depths
    depths = sorted(df['st_ocean'].unique())
    for depth in depths:
        depth_dir = os.path.join(output_dir, f"depth_{depth}")
        os.makedirs(depth_dir, exist_ok=True)

        for period in seasons:
            label = 'all' if period is None else period

            # generate distribution table
            table = generate_current_distribution_table(
                df=df,
                depth=depth,
                period=period,
                mode='bins'
            )
            csv_path = os.path.join(depth_dir, f"distribution_{label}.csv")
            table.to_csv(csv_path)
            print(f"Saved distribution table for depth {depth}, period {label}: {csv_path}")

            # generate wind rose plot
            ax = plot_wind_rose(
                df=df,
                depth=depth,
                period=period
            )
            ax.set_title(f"Wind Rose ({label}) at depth {depth}")
            fig_path = os.path.join(depth_dir, f"windrose_{label}.png")
            ax.figure.savefig(fig_path, dpi=300, bbox_inches='tight')
            plt.close(ax.figure)
            print(f"Saved wind rose for depth {depth}, period {label}: {fig_path}")


if __name__ == '__main__':
    run_analysis()
