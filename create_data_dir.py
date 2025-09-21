# Create data directory
import os
data_dir = "data/registry"
os.makedirs(data_dir, exist_ok=True)
print(f"Created data directory at: {os.path.abspath(data_dir)}")
