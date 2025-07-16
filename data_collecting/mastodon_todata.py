import os
import pandas as pd

folder_path = 'Folder0'

all_data = []

for filename in os.listdir(folder_path):
    if filename.endswith(".csv"):  # to csv
        file_path = os.path.join(folder_path, filename)

        with open(file_path, 'r', encoding='utf-8') as f:
            next(f)  
            for line in f:
                all_data.append(line.strip())  

df = pd.DataFrame(all_data, columns=['Content'])

# csv
df.to_csv('merged_data.csv', index=False, encoding='utf-8') 

print("success merged_data.csv")

import pandas as pd
import re

# read csv
df = pd.read_csv('merged_data.csv')

# Filter Mastodon data using regular expressions
mastodon_pattern = r"[^/]+\/@[^/]+\/[0-9]" # The modified regular expression
mastodon_data = df[df['Content'].str.contains(mastodon_pattern, regex=True)]

# to csv
mastodon_data.to_csv('mastodon_data.csv', index=False, encoding='utf-8')

print("Mastodon data save to mastodon_data.csv")