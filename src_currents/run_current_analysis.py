#!/usr/bin/env python3
"""
run_currents_analysis.py

Script to apply the analysis module (analyze_currents.py) to the CSV data file and produce output for
- All data combined
- Each meteorological season (DJF, MAM, JJA, SON)

Outputs for each run:
- A CSV distribution table
- A PNG wind rose plot
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from current_analysis import generate_current_distribution_table, plot_wind_rose


def run_analysis(
    input_csv: str = "dados_u_v_Ubu.csv",
    depth: float = 2.5,
    output_dir: str = "outputs",
    seasons: list = [None, 'DJF', 'MAM', 'JJA', 'SON']
) -> None:
    """
    Load input data, compute speed and direction, then generate distribution tables and wind roses
    for the full dataset and each specified season.

    Parameters:
    -----------
    input_csv : path to the CSV file (must include 'Time','u','v','st_ocean')
    depth     : depth value to filter (st_ocean)
    output_dir: directory for saving results
    seasons   : list of periods; None for full dataset or season codes
    """
    os.makedirs(output_dir, exist_ok=True)

    # Load and preprocess data
    df = pd.read_csv(input_csv, parse_dates=['Time'], index_col='Time')
    df['velocidade'] = np.sqrt(df['u'] ** 2 + df['v'] ** 2)
    df['direcao'] = (np.degrees(np.arctan2(df['v'], df['u'])) + 360) % 360

    for period in seasons:
        label = 'all' if period is None else period
        # Generate distribution table
        table = generate_current_distribution_table(
            df=df,
            depth=depth,
            period=period,
            mode='bins'
        )
        csv_path = os.path.join(output_dir, f"distribution_{label}.csv")
        table.to_csv(csv_path)
        print(f"Saved distribution table: {csv_path}")

        # Generate wind rose plot
        ax = plot_wind_rose(
            df=df,
            depth=depth,
            period=period
        )
        ax.set_title(f"Wind Rose ({label}) at depth {depth}")
        fig_path = os.path.join(output_dir, f"windrose_{label}.png")
        ax.figure.savefig(fig_path, dpi=300, bbox_inches='tight')
        plt.close(ax.figure)
        print(f"Saved wind rose: {fig_path}")


if __name__ == '__main__':
    run_analysis()
