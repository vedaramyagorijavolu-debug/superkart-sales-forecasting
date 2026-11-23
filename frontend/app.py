import pandas as pd
import requests
import streamlit as st

# Base URL of the Flask backend inside the Docker network
# Note: Your Flask app.py currently runs on port 5000 unless updated/mapped to 7860
BACKEND_URL = "http://backend:7860"

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

# Page title
st.title("SuperKart System")
st.write("Enter the product and store details below to predict the total sales.")

# Input fields for the 10 model features (matching the notebook payload defaults)
Product_Weight = st.number_input("Product Weight", min_value=0.0, value=12.66)
Product_Sugar_Content = st.selectbox(
    "Product Sugar Content", ["Low Sugar", "Regular", "No Sugar"]
)
Product_Allocated_Area = st.number_input(
    "Product Allocated Area", min_value=0.0, value=0.027
)
Product_MRP = st.number_input("Product MRP", min_value=0.0, value=117.08)
Store_Size = st.selectbox("Store Size", ["Small", "Medium", "High"], index=1)
Store_Location_City_Type = st.selectbox(
    "Store Location City Type", ["Tier 1", "Tier 2", "Tier 3"], index=1
)
Store_Type = st.selectbox(
    "Store Type",
    [
        "Supermarket Type1",
        "Supermarket Type2",
        "Supermarket Type3",
        "Departmental Store",
        "Food Mart",
    ],
    index=1,
)
Product_Id_char = st.selectbox("Product ID Character", ["FD", "DR", "NC"], index=0)
Store_Age_Years = st.number_input("Store Age (Years)", min_value=0, step=1, value=16)
Product_Type_Category = st.selectbox(
    "Product Type Category", ["Non Perishables", "Perishables"], index=0
)

# Build JSON payload matching FEATURE_COLUMNS
product_data = {
    "Product_Weight": float(Product_Weight),
    "Product_Sugar_Content": Product_Sugar_Content,
    "Product_Allocated_Area": float(Product_Allocated_Area),
    "Product_MRP": float(Product_MRP),
    "Store_Size": Store_Size,
    "Store_Location_City_Type": Store_Location_City_Type,
    "Store_Type": Store_Type,
    "Product_Id_char": Product_Id_char,
    "Store_Age_Years": int(Store_Age_Years),
    "Product_Type_Category": Product_Type_Category,
}

# Single Prediction (/v1/predict returns {"Sales": round(prediction, 2)})
if st.button("Predict", type="primary"):
    try:
        response = requests.post(
            f"{BACKEND_URL}/v1/predict",
            json=product_data,
            timeout=30,
        )
        if response.status_code == 200:
            result = response.json()
            predicted_sales = float(result["Sales"])
            st.success(f"Predicted Product Store Sales Total: ₹{predicted_sales:.2f}")
        else:
            st.error(f"API Error ({response.status_code}): {response.text}")
    except requests.RequestException as e:
        st.error(f"Unable to connect to the prediction API: {e}")

# Batch Prediction (/v1/predictbatch returns {"0": sales_0, "1": sales_1, ...})
st.subheader("Batch Prediction")
st.caption(f"Expected columns: {', '.join(FEATURE_COLUMNS)}")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        preview_df = pd.read_csv(uploaded_file)
        st.dataframe(preview_df.head(), use_container_width=True)
        uploaded_file.seek(0)
    except Exception as e:
        st.warning(f"Could not preview CSV: {e}")

    if st.button("Predict for Batch", type="primary"):
        try:
            # Reset pointer and send CSV bytes under 'file'
            uploaded_file.seek(0)
            csv_bytes = uploaded_file.getvalue()

            response = requests.post(
                f"{BACKEND_URL}/v1/predictbatch",
                files={"file": (uploaded_file.name, csv_bytes, "text/csv")},
                timeout=60,
            )

            if response.status_code == 200:
                results = response.json()
                st.success("Predictions completed successfully!")

                # Flask /v1/predictbatch returns {"0": 1234.56, "1": 2345.67, ...}
                if isinstance(results, dict):
                    pred_series = pd.Series(results, name="Predicted_Sales").astype(
                        float
                    )
                    pred_series.index = pred_series.index.astype(int)
                    pred_df = pred_series.sort_index().reset_index()
                    pred_df.columns = ["Row_Index", "Predicted_Sales"]
                    st.dataframe(pred_df, use_container_width=True)
                else:
                    st.json(results)
            else:
                st.error(f"API Error ({response.status_code}): {response.text}")
        except requests.RequestException as e:
            st.error(f"Unable to connect to the prediction API: {e}")