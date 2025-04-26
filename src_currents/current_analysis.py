#!/usr/bin/env python3
"""
Unified script to load ocean current data, generate distribution table, and plot wind rose.
"""
from typing import List, Optional
import argparse
import os
import logging

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from windrose import WindroseAxes


def generate_current_distribution_table(
    df: pd.DataFrame,
    depth: float,
    speed_thresholds: Optional[List[float]] = None,
    direction_bins: Optional[List[float]] = None,
    period: Optional[str] = None,
    mode: str = "bins"
) -> pd.DataFrame:
    """
    Generate a binned or cumulative distribution table of ocean current speeds and directions.

    Parameters:
    -----------
    df               : pd.DataFrame with columns ['st_ocean', 'velocidade', 'direcao'] and DatetimeIndex
    depth            : depth (st_ocean) value for filtering
    speed_thresholds : optional list of speed bin edges (m/s)
    direction_bins   : optional list of direction bin centers (°)
    period           : optional filter by month name or season ('DJF', 'MAM', 'JJA', 'SON')
    mode             : 'bins' for binned or 'accumulate' for cumulative distribution

    Returns:
    --------
    pd.DataFrame: distribution table with MultiIndex columns (Direction, Degrees)
    """
    if speed_thresholds is None:
        speed_thresholds = np.arange(0, 0.51, 0.05).tolist()
    if direction_bins is None:
        direction_bins = list(np.arange(0, 361, 30))

    subset = df[df['st_ocean'] == depth]
    speed = subset['velocidade']
    direction = subset['direcao']

    if period:
        seasons = {'DJF': [12,1,2], 'MAM': [3,4,5], 'JJA': [6,7,8], 'SON': [9,10,11]}
        if period in seasons:
            mask = speed.index.month.isin(seasons[period])
        else:
            month = pd.to_datetime(period, format='%B').month
            mask = speed.index.month == month
        speed = speed[mask]
        direction = direction[mask]

    current_df = pd.DataFrame({'speed': speed, 'direction': direction})

    bins_dir = np.arange(-15, 375, 30)
    labels_dir = direction_bins[:-1]
    current_df['DirBin'] = pd.cut(current_df['direction'], bins=bins_dir, right=False, labels=labels_dir)
    current_df.loc[current_df['direction'] > 345, 'DirBin'] = 0

    labels_speed = [f"{round(speed_thresholds[i], 2)}-{round(speed_thresholds[i+1], 2)}" for i in range(len(speed_thresholds)-1)]
    current_df['SpeedBin'] = pd.cut(current_df['speed'], bins=speed_thresholds, right=False, labels=labels_speed)

    dist = pd.crosstab(current_df['SpeedBin'], current_df['DirBin'])
    dist = dist * 100 / len(current_df)
    if mode == 'accumulate':
        dist = dist.cumsum(axis=0)
    dist = dist.round(2)

    dist['Omni'] = dist.sum(axis=1)
    dist.loc['Total'] = dist.sum()
    dist.loc['Mean'] = dist.iloc[:-1].mean().round(2)
    dist.loc['Maximum'] = dist.iloc[:-2].max().round(2)

    if mode == 'accumulate':
        dist.index = [f'< {int(lbl)}' for lbl in dist.index[:-3]] + ['Total', 'Mean', 'Maximum']

    directions = ["N","NNE","ENE","E","ESE","SSE","S","SSW","WSW","W","WNW","NNW","Omni"]
    degrees = [f"{d}°" for d in direction_bins[:-1]] + ['']
    dist.columns = pd.MultiIndex.from_tuples(
        [(directions[i], degrees[i]) for i in range(len(directions))],
        names=["Direction","Degrees"]
    )
    dist = dist.round(2)
    return dist


def plot_wind_rose(
    df: pd.DataFrame,
    depth: float,
    averaging_window: Optional[str] = None,
    colormap: str = 'viridis',
    period: Optional[str] = None
) -> WindroseAxes:
    """
    Create a wind rose plot for specified depth and period.
    """
    subset = df[df['st_ocean'] == depth]
    speed = subset['velocidade']
    direction = subset['direcao']

    if period:
        seasons = {'DJF': [12,1,2], 'MAM': [3,4,5], 'JJA': [6,7,8], 'SON': [9,10,11]}
        if period in seasons:
            mask = speed.index.month.isin(seasons[period])
        else:
            month = pd.to_datetime(period, format='%B').month
            mask = speed.index.month == month
        speed = speed[mask]
        direction = direction[mask]

    df_plot = pd.DataFrame({'speed': speed, 'direction': direction})
    if averaging_window:
        df_plot = df_plot.resample(averaging_window).mean()

    cmap = plt.get_cmap(colormap)
    ax = WindroseAxes.from_ax()
    ax.bar(
        df_plot['direction'],
        df_plot['speed'],
        normed=True,
        opening=0.8,
        edgecolor='white',
        cmap=cmap
    )
    ax.legend()
    return ax


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate ocean current distribution table and wind rose plot."
    )
    parser.add_argument(
        '-i', '--input', required=True,
        help='Path to input CSV file.'
    )
    parser.add_argument(
        '-d', '--depth', type=float, default=2.5,
        help='Depth (st_ocean) for filtering.'
    )
    parser.add_argument(
        '-p', '--period', default=None,
        help='Optional period filter (month name or season code).'
    )
    parser.add_argument(
        '-o', '--output_dir', default='outputs',
        help='Directory to save outputs.'
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info(f'Reading data from {args.input}')
    df = pd.read_csv(
        args.input,
        parse_dates=['Time'],
        index_col='Time'
    )
    df['velocidade'] = np.sqrt(df['u']**2 + df['v']**2)
    df['direcao'] = (np.degrees(np.arctan2(df['v'], df['u'])) + 360) % 360

    logger.info('Generating distribution table')
    table = generate_current_distribution_table(
        df=df,
        depth=args.depth,
        period=args.period,
        mode='bins'
    )
    table_path = os.path.join(args.output_dir, 'current_distribution_table.csv')
    table.to_csv(table_path)
    logger.info(f'Distribution table saved to {table_path}')

    logger.info('Plotting wind rose')
    ax = plot_wind_rose(
        df=df,
        depth=args.depth,
        period=args.period
    )
    ax.set_title(f'Wind Rose at depth {args.depth}')
    fig_path = os.path.join(args.output_dir, 'windrose_plot.png')
    ax.figure.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close(ax.figure)
    logger.info(f'Wind rose saved to {fig_path}')


if __name__ == '__main__':
    main()
