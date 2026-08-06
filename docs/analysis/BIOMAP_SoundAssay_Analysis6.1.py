import pandas as pd
import numpy as np
import os


def calculate_angle(p1, p2, p3):
    """Calculate angle at p2 between vectors p2->p1 and p2->p3"""
    v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
    v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
    dot_product = np.dot(v1, v2)
    magnitude_v1 = np.linalg.norm(v1)
    magnitude_v2 = np.linalg.norm(v2)
    if magnitude_v1 == 0 or magnitude_v2 == 0:
        return np.nan
    cos_angle = np.clip(dot_product / (magnitude_v1 * magnitude_v2), -1.0, 1.0)
    angle_deg = np.degrees(np.arccos(cos_angle))
    return angle_deg


def calculate_distance(p1, p2):
    """Calculate Euclidean distance between two points"""
    return np.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def assign_experimental_condition(frame_number):
    """Assign experimental condition based on frame number"""
    if 34080 <= frame_number <= 38909:
        return "Baseline"
    elif 38910 <= frame_number <= 46651:
        return "90 dB SPL"
    elif 46652 <= frame_number <= 54414:
        return "Post 90"
    elif 54415 <= frame_number <= 62139:
        return "60 dB SPL"
    elif 62140 <= frame_number <= 69903:
        return "Post 60"
    elif 69904 <= frame_number <= 77656:
        return "50 dB SPL"
    elif 77657 <= frame_number <= 85395:
        return "Post 50"
    elif 85396 <= frame_number <= 93116:
        return "70 dB SPL"
    elif 93117 <= frame_number <= 100952:
        return "Post 70"
    elif 100953 <= frame_number <= 108631:
        return "80 dB SPL"
    elif 108632 <= frame_number <= 116382:
        return "Post 80"
    else:
        return "Outside Range"


def safe_save_csv(dataframe, filename, max_attempts=3):
    """Safely save CSV with error handling"""
    for attempt in range(max_attempts):
        try:
            # Ensure we're in the current working directory
            safe_filename = os.path.basename(filename)  # Remove any path components
            dataframe.to_csv(safe_filename, index=False)
            print(f"✓ Successfully saved: {safe_filename}")
            return safe_filename
        except PermissionError:
            if attempt < max_attempts - 1:
                # Try with a timestamp
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = os.path.splitext(safe_filename)[0]
                extension = os.path.splitext(safe_filename)[1]
                safe_filename = f"{base_name}_{timestamp}{extension}"
                print(f"⚠️  Permission denied, trying: {safe_filename}")
            else:
                print(f"❌ Failed to save {filename} - please close any open Excel files and try again")
                return None
        except Exception as e:
            print(f"❌ Error saving {filename}: {e}")
            return None
    return None


# Load CSV with multi-level headers
print("Loading complete CSV...")
df = pd.read_csv('/Volumes/Extreme SSD 1/14days_NE_mice/Female_Mouse4_NE_14days-05212026160601-0000DLC_DlcrnetStride32Ms5_BIOMAPMar17shuffle2_snapshot_best-175.csv',
                 header=[0, 1, 2])

# Get the scorer name BEFORE inserting frame column
SCORER = df.columns[1][0]  # Gets the actual DLC scorer name
print(f"Detected scorer name: {SCORER}\n")

# Add frame number column (assuming it starts from 0)
df.insert(0, 'frame', range(len(df)))

# Add time column based on frame numbers (30 fps)
df['time_seconds'] = df['frame'] / 30.0

# Add experimental condition column
print("Assigning experimental conditions...")
df['Experimental_Condition'] = df['frame'].apply(assign_experimental_condition)

# Calculate angles and distances with likelihood filtering
angles_data = {
    'Snout Position': [],
    'Ear Tip Tilt': [],
    'Ear Position': [],
    'Mouth Position': []
}

distances_data = {
    'distance_eyeup_eyedown': [],
    'distance_innereye_outereye': [],
    'Eye Ratio': [],
    'distance_earmed_earlat': [],
    'distance_earcanal_eartip': [],
    'Ear Ratio': []
}

# Add filtered data for measurements
nosetip_inverted_data = []
face_inclination_data = []
movement_nosetip_filtered_data = []

print("Calculating measurements with likelihood filtering...")
print(f"Total rows to process: {len(df)}")

filter_counts = {
    'snout': 0, 'mouth': 0, 'eartip': 0, 'earpos': 0, 'ear_ratio': 0,
    'eye_ratio': 0, 'nosetip_inverted': 0, 'face_inclination': 0, 'nosetip_crossing': 0,
    'movement_nosetip': 0, 'snout_angle_range': 0, 'mouth_angle_range': 0
}

total_count = 0
error_count = 0

for index, row in df.iterrows():
    try:
        total_count += 1
        # Access coordinates (multi-level column names with correct scorer)
        innereye = (row[(SCORER, 'innereye', 'x')], row[(SCORER, 'innereye', 'y')])
        nosetip = (row[(SCORER, 'nosetip', 'x')], row[(SCORER, 'nosetip', 'y')])
        nosebot = (row[(SCORER, 'nosebot', 'x')], row[(SCORER, 'nosebot', 'y')])
        earcanal = (row[(SCORER, 'earcanal', 'x')], row[(SCORER, 'earcanal', 'y')])
        earcenter = (row[(SCORER, 'earcenter', 'x')], row[(SCORER, 'earcenter', 'y')])
        eartip = (row[(SCORER, 'eartip', 'x')], row[(SCORER, 'eartip', 'y')])
        mouth = (row[(SCORER, 'mouth', 'x')], row[(SCORER, 'mouth', 'y')])
        eyeup = (row[(SCORER, 'eyeup', 'x')], row[(SCORER, 'eyeup', 'y')])
        eyedown = (row[(SCORER, 'eyedown', 'x')], row[(SCORER, 'eyedown', 'y')])
        outereye = (row[(SCORER, 'outereye', 'x')], row[(SCORER, 'outereye', 'y')])
        earmed = (row[(SCORER, 'earmed', 'x')], row[(SCORER, 'earmed', 'y')])
        earlat = (row[(SCORER, 'earlat', 'x')], row[(SCORER, 'earlat', 'y')])
        neck = (row[(SCORER, 'neck', 'x')], row[(SCORER, 'neck', 'y')])

        # Get likelihoods (probabilities)
        nosebot_likelihood = row[(SCORER, 'nosebot', 'likelihood')]
        nosetip_likelihood = row[(SCORER, 'nosetip', 'likelihood')]
        mouth_likelihood = row[(SCORER, 'mouth', 'likelihood')]
        eartip_likelihood = row[(SCORER, 'eartip', 'likelihood')]
        earlat_likelihood = row[(SCORER, 'earlat', 'likelihood')]
        outereye_likelihood = row[(SCORER, 'outereye', 'likelihood')]
        neck_likelihood = row[(SCORER, 'neck', 'likelihood')]

        # Calculate nosetip_y_inverted with likelihood filtering
        if nosetip_likelihood > 0.75:
            nosetip_inverted_data.append(row[(SCORER, 'nosetip', 'y')] * -1)
        else:
            nosetip_inverted_data.append(np.nan)
            filter_counts['nosetip_inverted'] += 1

        # Calculate Face Inclination (neck_y - nosetip_y) with neck likelihood filtering
        if neck_likelihood > 0.75:
            face_inclination = neck[1] - nosetip[1]  # neck_y - nosetip_y
            face_inclination_data.append(face_inclination)
        else:
            face_inclination_data.append(np.nan)
            filter_counts['face_inclination'] += 1

        # Filter Movement_nosetip based on nosetip_p > 0.75
        if 'Movement_nosetip' in df.columns:
            if nosetip_likelihood > 0.75:
                movement_nosetip_filtered_data.append(row['Movement_nosetip'])
            else:
                movement_nosetip_filtered_data.append(np.nan)
                filter_counts['movement_nosetip'] += 1
        else:
            movement_nosetip_filtered_data.append(np.nan)

        # Calculate SNOUT POSITION with likelihood AND angle range filtering (50-110 degrees)
        if nosebot_likelihood > 0.75:
            snout_angle = calculate_angle(innereye, nosetip, nosebot)
            # Only keep angles between 50 and 110 degrees
            if not np.isnan(snout_angle) and 50 <= snout_angle <= 110:
                angles_data['Snout Position'].append(snout_angle)
            else:
                angles_data['Snout Position'].append(np.nan)
                if not np.isnan(snout_angle):
                    filter_counts['snout_angle_range'] += 1
        else:
            angles_data['Snout Position'].append(np.nan)
            filter_counts['snout'] += 1

        # Calculate MOUTH POSITION with likelihood AND angle range filtering (10-50 degrees)
        if mouth_likelihood > 0.75:
            mouth_angle = calculate_angle(nosebot, innereye, mouth)
            # Only keep angles between 10 and 50 degrees
            if not np.isnan(mouth_angle) and 10 <= mouth_angle <= 50:
                angles_data['Mouth Position'].append(mouth_angle)
            else:
                angles_data['Mouth Position'].append(np.nan)
                if not np.isnan(mouth_angle):
                    filter_counts['mouth_angle_range'] += 1
        else:
            angles_data['Mouth Position'].append(np.nan)
            filter_counts['mouth'] += 1

        angles_data['Ear Tip Tilt'].append(
            calculate_angle(earcanal, earcenter, eartip) if eartip_likelihood > 0.75 else np.nan)
        if eartip_likelihood <= 0.75:
            filter_counts['eartip'] += 1

        angles_data['Ear Position'].append(
            calculate_angle(innereye, earcanal, eartip) if eartip_likelihood > 0.75 else np.nan)
        if eartip_likelihood <= 0.75:
            filter_counts['earpos'] += 1

        # Calculate distances
        dist_eyeup_eyedown = calculate_distance(eyeup, eyedown)
        dist_innereye_outereye = calculate_distance(innereye, outereye)
        dist_earmed_earlat = calculate_distance(earmed, earlat)
        dist_earcanal_eartip = calculate_distance(earcanal, eartip)

        distances_data['distance_eyeup_eyedown'].append(dist_eyeup_eyedown)
        distances_data['distance_innereye_outereye'].append(dist_innereye_outereye)
        distances_data['distance_earmed_earlat'].append(dist_earmed_earlat)
        distances_data['distance_earcanal_eartip'].append(dist_earcanal_eartip)

        # Calculate ratios with likelihood filtering
        if outereye_likelihood > 0.75 and dist_innereye_outereye != 0:
            eye_ratio = dist_eyeup_eyedown / dist_innereye_outereye
        else:
            eye_ratio = np.nan
            if outereye_likelihood <= 0.75:
                filter_counts['eye_ratio'] += 1
        distances_data['Eye Ratio'].append(eye_ratio)

        if earlat_likelihood > 0.75 and dist_earcanal_eartip != 0:
            ear_ratio = dist_earmed_earlat / dist_earcanal_eartip
        else:
            ear_ratio = np.nan
            if earlat_likelihood <= 0.75:
                filter_counts['ear_ratio'] += 1
        distances_data['Ear Ratio'].append(ear_ratio)

        if (index + 1) % 1000 == 0:
            print(f"Processed {index + 1}/{len(df)} rows...")

    except Exception as e:
        error_count += 1
        print(f"⚠️  Error at row {index}: {e}")
        # Append NaN values for all data structures to maintain alignment
        for key in angles_data:
            angles_data[key].append(np.nan)
        for key in distances_data:
            distances_data[key].append(np.nan)
        nosetip_inverted_data.append(np.nan)
        face_inclination_data.append(np.nan)
        movement_nosetip_filtered_data.append(np.nan)
        continue

print(f"\n✓ Finished processing all {total_count} rows")
if error_count > 0:
    print(f"⚠️  Encountered {error_count} errors during processing")

# Verify data lengths match
print(f"\nVerifying data lengths:")
print(f"  DataFrame length: {len(df)}")
print(f"  Snout Position length: {len(angles_data['Snout Position'])}")
print(f"  nosetip_inverted length: {len(nosetip_inverted_data)}")

# Add all calculated columns to dataframe
for col_name, values in angles_data.items():
    df[col_name] = values

for col_name, values in distances_data.items():
    df[col_name] = values

# Add filtered columns
df['nosetip_y_inverted'] = nosetip_inverted_data
df['Face Inclination'] = face_inclination_data
df['Movement_nosetip_filtered'] = movement_nosetip_filtered_data

# Calculate nosetip x=900 line crossings with likelihood filtering
print("\nCalculating nosetip x=900 line crossings...")
nosetip_crossing_data = []
crossing_count = 0
previous_valid_x = None
previous_above_900 = None
crossing_error_count = 0

for index, row in df.iterrows():
    try:
        nosetip_likelihood = row[(SCORER, 'nosetip', 'likelihood')]

        # Only process if likelihood > 0.75
        if nosetip_likelihood > 0.75:
            current_x = row[(SCORER, 'nosetip', 'x')]
            current_above_900 = current_x > 900

            # Check for crossing (only if we have a previous valid point)
            if previous_valid_x is not None and previous_above_900 is not None:
                # Crossing occurs when previous and current are on different sides of 900
                if previous_above_900 != current_above_900:
                    crossing_count += 1

            # Update previous values
            previous_valid_x = current_x
            previous_above_900 = current_above_900
            nosetip_crossing_data.append(crossing_count)
        else:
            # If likelihood too low, keep the same crossing count but don't update previous values
            nosetip_crossing_data.append(crossing_count)
            filter_counts['nosetip_crossing'] += 1

        if (index + 1) % 5000 == 0:
            print(f"  Calculated crossings for {index + 1}/{len(df)} rows...")

    except Exception as e:
        crossing_error_count += 1
        nosetip_crossing_data.append(crossing_count)
        if crossing_error_count <= 5:
            print(f"⚠️  Error calculating crossing at row {index}: {e}")

print(f"✓ Finished calculating crossings for all {len(df)} rows")
print(f"  Crossing data length: {len(nosetip_crossing_data)}")

# Add the crossing count column
df['Nosetip X Crossings at 900'] = nosetip_crossing_data

# COMPREHENSIVE STATISTICAL ANALYSIS
print("\n" + "=" * 80)
print("COMPREHENSIVE STATISTICAL ANALYSIS")
print("=" * 80)

condition_order = [
    "Baseline", "50 dB SPL", "Post 50","60 dB SPL", "Post 60", "70 dB SPL", "Post 70", "80 dB SPL", "Post 80", "90 dB SPL",
    "Post 90"
]

# Define all measures to analyze
measures_to_analyze = [
    {'column': 'Movement_nosetip_filtered', 'name': 'Movement_nosetip'},
    {'column': 'Eye Ratio', 'name': 'Eye_Ratio'},
    {'column': 'Ear Ratio', 'name': 'Ear_Ratio'},
    {'column': 'Ear Position', 'name': 'Ear_Position'},
    {'column': 'Mouth Position', 'name': 'Mouth_Position'},
    {'column': 'Snout Position', 'name': 'Snout_Position'},
    {'column': 'Ear Tip Tilt', 'name': 'Ear_Tip_Tilt'},
    {'column': 'nosetip_y_inverted', 'name': 'Nosetip_Y_Inverted'},
    {'column': 'Face Inclination', 'name': 'Face_Inclination'},
    {'column': 'Nosetip X Crossings at 900', 'name': 'Nosetip_X_Crossings_900'}
]

# Comprehensive statistical analysis
all_stats = []

print("Analyzing statistical measures by experimental condition...")

for measure in measures_to_analyze:
    column_name = measure['column']
    measure_name = measure['name']

    if column_name in df.columns:
        print(f"\nAnalyzing {measure_name}...")

        for condition in condition_order:
            if condition in df['Experimental_Condition'].values:
                condition_data = df[df['Experimental_Condition'] == condition]

                if len(condition_data) > 0:
                    # Get the data for this measure and condition
                    measure_data = condition_data[column_name].dropna()

                    if len(measure_data) > 0:
                        stats = {
                            'Experimental_Condition': condition,
                            'Measure': measure_name,
                            'Mean': measure_data.mean(),
                            'Median': measure_data.median(),
                            'Min': measure_data.min(),
                            'Max': measure_data.max(),
                            'Std_Dev': measure_data.std(),
                            'Valid_Frames': len(measure_data),
                            'Total_Frames': len(condition_data),
                            'Percent_Valid': (len(measure_data) / len(condition_data) * 100)
                        }
                    else:
                        stats = {
                            'Experimental_Condition': condition,
                            'Measure': measure_name,
                            'Mean': np.nan,
                            'Median': np.nan,
                            'Min': np.nan,
                            'Max': np.nan,
                            'Std_Dev': np.nan,
                            'Valid_Frames': 0,
                            'Total_Frames': len(condition_data),
                            'Percent_Valid': 0
                        }

                    all_stats.append(stats)

                    # Print formatted results
                    if not np.isnan(stats['Mean']):
                        print(
                            f"  {condition:15s}: Mean={stats['Mean']:8.3f}, Median={stats['Median']:8.3f}, Min={stats['Min']:8.3f}, Max={stats['Max']:8.3f}, SD={stats['Std_Dev']:8.3f} ({stats['Valid_Frames']:4d}/{stats['Total_Frames']:4d} frames)")
                    else:
                        print(f"  {condition:15s}: No valid data (0/{stats['Total_Frames']:4d} frames)")
    else:
        print(f"⚠️  WARNING: '{column_name}' column not found for {measure_name}")

# NEW: PERCENT IN TOP ANALYSIS FOR NOSETIP_Y_INVERTED
print("\n" + "=" * 60)
print("PERCENT IN TOP ANALYSIS (Nosetip_Y_Inverted > -450)")
print("=" * 60)
print("Analyzing percentage of frames above -450 by experimental condition...")
print("(Filtered by nosetip_p > 0.75)")

for condition in condition_order:
    if condition in df['Experimental_Condition'].values:
        condition_data = df[df['Experimental_Condition'] == condition]

        if len(condition_data) > 0:
            # Get nosetip_y_inverted data filtered by nosetip_p > 0.75
            filtered_nosetip_data = condition_data['nosetip_y_inverted'].dropna()

            if len(filtered_nosetip_data) > 0:
                # Calculate percentage above -450
                frames_above_minus450 = (filtered_nosetip_data > -450).sum()
                percent_in_top = (frames_above_minus450 / len(filtered_nosetip_data)) * 100

                # Add to comprehensive stats
                percent_in_top_stats = {
                    'Experimental_Condition': condition,
                    'Measure': 'Percent_in_Top',
                    'Mean': percent_in_top,
                    'Median': percent_in_top,
                    'Min': percent_in_top,
                    'Max': percent_in_top,
                    'Std_Dev': 0,
                    'Valid_Frames': len(filtered_nosetip_data),
                    'Total_Frames': len(condition_data),
                    'Percent_Valid': (len(filtered_nosetip_data) / len(condition_data) * 100)
                }

                all_stats.append(percent_in_top_stats)

                print(
                    f"  {condition:15s}: {percent_in_top:6.2f}% above -450 ({frames_above_minus450:4d}/{len(filtered_nosetip_data):4d} valid frames)")
            else:
                # No valid data
                percent_in_top_stats = {
                    'Experimental_Condition': condition,
                    'Measure': 'Percent_in_Top',
                    'Mean': np.nan,
                    'Median': np.nan,
                    'Min': np.nan,
                    'Max': np.nan,
                    'Std_Dev': np.nan,
                    'Valid_Frames': 0,
                    'Total_Frames': len(condition_data),
                    'Percent_Valid': 0
                }

                all_stats.append(percent_in_top_stats)
                print(f"  {condition:15s}: No valid data (0/{len(condition_data):4d} frames)")

# NEW: FACE INCLINATION PERCENTAGE ANALYSIS (Nosetip Y > Neck Y)
print("\n" + "=" * 60)
print("FACE INCLINATION PERCENTAGE ANALYSIS (Nosetip Y > Neck Y)")
print("=" * 60)
print("Analyzing percentage of frames where nosetip_y > neck_y by experimental condition...")
print("(Filtered by neck likelihood > 0.75)")

for condition in condition_order:
    if condition in df['Experimental_Condition'].values:
        condition_data = df[df['Experimental_Condition'] == condition]

        if len(condition_data) > 0:
            # Get face inclination data (already filtered by neck likelihood > 0.75)
            filtered_face_data = condition_data['Face Inclination'].dropna()

            if len(filtered_face_data) > 0:
                # Face Inclination = neck_y - nosetip_y
                # If Face Inclination < 0, then nosetip_y > neck_y
                frames_nosetip_above_neck = (filtered_face_data < 0).sum()
                percent_nosetip_above = (frames_nosetip_above_neck / len(filtered_face_data)) * 100

                # Add to comprehensive stats
                face_inclination_percent_stats = {
                    'Experimental_Condition': condition,
                    'Measure': 'Percent_Nosetip_Above_Neck',
                    'Mean': percent_nosetip_above,
                    'Median': percent_nosetip_above,
                    'Min': percent_nosetip_above,
                    'Max': percent_nosetip_above,
                    'Std_Dev': 0,
                    'Valid_Frames': len(filtered_face_data),
                    'Total_Frames': len(condition_data),
                    'Percent_Valid': (len(filtered_face_data) / len(condition_data) * 100)
                }

                all_stats.append(face_inclination_percent_stats)

                print(
                    f"  {condition:15s}: {percent_nosetip_above:6.2f}% nosetip above neck ({frames_nosetip_above_neck:4d}/{len(filtered_face_data):4d} valid frames)")
            else:
                # No valid data
                face_inclination_percent_stats = {
                    'Experimental_Condition': condition,
                    'Measure': 'Percent_Nosetip_Above_Neck',
                    'Mean': np.nan,
                    'Median': np.nan,
                    'Min': np.nan,
                    'Max': np.nan,
                    'Std_Dev': np.nan,
                    'Valid_Frames': 0,
                    'Total_Frames': len(condition_data),
                    'Percent_Valid': 0
                }

                all_stats.append(face_inclination_percent_stats)
                print(f"  {condition:15s}: No valid data (0/{len(condition_data):4d} frames)")

# Create comprehensive statistical analysis dataframe
if all_stats:
    comprehensive_stats_df = pd.DataFrame(all_stats)

    # Save comprehensive statistical analysis
    comprehensive_filename = safe_save_csv(comprehensive_stats_df, 'F_Mouse4_NE_14D_Sound.csv')

    print(f"\n✓ Comprehensive statistical analysis saved to: {comprehensive_filename}")

    # Print summary by measure
    print(f"\nSUMMARY BY MEASURE:")
    print("-" * 80)
    for measure in measures_to_analyze:
        measure_name = measure['name']
        measure_stats = comprehensive_stats_df[comprehensive_stats_df['Measure'] == measure_name]
        if len(measure_stats) > 0:
            valid_stats = measure_stats.dropna(subset=['Mean'])
            if len(valid_stats) > 0:
                overall_mean = valid_stats['Mean'].mean()
                overall_std = valid_stats['Mean'].std()
                print(
                    f"{measure_name:30s}: Overall Mean={overall_mean:8.3f}, SD across conditions={overall_std:8.3f} ({len(valid_stats)}/{len(measure_stats)} conditions with data)")
            else:
                print(f"{measure_name:30s}: No valid data across conditions")

    # Print Percent in Top summary
    percent_in_top_stats = comprehensive_stats_df[comprehensive_stats_df['Measure'] == 'Percent_in_Top']
    if len(percent_in_top_stats) > 0:
        valid_percent_stats = percent_in_top_stats.dropna(subset=['Mean'])
        if len(valid_percent_stats) > 0:
            overall_percent_mean = valid_percent_stats['Mean'].mean()
            overall_percent_std = valid_percent_stats['Mean'].std()
            print(
                f"{'Percent_in_Top':30s}: Overall Mean={overall_percent_mean:8.3f}%, SD across conditions={overall_percent_std:8.3f}% ({len(valid_percent_stats)}/{len(percent_in_top_stats)} conditions with data)")
        else:
            print(f"{'Percent_in_Top':30s}: No valid data across conditions")

    # Print Face Inclination Percentage summary
    face_incl_percent_stats = comprehensive_stats_df[comprehensive_stats_df['Measure'] == 'Percent_Nosetip_Above_Neck']
    if len(face_incl_percent_stats) > 0:
        valid_face_incl_stats = face_incl_percent_stats.dropna(subset=['Mean'])
        if len(valid_face_incl_stats) > 0:
            overall_face_incl_mean = valid_face_incl_stats['Mean'].mean()
            overall_face_incl_std = valid_face_incl_stats['Mean'].std()
            print(
                f"{'Percent_Nosetip_Above_Neck':30s}: Overall Mean={overall_face_incl_mean:8.3f}%, SD across conditions={overall_face_incl_std:8.3f}% ({len(valid_face_incl_stats)}/{len(face_incl_percent_stats)} conditions with data)")
        else:
            print(f"{'Percent_Nosetip_Above_Neck':30s}: No valid data across conditions")

# Save complete dataset with all original data plus new analysis
output_file = safe_save_csv(df, 'F_Mouse4_NE_14DSoundComplete_with_all_analysis.csv')

# Report filtering results
print(f"\nFILTERING RESULTS:")
print(f"Total frames: {total_count}")
print(f"Measurements filtered out (likelihood ≤ 0.75):")
print(f" - Snout Position (likelihood): {filter_counts['snout']} ({filter_counts['snout'] / total_count * 100:.1f}%)")
print(f" - Snout Position (angle range): {filter_counts['snout_angle_range']} ({filter_counts['snout_angle_range'] / total_count * 100:.1f}%)")
print(f" - Mouth Position (likelihood): {filter_counts['mouth']} ({filter_counts['mouth'] / total_count * 100:.1f}%)")
print(f" - Mouth Position (angle range): {filter_counts['mouth_angle_range']} ({filter_counts['mouth_angle_range'] / total_count * 100:.1f}%)")
print(f" - Ear Tip Tilt: {filter_counts['eartip']} ({filter_counts['eartip'] / total_count * 100:.1f}%)")
print(f" - Ear Position: {filter_counts['earpos']} ({filter_counts['earpos'] / total_count * 100:.1f}%)")
print(
    f" - Movement Nosetip: {filter_counts['movement_nosetip']} ({filter_counts['movement_nosetip'] / total_count * 100:.1f}%)")
print(
    f" - Nosetip X Crossings: {filter_counts['nosetip_crossing']} ({filter_counts['nosetip_crossing'] / total_count * 100:.1f}%)")

print("\n" + "=" * 80)
print("COMPLETE ANALYSIS FINISHED")
print("=" * 80)

# List all generated files
generated_files = []
if output_file:
    print(f"✓ Complete dataset with all original data: {output_file}")
    generated_files.append(output_file)

if 'comprehensive_filename' in locals() and comprehensive_filename:
    print(f"✓ Comprehensive statistical analysis (including Percent in Top and Face Inclination %): {comprehensive_filename}")
    generated_files.append(comprehensive_filename)

print(f"✓ Snout Position filtered to 50-110 degree range")
print(f"✓ Mouth Position filtered to 10-50 degree range")
print(f"✓ Face Inclination percentage analysis added (nosetip_y > neck_y)")
print(f"✓ Nosetip x=900 crossings detected: {crossing_count}")
print("✓ All original columns preserved")
print(f"✓ Percent in Top analysis included for Nosetip_Y_Inverted > -450")

if generated_files:
    print(f"\nSUCCESSFULLY GENERATED FILES:")
    for file in generated_files:
        print(f"  - {file}")
else:
    print("\n⚠️  Some files may not have been saved due to permission issues.")
    print("Please close any open Excel files and try running the script again.")