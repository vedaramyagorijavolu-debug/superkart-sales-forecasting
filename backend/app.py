# Import necessary libraries
import joblib  # For loading the serialized model
import numpy as np
import pandas as pd  # For data manipulation
from flask import Flask, jsonify, request  # For creating the Flask API

# Initialize Flask app with a name
superkart_api = Flask("SuperKart")

# Load the trained pipeline (ColumnTransformer + Tuned Random Forest)
model = joblib.load("superkart_sales_model.joblib")

FEATURE_COLUMNS = [
    "Product_Weight",
    "Product_Sugar_Content",
    "Product_Allocated_Area",
    "Product_MRP",
    "Store_Size",
    "Store_Location_City_Type",
    "Store_Type",
    "Product_Id_char",
    "Store_Age_Years",
    "Product_Type_Category",
]

PERISHABLE_TYPES = {
    "Fruits and Vegetables",
    "Dairy",
    "Meat",
    "Seafood",
    "Breads",
    "Breakfast",
    "Frozen Foods",
}


def engineer_features(data: pd.DataFrame, ref_year: int = 2026) -> pd.DataFrame:
    """Apply the same label cleanup and feature engineering used during training."""
    df_clean = data.copy()

    # Standardize inconsistent sugar category label
    if "Product_Sugar_Content" in df_clean.columns:
        df_clean["Product_Sugar_Content"] = df_clean["Product_Sugar_Content"].replace(
            {"reg": "Regular"}
        )

    # Extract 2-character product category prefix (FD, NC, DR) if raw Product_Id is passed
    if "Product_Id_char" not in df_clean.columns and "Product_Id" in df_clean.columns:
        df_clean["Product_Id_char"] = df_clean["Product_Id"].astype(str).str[:2]

    # Convert store establishment year into store age if Store_Age_Years isn't already provided
    if (
        "Store_Age_Years" not in df_clean.columns
        and "Store_Establishment_Year" in df_clean.columns
    ):
        df_clean["Store_Age_Years"] = ref_year - pd.to_numeric(
            df_clean["Store_Establishment_Year"], errors="coerce"
        )

    # Map detailed Product_Type into Perishables vs. Non Perishables if needed
    if (
        "Product_Type_Category" not in df_clean.columns
        and "Product_Type" in df_clean.columns
    ):
        df_clean["Product_Type_Category"] = np.where(
            df_clean["Product_Type"].isin(PERISHABLE_TYPES),
            "Perishables",
            "Non Perishables",
        )

    # Ensure exact feature alignment expected by the pipeline
    missing_cols = [c for c in FEATURE_COLUMNS if c not in df_clean.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns: {missing_cols}")

    return df_clean[FEATURE_COLUMNS]


# Define a route for the home page
@superkart_api.get("/")
def home():
    return "Welcome to the SuperKart System"


# Define an endpoint to predict sales for a single product
@superkart_api.post("/v1/predict")
def predict_sales():
    # Get JSON data from the request
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid or empty JSON payload"}), 400

    # Extract relevant features from the input data
    sample = {col: data.get(col) for col in FEATURE_COLUMNS}

    # Convert to DataFrame and apply consistent feature preprocessing
    input_data = engineer_features(pd.DataFrame([sample]))

    # Make a prediction using the trained pipeline
    prediction = float(model.predict(input_data)[0])

    # Return the prediction as a JSON response
    return jsonify({"Sales": round(prediction, 2)})


# Define an endpoint to predict sales for a batch of products
@superkart_api.post("/v1/predictbatch")
def predict_sales_batch():
    # Get the uploaded CSV file from the request
    if "file" not in request.files:
        return jsonify({"error": "Missing CSV file under form field 'file'"}), 400

    file = request.files["file"]

    # Read the file into a DataFrame and apply consistent feature preprocessing
    raw_batch_df = pd.read_csv(file)
    input_data = engineer_features(raw_batch_df)

    # Make predictions for the batch data
    predictions = model.predict(input_data).tolist()

    # Create an output dictionary mapping row index to predicted sales
    output_dict = {str(i): round(float(pred), 2) for i, pred in enumerate(predictions)}

    return jsonify(output_dict)


# Run the Flask app
if __name__ == "__main__":
    superkart_api.run(host="0.0.0.0", port=5000, debug=True)