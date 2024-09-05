import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from Backend import (process_uploaded_file,
                     create_employee_dict,calculate_daily_durations,Early_over_time_calculation,
                     half_day_calculation,leave_calculation,latePunch_calculation,dateConversion,
                     finalCalculations_processing,present_calculator,actual_overtime_calculation,
                     report_dataframe_creator,calculation_adjustments)

# Set page layout to wide
st.set_page_config(layout="wide")
def main():
    st.sidebar.title("What You Doing ❓")
    options = st.sidebar.radio("Go to", ["Home 🏠", "Report Generator 🛠️", "Monthly Dashboard 🗓️"])

    if options == "Home 🏠":
        st.title("Welcome Boi")
        st.write("This is the Home Page.")

    elif options == "Report Generator 🛠️":
        st.title("Report Generator 🛠️")
        # File uploader
        uploaded_file = st.file_uploader("Upload the monthly report csv", type="csv")

        # Input for month selection
        month = st.selectbox("Select the month", ["January", "February", "March", "April", "May", "June",
                                                  "July", "August", "September", "October", "November", "December"])

        # Input for holidays
        holidays = st.text_input("Enter holidays separated by comma in \n DD-MM-YYYY format", value="")
        holidays_list = holidays.split(", ")

        if uploaded_file is not None:
            employee_dict = process_uploaded_file(uploaded_file)

            if employee_dict:
                st.write("Employee data has been processed. Click the button below to generate the report.")

                # Button to generate the report
                if st.button("Generate Report"):
                    employee_dict = calculate_daily_durations(employee_dict)
                    employee_dict = Early_over_time_calculation(employee_dict)
                    employee_dict = half_day_calculation(employee_dict)
                    employee_dict = leave_calculation(employee_dict)
                    employee_dict = latePunch_calculation(employee_dict)
                    employee_dict = dateConversion(employee_dict, month=month, year='2024')
                    employee_dict = finalCalculations_processing(employee_dict, holidays_list)
                    employee_dict = present_calculator(employee_dict, holidays_list)
                    employee_dict = actual_overtime_calculation(employee_dict)
                    # employee_dict = adjustment(employee_dict)
                    report_dataframe = report_dataframe_creator(employee_dict)
                    updated_dataframe = calculation_adjustments(report_dataframe)

                    st.write("Final Report DataFrame:")
                    st.write(updated_dataframe)

                    csv = updated_dataframe.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Report",
                        data=csv,
                        file_name=f'employee_report_{month}.csv',
                        mime='text/csv',
                    )
            else:
                st.error("Failed to process the CSV file. Please check the file format.")
        else:
            st.error("Please upload a CSV file.")

    elif options == "Monthly Dashboard 🗓️":
        st.title("Monthly Dashboard")
        st.write("This section is under construction.")

if __name__ == "__main__":
    main()

