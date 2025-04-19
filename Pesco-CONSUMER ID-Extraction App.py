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

# Streamlit UI Enhancements
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
        <p class="dedication">🎓 Dedicated to Engr. Bilal Shalman</p>
    </div>
""", unsafe_allow_html=True)


uploaded_file = st.file_uploader("📤 Upload your Excel file", type=["xlsx", "xls"])

if uploaded_file:
    try:
        # Read the uploaded file
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        st.success("✅ File uploaded successfully.")

        # Replace NaN or None values with empty strings (for display purposes)
        df = df.where(pd.notnull(df), "")

        st.write("📄 Preview of Uploaded Data:")
        st.dataframe(df)

        # Step 1: Ask user which column contains Account Numbers
        selected_col = st.selectbox("1️⃣ Select the column containing Account Numbers:", df.columns)

        # Step 2: Ask user which column to store the Customer ID
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

        # Step 3: Show Warning Before Scraping
        if st.checkbox("⚠️ I understand this will modify the selected column with extracted data. Proceed?"):

            # Step 4: Start Button
            if st.button("🚀 Start Extracting Customer IDs"):

                # Show a wait message
                with st.spinner("🔄 Please wait... Extracting data from PESCO website..."):

                    # Set up Selenium
                    chrome_options = Options()
                    chrome_options.add_argument("--disable-gpu")
                    chrome_options.add_argument("--no-sandbox")
                    chrome_options.add_argument("--disable-dev-shm-usage")
                    driver = webdriver.Chrome(service=Service(), options=chrome_options)
                    wait = WebDriverWait(driver, 10)

                    try:
                        driver.get("https://bill.pitc.com.pk/pescobill")
                        time.sleep(1)
                        i = 1

                        for index, row in df.iterrows():
                            acc_raw = row[selected_col]

                            # Convert to string and clean format (ensure exactly 14 digits)
                            try:
                                acc_str = str(int(float(acc_raw))).zfill(14)  # Ensure 14 digits, strip scientific
                            except:
                                df.at[index, target_col] = ""
                                continue

                            if len(acc_str) != 14:
                                df.at[index, target_col] = ""
                                continue

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
                                    i += 1
                                except Exception:
                                    df.at[index, target_col] = ""
                                    i += 1

                                driver.get("https://bill.pitc.com.pk/pescobill")
                                time.sleep(1)

                            except Exception:
                                df.at[index, target_col] = "ERROR"

                    finally:
                        driver.quit()

                    # Show result
                    st.success("✅ Congratulation Extraction completed Successfully.")
                    st.write("🔎 Final Updated Data:")
                    st.dataframe(df)


                    # Add download button
                    @st.cache_data
                    def to_excel(df: pd.DataFrame):
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine="openpyxl") as writer:
                            # Ensure the account column stays as text
                            df[selected_col] = df[selected_col].astype(str)
                            df.to_excel(writer, index=False, sheet_name="Data")
                        return output.getvalue()


                    # Button to download the updated Excel file
                    excel_data = to_excel(df)
                    st.download_button(
                        label="📥 Download Updated Excel",
                        data=excel_data,
                        file_name="updated_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
