# Before you run the models in SimBA, you may need to clean the features extracted files. Copy the path to your files in the features_extracted folder. Change the input and output paths below.

import pandas as pd

df = pd.read_csv(r'C:\Users\lmbwo\Desktop\male_mouse4_baseline-05052026115715-0000.csv')

print(f"Original features: {df.shape[1]}")
print(f"Original shape: {df.shape}")

# Fill NaN values with 0 (or use df.mean() for mean imputation)
df_clean = df.fillna(0)

print(f"Cleaned shape: {df_clean.shape}")
print(f"Any remaining NaN: {df_clean.isnull().sum().sum()}")

df_clean.to_csv(r'C:\Users\lmbwo\Desktop\male_mouse4_baseline-05052026115715-0000_CLEAN.csv', index=False)
print("Saved!")