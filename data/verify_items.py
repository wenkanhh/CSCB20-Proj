import pandas as pd

df = pd.read_csv('requirement_items.csv')

print("CSV Structure:")
print(f"Columns: {list(df.columns)}")
print(f"Shape: {df.shape}")
print(f"\nData types:\n{df.dtypes}")

print("\n\nItem Type Distribution:")
print(df['item_type'].value_counts())

print("\n\nSample Items by Type:")
for item_type in df['item_type'].unique():
    print(f"\n--- {item_type} ---")
    sample = df[df['item_type'] == item_type].head(3)
    for col in df.columns:
        print(f"{col}: {sample[col].values}")
