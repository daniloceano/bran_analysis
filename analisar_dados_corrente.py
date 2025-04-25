import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from windrose import WindroseAxes

def generate_current_distribution_table(df, depth, speed_thresholds=None, direction_bins=None, period=None, mode='bins'):
    """
    Generate a cumulative or binned wind distribution table.
    
    Parameters:
    -----------
    height : int
        The height at which to calculate the wind distribution.

    speed_thresholds : list, optional
        List of wind speed thresholds (in m/s). Default is [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32].

    direction_bins : list, optional
        List of direction bin edges (in degrees). Default is [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360].

    period : str, optional
        The specific period to filter by. Can be a month ('January', 'February', etc.) or a season ('DJF', 'JJA', etc.).
        If None, the distribution will be calculated for the entire dataset.

    mode : str, optional
        The mode of calculation. Either 'accumulate' for cumulative probabilities or 'bins' for binned probabilities. Default is 'accumulate'.

    Returns:
    --------
    pd.DataFrame
        A DataFrame representing the wind distribution table, where rows represent wind speed thresholds or bins, 
        columns are Current Direction bins (covering ±15°), and values are percentages of occurrence (formatted to 2 decimal places).
    """
    
    # Default thresholds if none provided
    if speed_thresholds is None:
        speed_thresholds = np.arange(0, 0.51, 0.05) 
    
    if direction_bins is None:
        direction_bins = np.arange(0, 361, 30)  # Centered on 0°, 30°, 60°, etc.

    # Retrieve wind speed and direction for the specified height
    speed = df[df['st_ocean'] == depth]['velocidade']
    direction = df[df['st_ocean'] == depth]['direcao']
    
    # Filter data based on the period (month or season)
    if period:
        # Define seasonal periods for meteorological seasons
        seasons = {
            'DJF': [12, 1, 2],
            'MAM': [3, 4, 5],
            'JJA': [6, 7, 8],
            'SON': [9, 10, 11]
        }

        if period in seasons:
            # Filter by season
            speed = speed[speed.index.month.isin(seasons[period])]
            direction = direction[speed.index.month.isin(seasons[period])]
        else:
            # Filter by specific month
            month_num = pd.to_datetime(period, format='%B').month
            speed = speed[speed.index.month == month_num]
            direction = direction[speed.index.month == month_num]

    # Create a DataFrame with wind speed and direction
    current_df = pd.DataFrame({'Wind Speed (m/s)': speed, 'Current Direction (°)': direction})

    # Bin Current Directions (±15° around the center)
    current_df['Direction Bin'] = pd.cut(current_df['Current Direction (°)'], bins=np.arange(-15, 375, 30), right=False, labels=direction_bins[:-1])
    current_df.loc[current_df['Current Direction (°)'] > 345, 'Direction Bin'] = 0 # Wrap around to 0° for the last bin

    # Bin Current Speeds
    speed_bin_labels = [f"{round(speed_thresholds[i], 2)}-{round(speed_thresholds[i+1], 2)}" 
                        for i in range(len(speed_thresholds) - 1)]
    current_df['Speed Bin'] = pd.cut(current_df['Wind Speed (m/s)'], bins=speed_thresholds, right=False, labels=speed_bin_labels)

    # Create contigency table
    current_distribution = pd.crosstab(current_df['Speed Bin'], current_df['Direction Bin'])    

    # Normalize the distribution to get percentages
    current_distribution = current_distribution * 100 / len(current_df)

    # If mode is 'accumulate', calculate cumulative distribution
    if mode == 'accumulate':
        current_distribution = current_distribution.cumsum(axis=0)

    # Round the values to 2 decimal places
    current_distribution = current_distribution.round(2)

    # Primeiro, remova a formatação para garantir que a soma ocorra corretamente
    current_distribution = current_distribution.apply(pd.to_numeric, errors='coerce')

    # Add a column for the "Omni" (all directions) distribution
    current_distribution['Omni'] = current_distribution.sum(axis=1)

    # Calcular a soma dos valores numéricos para a linha "Total"
    current_distribution.loc['Total'] = current_distribution.sum(axis=0)

    # Calculate the mean for each column, excluding the "Omni" column and "Total" row
    current_distribution.loc['Mean'] = current_distribution.iloc[~current_distribution.index.isin(['Total', 'Mean', 'Maximum']), :-1].mean(axis=0).round(2)
    current_distribution.loc['Mean', 'Omni'] = current_distribution.loc['Mean'].mean().round(2)

    # Calculate the maximum for each column, and set the Omni column to the maximum of the maximum values
    current_distribution.loc['Maximum'] = current_distribution.iloc[~current_distribution.index.isin(['Total', 'Mean', 'Maximum']), :-1].max().round(2)
    current_distribution.loc['Maximum', 'Omni'] = current_distribution.loc['Maximum'].max()

    # Format the table to have only 2 decimal places
    current_distribution = current_distribution.map(lambda x: f'{x:.2f}' if isinstance(x, (float, int)) else x)

    # Rename the index and columns
    if mode == 'accumulate':
        current_distribution.index = [f'< {int(i)}' for i in current_distribution.index[:-3]] + ['Total', 'Mean', 'Maximum']
    elif mode == 'bins':
        current_distribution.index = list(current_distribution.index[:-3]) + ['Total', 'Mean', 'Maximum']

    # Add a multi-level header to the columns to include Current Direction labels
    direction_labels = ["N", "NNE", "ENE", "E", "ESE", "SSE", "S", "SSW", "WSW", "W", "WNW", "NNW", "Omni"]
    current_distribution.columns = pd.MultiIndex.from_tuples(
        [(label, f"{deg}°") if label != "Omni" else ("Omni", "") for label, deg in zip(direction_labels, list(direction_bins[:-1]) + [None])],
        names=["Direction", "Degrees"]
    )

    return current_distribution

def plot_wind_rose(df, depth, averaging_window=None, colormap='coolwarm', period=None):
    """
    Plot a wind rose using wind speed and direction data, with an option to average the data over a specified time window,
    and filter by a specific month or season.

    Parameters:
    -----------
    depth : int
        The depth at which to plot the wind rose.

    averaging_window : str, optional
        A resampling rule to average the data over a specified time window (e.g., '1H' for 1 hour).
        Default is None, meaning no averaging will be performed.

    colormap : str, optional
        The colormap to use for the wind rose plot. Default is 'viridis'.
    
    period : str, optional
        The specific period to filter by. Can be a month ('January', 'February', etc.) or a season ('DJF', 'JJA', etc.).
        If None, the distribution will be calculated for the entire dataset.

    Returns:
    --------
    ax : WindroseAxes
        The WindroseAxes instance used for the plot, allowing the user to modify or save the plot.

    Example usage:
    --------------
    ax = ds_accessor.plot_wind_rose(40, averaging_window='1H', colormap='coolwarm', period='DJF')
    ax.set_title("Modified Title")  # Example of modifying the plot after it is created
    ax.figure.savefig('windrose_plot.png')  # Example of saving the figure
    """
    # Retrieve current speed and direction for the specified height
    current_speed = df[df['st_ocean'] == depth]['velocidade']
    current_direction = df[df['st_ocean'] == depth]['direcao']

    # Filter data based on the period (month or season)
    if period:
        # Define seasonal periods for meteorological seasons
        seasons = {
            'DJF': [12, 1, 2],
            'MAM': [3, 4, 5],
            'JJA': [6, 7, 8],
            'SON': [9, 10, 11]
        }

        if period in seasons:
            # Filter by season
            current_speed = current_speed.sel(time=current_speed['time.month'].isin(seasons[period]))
            current_direction = current_direction.sel(time=current_direction['time.month'].isin(seasons[period]))
        else:
            # Filter by specific month
            month_num = pd.to_datetime(period, format='%B').month
            current_speed = current_speed.sel(time=current_speed['time.month'] == month_num)
            current_direction = current_direction.sel(time=current_direction['time.month'] == month_num)

    # Combine wind speed and direction into a DataFrame
    current_df = pd.DataFrame({'Current Speed (m/s)': current_speed, 'Current Direction (°)': current_direction})

    # If averaging_window is provided, perform resampling and averaging
    if averaging_window:
        current_df = current_df.resample(averaging_window).mean()

    # Convert colormap string to a colormap object
    cmap = plt.get_cmap(colormap)

    # Create the wind rose plot
    ax = WindroseAxes.from_ax()
    ax.bar(current_df['Current Direction (°)'], current_df['Current Speed (m/s)'], normed=True, opening=0.8, edgecolor='white', cmap=cmap)
    
    # Place the legend outside the plot area
    ax.legend()

    # Return the WindroseAxes instance
    return ax

# Carregar os dados do CSV
df = pd.read_csv("dados_u_v_Ubu.csv")

# Calcular a velocidade da corrente (magnitude)
df['velocidade'] = np.sqrt(df['u']**2 + df['v']**2)

# Calcular a direção da corrente (em graus)
df['direcao'] = np.degrees(np.arctan2(df['v'], df['u']))

# Ajustar a direção para o intervalo [0, 360] graus (pois a atan2 retorna valores entre -180 e 180)
df['direcao'] = (df['direcao'] + 360) % 360

# Colocar data como index
df.set_index('Time', inplace=True)
df.index = pd.to_datetime(df.index)

# Gerar a rosa dos ventos
ax = plot_wind_rose(df, 2.5)
ax.set_title("Rosa de Correntes")
plt.show()

# Gerar a tabela de contagem
current_distribution = generate_current_distribution_table(df, 2.5, mode='bins')
print(current_distribution)


