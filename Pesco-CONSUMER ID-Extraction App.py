import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import io

# ---------------------------------------------
# Streamlit UI
# ---------------------------------------------

st.markdown("""
    <style>
        .main {
            background-image: url("https://images.unsplash.com/photo-1532619187608-e5375cab36c9?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80");
            background-size: cover;
            background-attachment: fixed;
        }

        .designer {
            text-align: center;
            font-size: 26px;
            color: #ffffff;
            font-weight: bold;
            margin-top: 20px;
            font-family: 'Arial', sans-serif;
        }

        .center-title {
            text-align: center;
            color: #ffffff;
            background-color: rgba(0, 0, 0, 0.6);
            padding: 1rem;
            border-radius: 10px;
            font-family: 'Arial', sans-serif;
            margin-top: 10px;
        }

        .dedication {
            text-align: center;
            font-size: 18px;
            margin-top: -10px;
            color: #dddddd;
        }
    </style>

    <div class="designer">👨‍💻 Designed by Engr. Ozair Khan</div>

    <div class="center-title">
        <h1>🔍 PESCO Bill Extractor Tool</h1> 
        <p class="dedication">🎓 Dedicated to Engr. Bilal Ahmad</p>
    </div>
""", unsafe_allow_html=True)

# Use session_state to preserve downloaded file
if "excel_data" not in st.session_state:
    st.session_state.excel_data = None

uploaded_file = st.file_uploader("📤 Upload your Excel file", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        df = df.where(pd.notnull(df), "")  # Fill NaN with empty strings
        st.success("✅ File uploaded successfully.")
        st.write("📄 Preview of Uploaded Data:")
        st.dataframe(df)

        selected_col = st.selectbox("1️⃣ Select the column containing Account Numbers:", df.columns)

        target_col = st.selectbox("2️⃣ Select the column where Customer ID should be saved:",
                                  df.columns.tolist() + ["➕ Create new column..."])

        if target_col == "➕ Create new column...":
            new_col_name = st.text_input("Enter name for new column:")
            if new_col_name:
                if new_col_name not in df.columns:
                    df[new_col_name] = ""
                    target_col = new_col_name
                else:
                    st.warning("⚠️ Column already exists. Please choose another name.")
                    st.stop()

        if st.checkbox("⚠️ I understand this will modify the selected column with extracted data. Proceed?"):
            if st.button("🚀 Start Extracting Customer IDs"):

                with st.spinner("🔄 Please wait... Extracting data from PESCO website..."):

                    chrome_options = Options()
                    chrome_options.add_argument("--disable-gpu")
                    chrome_options.add_argument("--no-sandbox")
                    chrome_options.add_argument("--disable-dev-shm-usage")

                    driver = webdriver.Chrome(service=Service(), options=chrome_options)
                    wait = WebDriverWait(driver, 10)

                    try:
                        driver.get("https://bill.pitc.com.pk/pescobill")
                        time.sleep(1)

                        for i, (index, row) in enumerate(df.iterrows(), start=1):
                            acc_raw = row[selected_col]

                            try:
                                acc_str = str(int(float(acc_raw))).zfill(14)
                            except:
                                df.at[index, target_col] = ""
                                continue

                            if len(acc_str) != 14:
                                df.at[index, target_col] = ""
                                continue

                            # Show currently processing
                            st.info(f"🔁 [{i}] Extracting data for Account: {acc_str}")

                            try:
                                input_box = wait.until(EC.presence_of_element_located((By.ID, "searchTextBox")))
                                input_box.clear()
                                input_box.send_keys(acc_str)
                                input_box.send_keys(Keys.ENTER)
                                time.sleep(3)

                                try:
                                    consumer_id_td = driver.find_element(
                                        By.XPATH,
                                        "//tr[contains(@class,'fontsize') and contains(@class,'content')]/td[1]"
                                    )
                                    consumer_id = consumer_id_td.text.strip()
                                    df.at[index, target_col] = consumer_id
                                except Exception:
                                    df.at[index, target_col] = ""

                                driver.get("https://bill.pitc.com.pk/pescobill")
                                time.sleep(1)

                            except Exception:
                                df.at[index, target_col] = "ERROR"

                    finally:
                        driver.quit()

                    st.success("✅ Extraction completed successfully.")
                    st.write("🔎 Final Updated Data:")
                    st.dataframe(df)

                    @st.cache_data
                    def to_excel(df: pd.DataFrame):
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine="openpyxl") as writer:
                            df[selected_col] = df[selected_col].astype(str)  # Force text
                            df.to_excel(writer, index=False, sheet_name="Data")
                        return output.getvalue()

                    st.session_state.excel_data = to_excel(df)

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")

# Keep download button even after refresh
if st.session_state.excel_data:
    st.download_button(
        label="📥 Download Updated Excel",
        data=st.session_state.excel_data,
        file_name="updated_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )
