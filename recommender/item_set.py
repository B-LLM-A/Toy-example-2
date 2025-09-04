import os
from dataclasses import dataclass
import pandas as pd


BASE_DIR = os.path.dirname(__file__)  # where item_set.py is
CSV_PATH = os.path.join(BASE_DIR, "data", "sample_cars.csv")


@dataclass
class CarSample:
    Car_name: str
    Year: int
    Price: float
    Gas_emission: float
    Fuel_type: str
    Engine_size: float
    Trim: str


def load_car_samples(csv_path: str) -> list[CarSample]:
    df = pd.read_csv(csv_path)
    # Enforce correct data types just in case the CSV has unexpected formats
    df = df.astype({
        "Car_name": str,
        "Year": int,
        "Price": float,
        "Gas_emission": float,
        "Fuel_type": str,
        "Engine_size": float,
        "Trim": str
    })
    return [CarSample(**row) for row in df.to_dict(orient="records")]


# Example usage
item_set = load_car_samples(CSV_PATH)

print(f"Loaded {len(item_set)} car samples.")
print(item_set[0])
