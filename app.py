import plotly.graph_objects as go
import streamlit as st
import plotly.express as px
import pandas as pd

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from Backend import create_employee_dict, dailyDuration, overTimeCalculator, dateConversion, holidayCalculation, halfDaysCalculation
from Backend import lateAndEarlyLeaveCalculation, compOffCalculation,total_workingdays_calculation,merge_dictionaries
from Backend import finalProcessing, dict_to_dataframe, process_uploaded_file
from Backend import process_employee_hroneData,dict_cleaning,statusFilling,minorprocessing

st.set_page_config(layout="wide")


def main():
    st.sidebar.title("What You Doing ❓")
    options = st.sidebar.radio("Go to", ["Home 🏠", "Report Generator 🛠️", "Monthly Dashboard 🗓️", "Insights and trends analysis 🔍"])

    if options == "Home 🏠":

        st.title("Welcome Team HR 🙋‍♂️")
        col1,col2 = st.columns([1,2])

        with col1:
            st.subheader("What it do for you ❓")
            st.write('This application is designed to streamline employee attendance and performance tracking, making it easier to manage key metrics such as working hours, leaves, absenteeism, and more. By automating these calculations, it saves time and reduces errors, providing an all-in-one dashboard that offers clear insights into individual performance.')
            st.write("")
            st.write("With this tool, Human Resources can easily analyze patterns, track trends, and make data-driven decisions that improve team efficiency. The goal is simple: to lighten your workload and enhance productivity, all while making the process effortless")
            st.divider()
            st.write('Made with care to help you work smarter!')


        with col2:
            st.subheader("How to use this tool 🤔")
            st.write("1️⃣ Monthly Report Generation:")
            st.write("1. Upload the biometric data in CSV format and the HR One Excel file.\n 2. Select the month for which the report needs to be generated.\n 3. Click on Generate Report, and you will receive a downloadable Excel file with detailed attendance, leave, and time metrics for further analysis.")
            st.write('')
            st.write("2️⃣ Monthly Dashboard Generation:")
            st.write('Select the month to generate a visual dashboard.Analyze trends and insights based on the generated report to support data-driven decisions.')
    elif options == "Report Generator 🛠️":
        st.title("Report Generator 🛠️")
        # File uploader
        uploaded_file = st.file_uploader("Upload your Bio metric extracted report csv", type="csv")
        uploaded_file_hrone = st.file_uploader("upload your HR one Report of same month", type="xlsx")

        # Input for month selection
        month = st.selectbox("Select the month", ["January", "February", "March", "April", "May", "June",
                                                  "July", "August", "September", "October", "November", "December"])

        # Input for holidays
        holidays = st.text_input("Enter holidays separated by comma in DD-MM-YYYY format", value="")
        holidays_list = holidays.split(", ")

        if uploaded_file and uploaded_file_hrone is not None:
            employee_dict = process_uploaded_file(uploaded_file)  # Process uploaded file
            employee_dict_hrone = process_employee_hroneData(uploaded_file_hrone)
            employee_dict_hrone = dict_cleaning(employee_dict_hrone)
            employee_dict_hrone = statusFilling(employee_dict_hrone)
            employee_dict_hrone = minorprocessing(employee_dict_hrone)

            if employee_dict:
                st.write("Employee data has been processed. Click the button below to generate the report.")

                # Button to generate the report
                if st.button("Generate Report"):
                    employee_dict = dateConversion(employee_dict, month=month, year='2024')
                    employee_dict = merge_dictionaries(employee_dict, employee_dict_hrone)
                    employee_dict = dailyDuration(employee_dict)
                    employee_dict = overTimeCalculator(employee_dict)
                    employee_dict = halfDaysCalculation(employee_dict)
                    employee_dict = holidayCalculation(employee_dict, holidays=holidays_list)
                    employee_dict = compOffCalculation(employee_dict)
                    employee_dict = total_workingdays_calculation(employee_dict, holidays=holidays_list)
                    employee_dict = lateAndEarlyLeaveCalculation(employee_dict)
                    employee_dict = finalProcessing(employee_dict)
                    data = dict_to_dataframe(employee_dict)

                    # Store employee_dict in session state
                    st.session_state.employee_dict = employee_dict
                    # st.session_state.data = data

                    st.write(f"Employee Report For {month} 2024:")
                    st.write(data)

                    csv = data.to_csv(index=False).encode('utf-8')
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

        if st.session_state.employee_dict:
            # Filter by employee name in the sidebar
            employee_names = list(st.session_state.employee_dict.keys())
            selected_employee = st.sidebar.selectbox("Select Employee", employee_names)
            # Get the employee data from employee_dict
            employee_data = st.session_state.employee_dict[selected_employee]
            # employee_data_df = st.session_state.data[selected_employee]
            st.title(f"{selected_employee} Dashboard")
            # Custom CSS to style each card-like structure
            st.markdown("""
                <style>
                .card {
                    padding: 15px;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
                    margin: 5px;
                    text-align: center;
                    background-color: #F5F5F7;
                }
                .card-title {
                    font-size: 20px;
                    font-weight: semi-bold;
                    color: #333;
                }
                .card-value {
                    font-size: 18px;
                    font-weight: bold;
                    color: #16325B;
                }
                </style>
            """, unsafe_allow_html=True)

            # Creating the card structure for each column
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

            # Employee Name Card
            with col1:
                st.markdown(f"""
                    <div class="card">
                        <div class="card-title">Employee Name</div>
                        <div class="card-value">{selected_employee}</div>
                    </div>
                """, unsafe_allow_html=True)

            # Total Overtime Card
            with col2:
                employeeOvertime = employee_data['totalOverTime']
                st.markdown(f"""
                    <div class="card">
                        <div class="card-title">Total Overtime</div>
                        <div class="card-value">{employeeOvertime} hr</div>
                    </div>
                """, unsafe_allow_html=True)

            # Incomplete Hours Card
            with col3:
                employeeIncompletehours = employee_data['totalEarlyLeave']
                st.markdown(f"""
                    <div class="card">
                        <div class="card-title">Incomplete Hours</div>
                        <div class="card-value">{employeeIncompletehours} hr</div>
                    </div>
                """, unsafe_allow_html=True)

            # Total Compensatory Leaves Card
            with col4:
                employeeCompoffs = employee_data['comp_off']
                st.markdown(f"""
                    <div class="card">
                        <div class="card-title">Compensatory Leaves</div>
                        <div class="card-value">{employeeCompoffs} Days</div>
                    </div>
                """, unsafe_allow_html=True)
            st.write('\n\n')
            st.divider()
            st.write('\n')
            #### Line and Bar Graphs #######
            # Sample data from employee_dict (as per your example)
            dates = employee_data['Days']
            working_hours = employee_data['DailyWorkingHours']
            overtime_hours = employee_data['actualOvertime']

            # Convert 'HH:MM' strings to hours (float) and handle 'NaT' values
            def convert_to_hours(time_str):
                if time_str == 'NaT':
                    return None  # Treat 'NaT' as None, which will be filtered out
                hours, minutes = map(int, time_str.split(':'))
                return hours + minutes / 60  # Convert HH:MM to fractional hours

            # Convert float hours back to HH:MM format for display
            def hours_to_hhmm(hours_float):
                if hours_float is None:
                    return None
                hours = int(hours_float)
                minutes = int((hours_float - hours) * 60)
                return f"{hours:02d}:{minutes:02d}"  # Return formatted as HH:MM

            # Apply the conversion and filter out NaT values for both working hours and overtime
            working_hours_in_float = [convert_to_hours(time) for time in working_hours]

            # Convert overtime to hours and filter out values less than or equal to 55 minutes, and scale them
            scaling_factor = 1  # You can adjust this factor for better visibility
            overtime_in_float = [
                (convert_to_hours(time) if convert_to_hours(time) and convert_to_hours(
                    time) > 55 / 60 else 0) * scaling_factor
                for time in overtime_hours
            ]

            # Create a DataFrame with cleaned data
            cleaned_data = pd.DataFrame({
                'Date': dates,
                'Working Hours': working_hours_in_float,
                'Overtime Hours': overtime_in_float
            }).dropna(subset=['Working Hours'])  # Drop rows with None (NaT) for working hours

            # Create the figure
            fig = go.Figure()

            # Add line chart for working hours
            fig.add_trace(
                go.Scatter(
                    x=cleaned_data['Date'],
                    y=cleaned_data['Working Hours'],
                    mode='lines+markers',
                    name='Working Hours',
                    line=dict(color='#16325B', width=3),
                    marker=dict(size=8),
                )
            )

            # Add bar chart for overtime hours (scaled)
            fig.add_trace(
                go.Bar(
                    x=cleaned_data['Date'],
                    y=cleaned_data['Overtime Hours'],
                    name='Overtime Hours (scaled)',
                    marker_color='#37B7C3',
                    opacity=0.8  # Make bars slightly transparent for better visibility
                )
            )
            # Convert y-axis values to HH:MM format for labels
            # This will show values from 0 hours to 14 hours in HH:MM format
            y_values = [i for i in range(0, 15)]  # Values from 0 to 14 hours
            y_labels = [hours_to_hhmm(val) for val in y_values]  # Convert to HH:MM format

            # Customize the layout to show everything on the same y-axis
            fig.update_layout(
                title=f"Working Hours and Overtime Trend of {selected_employee}",
                xaxis=dict(title="Date", tickmode='linear', dtick=1),  # Ensure all days are shown on x-axis
                yaxis=dict(
                    title="Working Hours",  # Y-axis for both Working Hours and scaled Overtime
                    range=[0, 14],  # Adjust the range based on expected working hours
                    tickvals=y_values,  # The values to show on the y-axis
                    ticktext=y_labels  # The corresponding HH:MM labels
                ),
                height=500,
                width=1500,
                showlegend=False,  # Show the legend to differentiate the two plots
                legend=dict(x=0.1, y=1.1),  # Adjust legend position
                margin=dict(l=0, r=0, t=25, b=0)  # Adjust margins to fit everything neatly
            )

            # Display the combined chart in Streamlit
            st.plotly_chart(fig, use_container_width=True)

            ###### Line and bar chart ends ###

            st.divider()

            # Layout for the dashboard: 33% and 66% parts
            col1, col2 = st.columns([1, 2])
            with col1:
                # Convert employee's total working hours to float
                employee_working = employee_data['TotalWorkingHours']
                supposed_working_days = employee_data['totalOfficeWorkingDays']

                # Assuming the employee is supposed to work 9 hours per day
                expected_working_hours = supposed_working_days * 9
                # Convert total working hours from 'HH:MM' format to float (hours)
                employee_working_float = convert_to_hours(employee_working)

                # Determine the maximum range for the gauge to account for overflow
                max_gauge_value = max(expected_working_hours,
                                      employee_working_float) * 1.2  # Adding 20% buffer for overflow

                # Create a gauge chart for total working hours
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=employee_working_float,  # Employee's actual total working hours
                    gauge={
                        'axis': {'range': [0, max_gauge_value], 'tickvals': [0, expected_working_hours]},
                        # Only display 0 and expected hours
                        'bar': {'color': "#071952"},  # Bar color
                        'threshold': {
                            'line': {'color': "red", 'width': 4},  # Red threshold line
                            'thickness': 0.85,
                            'value': expected_working_hours  # Threshold at expected working hours
                        },
                    },
                    number={
                        'suffix': " hr",  # Display units as hours
                        'font': {'size': 35, 'weight': 'bold', 'color': '#476072'}  # Adjust font size here
                    }
                ))

                # Adjust the layout to reduce the figure size
                fig_gauge.update_layout(
                    title={'text': "Working Hours"},
                    width=200,
                    height=220,  # Reduce the height of the gauge
                    margin=dict(t=25, b=15, l=55, r=55)  # Add some margin
                )

                # Display gauge chart in Streamlit
                st.plotly_chart(fig_gauge, use_container_width=True)


            with col2:
                ######### Heatmaps #######

                # Prepare the data for both heatmaps
                dates = employee_data['Days']
                absences = employee_data['AbsentDays']
                halfdays = employee_data['isHalfDay']
                latePunch = employee_data['isLate']

                # Create the subplot with 2 rows and 1 column
                fig = make_subplots(
                    rows=3, cols=1,
                    shared_xaxes=True,  # Share the x-axis (dates) between the two heatmaps
                    vertical_spacing=0.08,  # Add some space between the two heatmaps

                )
                # Absentee heatmap (first row)
                fig.add_trace(
                    go.Heatmap(
                        z=[absences],  # Data for absenteeism
                        x=dates,  # Dates on the x-axis
                        y=['Absent'],  # Empty y-axis label
                        colorscale=[(0, "#EEEDED"), (1, "#DA1212")],  # Grey for present, red for absent
                        zmin=0,  # Minimum value for z
                        zmax=1,  # Maximum value for z
                        showscale=False,  # Hide color scale
                        xgap=4,  # Horizontal gap between boxes
                        ygap=1,  # Vertical gap between boxes
                    ),
                    row=3, col=1  # Position in the subplot
                )
                # Half Day heatmap (second row)
                fig.add_trace(
                    go.Heatmap(
                        z=[halfdays],  # Data for half days
                        x=dates,  # Dates on the x-axis
                        y=['HalfDay'],  # Empty y-axis label
                        colorscale=[(0, "#EEEDED"), (1, "#F0DE36")],  # Grey for full day, yellow for half day
                        zmin=0,  # Minimum value for z
                        zmax=1,  # Maximum value for z
                        showscale=False,  # Hide color scale
                        xgap=4,  # Horizontal gap between boxes
                        ygap=1,  # Vertical gap between boxes
                    ),
                    row=2, col=1  # Position in the subplot
                )
                # Late heatmap (Third row)
                fig.add_trace(
                    go.Heatmap(
                        z=[latePunch],  # Data for half days
                        x=dates,  # Dates on the x-axis
                        y=['Late punch'],  # Empty y-axis label
                        colorscale=[(0, "#EEEDED"), (1, "#E85C0D")],  # Grey for full day, yellow for half day
                        zmin=0,  # Minimum value for z
                        zmax=1,  # Maximum value for z
                        showscale=False,  # Hide color scale
                        xgap=4,  # Horizontal gap between boxes
                        ygap=1,  # Vertical gap between boxes
                    ),
                    row=1, col=1  # Position in the subplot
                )

                # Update the layout for both heatmaps
                fig.update_layout(
                    height=165,  # Total height for both rows (160 + 160)
                    width=1000,  # Wider layout to ensure all dates are visible
                    margin=dict(l=0, r=0, t=5, b=0),  # Minimal margins
                    xaxis=dict(showgrid=False),  # No grid for a cleaner look
                    yaxis=dict(showgrid=False),  # No grid for a cleaner look
                    xaxis2=dict(showgrid=False),  # No grid for second subplot (Half Days)
                    yaxis2=dict(showgrid=False),  # No grid for second subplot (Half Days)
                    xaxis3 = dict(showgrid=False),  # No grid for second subplot (Half Days)
                    yaxis3 = dict(showgrid=False)  # No grid for second subplot (Half Days)
                )

                # Set the subplot titles (optional)
                fig.update_annotations(font_size=12)

                # Display the combined heatmap in Streamlit
                st.plotly_chart(fig, use_container_width=True)

                ######### Heatmap ends #######

        else:
            st.error("Please generate the report first in the 'Report Generator' section.")

    elif options == "Insights and trends analysis 🔍":
        st.write ('Coming soon !')
if __name__ == "__main__":
    main()
