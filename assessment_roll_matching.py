import streamlit as st
import pandas as pd 
import pymysql
import toml

# Load the configuration file
config = toml.load("config.toml")

# Replace with your desired credentials
USERNAME = config['USERNAME']
PASSWORD = config['PASSWORD']

# Define a function to check username and password
def check_credentials(username, password):
    return username == USERNAME and password == PASSWORD

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Authentication block
if not st.session_state.authenticated:
    st.title('Assessment Roll Matching Tool')
    
    # Create two input fields for username and password
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    # Check if the login button is pressed and credentials are correct
    if st.button("Login"):
        if check_credentials(username, password):
            st.session_state.authenticated = True
            st.success("Login successful. Please proceed.")
        else:
            st.error("Invalid username or password")

# If authenticated, show the main app
if st.session_state.authenticated:
    st.title('Assessment Roll Matching Tool')

    # Function to query the database
    def TP_Query(county, state):
        connection = pymysql.connect(
            host=config['HOST'],
            user=config['USER'],
            password=config['PASS'],
            database=config['DATA'],
            charset=config['CHAR'],
            cursorclass=pymysql.cursors.DictCursor
        )
        try: 
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                    p.parcel_id
                    FROM ebdb.main_parcel p 
                    JOIN ebdb.main_property pr on p.property_id = pr.id
                    JOIN ebdb.main_address a on pr.address_id = a.id
                    WHERE a.county = %s
                    AND a.state = %s
                    """, (county, state))
                result = cursor.fetchall()
                df1 = pd.DataFrame(result)
                return df1
        finally:
            connection.close()

    county = st.text_input('What is the County of the Assessment Roll?').strip()
    state = st.text_input('What is the state of the Assessment Roll? (2 Letter Abbreviation)').strip()

    uploaded_file = st.file_uploader("Upload an Assessment Roll CSV file", type=["csv"])

    if uploaded_file is not None: 
        df = pd.read_csv(uploaded_file)
        st.write(df.head())

        st.write('Please select the Parcel ID, Market Value, Building Value, Land Value, and Extra Feature Value Columns from the roll')
        parcel_id = st.selectbox('Parcel ID Column', ["Not Selected"] + list(df.columns))
        market_value = st.selectbox('Market Value Column', ["Not Selected"] + list(df.columns))
        building_value = st.selectbox('Building Value Column', ["Not Selected"] + list(df.columns))
        land_value = st.selectbox('Land Value Column', ["Not Selected"] + list(df.columns))
        extra_feature_value = st.selectbox('Extra Feature Value Column', ["Not Selected"] + list(df.columns))

        # Verify selected columns exist in the DataFrame
        selected_columns = [parcel_id, market_value, building_value, land_value, extra_feature_value]
        for col in selected_columns:
            if col not in df.columns:
                st.error(f"Column '{col}' not found in the uploaded file.")
                st.stop()

        # Rename and clean the parcel_id column
        df.rename(columns={parcel_id: 'parcel_id'}, inplace=True)
        
        # Convert parcel_id column to string type before applying string operations
        df['parcel_id'] = df['parcel_id'].astype(str)
        df['parcel_id'] = df['parcel_id'].str.strip().str.replace('-','').str.replace('.','').str.replace(' ','')
        
        # Select relevant columns
        df = df[['parcel_id', market_value, building_value, land_value, extra_feature_value]]

        if st.button('Submit'):
            # Query the database
            df1 = TP_Query(county, state)

            # Merge the dataframes on 'parcel_id'
            merged_df = pd.merge(df, df1, on='parcel_id', how='inner')

            # Convert the merged dataframe to CSV
            csv = merged_df.to_csv(index=False)

            # Download button for CSV
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name='query_results.csv',
                mime='text/csv'
            )
