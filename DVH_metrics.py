import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#Load the DVH file of interest
file_path = '/content/DVH3_1.csv'
dvh_data = pd.read_csv(file_path)

dvh_metrics_path = '/content/DVH_metrics3_1.csv'
dvh_metrics = pd.read_csv(dvh_metrics_path)

# Extract the segments and their volumes
segments = []
volumes = []

for col in dvh_data.columns:
    if 'Value' in col:
        segment_name = col.split(' ')[0]
        volume_value = col.split('of ')[-1].split(' cc')[0]
        if segment_name not in segments:
          segments.append(segment_name)
          volumes.append(float(volume_value))

# Create the dataframe for segments and volumes
segments_volumes_df = pd.DataFrame({
    'Segment': segments,
    'Volume (cc)': volumes
})

segments_volumes_df

# Plot the DVH for each unique segment
plt.figure(figsize=(10, 6))
for segment, volume in zip(segments, volumes):
    dose_col = f'{segment} Dose (GY)'
    value_col = f'{segment} Value (% of {volume:.3f} cc)'

    # Ensure the column exists before plotting
    if dose_col in dvh_data.columns and value_col in dvh_data.columns:
        plt.plot(dvh_data[dose_col], dvh_data[value_col], label=segment)

plt.title('DVH Plot for All Unique Segments')
plt.xlabel('Dose (Gy)')
plt.ylabel('Volume (%)')
plt.legend(title='Segments')
plt.grid(True)
plt.tight_layout()

plt.show()

# Function to extract the required metrics from the cumulative DVH and check constraints
def extract_dvh_metrics(dvh_data, segment, volume):
    # Extract dose and volume columns based on the segment
    dose_col = dvh_data[f'{segment} Dose (GY)'].dropna()
    value_col = dvh_data[f'{segment} Value (% of {volume:.3f} cc)'].dropna()

    # Ensure the volume is calculated directly as percentage values are already cumulative
    cumulative_volume = value_col

  #  # Convert the percentage volume to absolute volume (in cc)
  #   absolute_volume_col = (value_col / 100) * volume

  #  # Filter out zero dose values for calculations
  #   nonzero_mask = absolute_volume_col > 0
  #   dose_col = dose_col[nonzero_mask ].reset_index(drop=True)
  #   value_col = absolute_volume_col[nonzero_mask].reset_index(drop=True)

    # Calculate DMax and DMean
    dmax = dose_col.max()
    dmean = dvh_metrics[dvh_metrics['Structure'] == segment]['Mean dose (GY)'].values[0]

    # D(98%) and D(2%) are the dose levels corresponding to 98% and 2% of the cumulative volume
    d_98 = dose_col[cumulative_volume >= 98].min() if len(dose_col[cumulative_volume >= 98]) > 0 else None
    d_2 = dose_col[cumulative_volume >= 2].max() if len(dose_col[cumulative_volume >= 2]) > 0 else None

    # V(95%) and V(90%) - percentage of volume that receives at least 95% and 90% of the maximum dose
    v_95 = (value_col[dose_col >= 0.95 * dmax]).max() if len(value_col[dose_col >= 0.95 * dmax]) > 0 else 0
    v_90 = (value_col[dose_col >= 0.90 * dmax]).max() if len(value_col[dose_col >= 0.90 * dmax]) > 0 else 0

    # Initial volume at 0 Gy
    initial_volume = volume

    # Initialize constraint checks
    constraints_met = {}
    metrics = {}

    # Apply specific constraints based on the segment name
    if 'DUODENUM' in segment:
        vol_at_22_2 = value_col[dose_col >= 22.2].max()
        vol_at_16_5 = value_col[dose_col >= 16.5].max()
        constraints_met['<0.5cc at 22.2 Gy'] = vol_at_22_2 < 0.5 if pd.notna(vol_at_22_2) else True
        constraints_met['<5cc at 16.5 Gy'] = vol_at_16_5 < 5 if pd.notna(vol_at_16_5) else True
        metrics['Volume at 22.2 Gy (cc)'] = vol_at_22_2
        metrics['Volume at 16.5 Gy (cc)'] = vol_at_16_5

    elif 'STOMACH' in segment:
        vol_at_22_2 = value_col[dose_col >= 22.2].max()
        vol_at_16_5 = value_col[dose_col >= 16.5].max()
        constraints_met['<0.5cc at 22.2 Gy'] = vol_at_22_2 < 0.5 if pd.notna(vol_at_22_2) else True
        constraints_met['<10cc at 16.5 Gy'] = vol_at_16_5 < 10 if pd.notna(vol_at_16_5) else True
        metrics['Volume at 22.2 Gy (cc)'] = vol_at_22_2
        metrics['Volume at 16.5 Gy (cc)'] = vol_at_16_5

    elif 'LARGEBOWEL' in segment:
        vol_at_28_2 = value_col[dose_col >= 28.2].max()
        vol_at_20_4 = value_col[dose_col >= 20.4].max()
        constraints_met['<0.5cc at 28.2 Gy'] = vol_at_28_2 < 0.5 if pd.notna(vol_at_28_2) else True
        constraints_met['<20cc at 20.4 Gy'] = vol_at_20_4 < 20 if pd.notna(vol_at_20_4) else True
        metrics['Volume at 28.2 Gy (cc)'] = vol_at_28_2
        metrics['Volume at 20.4 Gy (cc)'] = vol_at_20_4

    elif 'SMALLBOWEL' in segment:
        vol_at_25_2 = value_col[dose_col >= 25.2].max()
        vol_at_17_7 = value_col[dose_col >= 17.7].max()
        constraints_met['<0.5cc at 25.2 Gy'] = vol_at_25_2 < 0.5 if pd.notna(vol_at_25_2) else True
        constraints_met['<5cc at 17.7 Gy'] = vol_at_17_7 < 5 if pd.notna(vol_at_17_7) else True
        metrics['Volume at 25.2 Gy (cc)'] = vol_at_25_2
        metrics['Volume at 17.7 Gy (cc)'] = vol_at_17_7

    elif 'GTV' in segment or 'CTV' in segment:
        # Calculate the difference from 99% cumulative volume
        cumulative_volume_diff = (cumulative_volume - 99).abs()

        # Find the dose closest to 99% cumulative volume
        dose_at_99_volume = dose_col[cumulative_volume_diff.idxmin()]

        constraints_met['99% > 22.8 Gy'] = dose_at_99_volume > 22.8
        metrics['Dose at 99% volume (Gy)'] = dose_at_99_volume


# Find the row where the cumulative volume percentage is closest to 99%


    # Combine metrics and constraint results
    return {
        'Initial Volume [cc]': initial_volume,
        'DMax [Gy]': dmax,
        'DMean [Gy]': dmean,
        'D(98 %) [Gy]': d_98,
        'D(2 %) [Gy]': d_2,
        'V(95 %) [%]': v_95,
        'V(90 %) [%]': v_90,
        'Constraints Met': constraints_met,
        **metrics
    }

# Apply the function to all segments and calculate the metrics
metrics = {}
for segment, volume in zip(segments, volumes):
    metrics[segment] = extract_dvh_metrics(dvh_data, segment, volume)

# Convert the metrics to a DataFrame for easy viewing
metrics_df = pd.DataFrame(metrics).T

# View the metrics and constraint checks
metrics_df

# Sample constraints to include in the plot (all in cc)
constraints = {
    'DUODENUM': [(22.2, 0.5), (16.5, 5)],
    'STOMACH': [(22.2, 0.5), (16.5, 10)],
    'LARGEBOWEL': [(28.2, 0.5), (20.4, 20)],
    'SMALLBOWEL': [(25.2, 0.5), (17.7, 5)],
    'GTV': [(None, None)],  # Add constraints for GTV if needed
    'CTV': [(None, None)]   # Add constraints for CTV if needed
}

# Function to plot constraints for a segment with the same color
def plot_constraints(ax, segment_name, segment_constraints, color):
    for key in constraints:
        if key in segment_name:  # Match the segment name with the constraints
            segment_constraints = constraints[key]
            for dose, volume in segment_constraints:
                if dose is not None and volume is not None:
                    # Plot the constraint points and lines in cc
                    ax.plot(dose, volume, marker='o', color=color, markersize=8, label=f'{key} constraint')
                    ax.axvline(x=dose, color=color, linestyle='--', alpha=0.7)
                    ax.axhline(y=volume, color=color, linestyle='--', alpha=0.7)

# Plot the DVH with constraints for each segment (in cc)
fig, ax2 = plt.subplots(figsize=(10, 6))

for segment, volume in zip(segments, volumes):
    dose_col = f'{segment} Dose (GY)'
    value_col = f'{segment} Value (% of {volume:.3f} cc)'

    if dose_col in dvh_data.columns and value_col in dvh_data.columns:
        # Convert volume percentage to cc
        cumulative_volume_cc = (dvh_data[value_col] / 100) * volume

        # Plot the segment's DVH curve (in cc)
        line, = ax2.plot(dvh_data[dose_col], cumulative_volume_cc, label=segment)
        segment_color = line.get_color()  # Capture the color used for the segment

        # Plot constraints for each segment
        plot_constraints(ax2, segment, constraints.get(segment, []), segment_color)

ax2.set_xlabel('Dose (GY)')
ax2.set_ylabel('Volume (cc)')
ax2.set_title('DVH Plot with Constraints in cc')
ax2.legend()
ax2.grid(True)

plt.show()
