import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

from datetime import datetime
from datetime import datetime, timedelta
import pandas as pd

from datetime import datetime
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
def process_uploaded_file(uploaded_file):
    if uploaded_file is not None:
        employee_data = create_employee_dict(uploaded_file)
        st.success("Employee data processed successfully!")
        return employee_data
    return None


def create_employee_dict(csv_file):
    # Read the CSV file
    df = pd.read_csv(csv_file, header=None)
    df.dropna(axis=1, how='all', inplace=True)

    # Initialize the dictionary to hold the final data
    employee_data = {}

    # Loop through the DataFrame by locating the employee name and then slicing the DataFrame
    i = 0
    while i < len(df):
        if pd.notna(df.iloc[i, 0]):  # Find employee name
            employee_name = df.iloc[i, 0]
            i += 1  # Move to the next row
            employee_dict = {
                'Days': list(df.iloc[i, 1:]),
                'Status': list(df.iloc[i + 1, 1:]),
                'InTime': [str(x) if pd.notna(x) else 'NaT' for x in df.iloc[i + 2, 1:]],
                'OutTime': [str(x) if pd.notna(x) else 'NaT' for x in df.iloc[i + 3, 1:]]
            }
            # Store the employee's data in the dictionary
            employee_data[employee_name] = employee_dict
            # Skip over the processed rows
            i += 8
        i += 1  # Continue to the next employee section

    return employee_data


def dailyDuration(employee_dict):
    # Helper function to convert string time to datetime
    def time_conversion(time_str):
        try:
            return datetime.strptime(time_str, '%H:%M') if time_str != 'NaT' else 'NaT'
        except ValueError:
            return 'NaT'

    # Iterate through each employee in the dictionary
    for employee, data in employee_dict.items():
        in_times = data.get('InTime', [])
        out_times = data.get('OutTime', [])
        daily_working_hours = []
        total_duration = timedelta()  # Initialize total duration
        valid_days = 0  # Counter for valid days

        # Iterate through each day's InTime and OutTime
        for in_time_str, out_time_str in zip(in_times, out_times):
            in_time = time_conversion(in_time_str)
            out_time = time_conversion(out_time_str)

            # Calculate duration only if both InTime and OutTime are available
            if in_time != 'NaT' and out_time != 'NaT':
                # Check if OutTime is before InTime (meaning it's past midnight)
                if out_time < in_time:
                    # Add 24 hours to the OutTime to account for the next day
                    out_time += timedelta(hours=24)

                # Calculate the time difference (working hours)
                duration = out_time - in_time
                total_duration += duration  # Add to total duration
                valid_days += 1  # Increment valid days count

                # Extract hours and minutes from the duration
                hours, remainder = divmod(duration.total_seconds(), 3600)
                minutes = remainder // 60

                # Format to HH:MM
                formatted_duration = f'{int(hours):02}:{int(minutes):02}'
                daily_working_hours.append(formatted_duration)
            else:
                # If any time is NaT, add 'NaT' for that day
                daily_working_hours.append('NaT')

        # Add DailyWorkingHours to the employee's data
        employee_dict[employee]['DailyWorkingHours'] = daily_working_hours

        # Calculate total working hours in HH:MM format
        total_hours, remainder = divmod(total_duration.total_seconds(), 3600)
        total_minutes = remainder // 60
        total_working_hours = f'{int(total_hours):02}:{int(total_minutes):02}'

        employee_dict[employee]['TotalWorkingHours'] = total_working_hours

        # Calculate average working hours in HH:MM format
        if valid_days > 0:
            average_duration = total_duration / valid_days
            avg_hours, avg_remainder = divmod(average_duration.total_seconds(), 3600)
            avg_minutes = avg_remainder // 60
            average_working_hours = f'{int(avg_hours):02}:{int(avg_minutes):02}'
        else:
            average_working_hours = '00:00'  # Default if no valid days

        employee_dict[employee]['AverageWorkingHours'] = average_working_hours

    return employee_dict


def overTimeCalculator(employee_dict):
    # Helper function to convert time from 'HH:MM' to total seconds
    def time_to_seconds(time_str):
        if time_str == 'NaT':
            return None
        hours, minutes = map(int, time_str.split(':'))
        return hours * 3600 + minutes * 60

    # Helper function to convert total seconds to 'HH:MM' format
    def seconds_to_time(seconds):
        if seconds <= 0:
            return '00:00'
        hours, remainder = divmod(seconds, 3600)
        minutes = remainder // 60
        return f'{int(hours):02}:{int(minutes):02}'

    # The standard shift duration in seconds (9 hours)
    standard_shift_seconds = 9 * 3600

    # Iterate through each employee in the dictionary
    for employee, data in employee_dict.items():
        daily_working_hours = data.get('DailyWorkingHours', [])
        actual_overtime = []
        total_overtime_seconds = 0  # To calculate total overtime
        real_total_overtime_seconds = 0  # To calculate real total overtime

        # Iterate through each day's working hours
        for work_hours in daily_working_hours:
            if work_hours != 'NaT':
                # Convert the working hours to seconds
                work_seconds = time_to_seconds(work_hours)

                # Check if the working hours are above the standard shift time
                if work_seconds > standard_shift_seconds:
                    # Calculate overtime in seconds
                    overtime_seconds = work_seconds - standard_shift_seconds
                    total_overtime_seconds += overtime_seconds  # Add to total overtime

                    # Only consider overtime greater than 1 hour for real total overtime
                    if overtime_seconds > 3600:
                        real_total_overtime_seconds += overtime_seconds

                    # Convert overtime to 'HH:MM' format
                    actual_overtime.append(seconds_to_time(overtime_seconds))
                else:
                    # No overtime if less than or equal to 9 hours
                    actual_overtime.append('00:00')
            else:
                # Handle missing values (NaT) as no overtime
                actual_overtime.append('NaT')

        # Add actualOvertime, totalOverTime, and realTotalOverTime to the employee's data
        employee_dict[employee]['actualOvertime'] = actual_overtime
        employee_dict[employee]['totalOverTime'] = seconds_to_time(total_overtime_seconds)
        employee_dict[employee]['realTotalOverTime'] = seconds_to_time(real_total_overtime_seconds)

    return employee_dict


def dateConversion(employee_dict, month, year):
    # Helper function to get the ordinal suffix for a date
    def ordinal(n):
        return "%d%s" % (n, "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])

    # Dictionary to map weekday abbreviations to full names
    day_map = {
        'M': 'Monday',
        'T': 'Tuesday',
        'W': 'Wednesday',
        'Th': 'Thursday',
        'F': 'Friday',
        'St': 'Saturday',
        'S': 'Sunday'
    }

    # Loop through each employee in the dictionary
    for employee, data in employee_dict.items():
        converted_days = []  # List to hold the converted dates

        # Loop through each day in the Days list
        for day_str in data['Days']:
            day_num, day_abbr = day_str.split()  # Split the day number and abbreviation
            # Create a date object using the provided month and year
            date_obj = datetime.strptime(f"{day_num} {month} {year}", "%d %B %Y")
            # Get the full day name using the day_map
            full_day_name = day_map[day_abbr]
            # Create the final date string in the desired format
            formatted_date = date_obj.strftime(f"%d-%m-%Y")
            # Append the formatted date and day tuple to the list
            converted_days.append(formatted_date)
        # Update the employee's Days list with the converted dates
        employee_dict[employee]['Days'] = converted_days

    return employee_dict


def holidayCalculation(employee_dict, holidays):
    # Convert holiday dates to datetime objects for easier comparison
    holidays = pd.to_datetime(holidays, format="%d-%m-%Y").date

    for employee, data in employee_dict.items():
        days = data['Days']  # List of days
        status = data['Status']  # Status for each day (P, A, ½P, WO, etc.)
        in_times = data['InTime']  # In-time for each day (or NaT if absent)
        out_times = data['OutTime']  # Out-time for each day (or NaT if absent)

        total_present_days = 0  # Initialize count for present days
        total_absent_days = 0  # Initialize count for absent days
        absent_days = [0] * len(days)  # Initialize absent days list
        office_working_days = 0  # Initialize office working days count

        saturday_adjusted = False  # To track if a Saturday absence has been adjusted

        # Loop through each day of the month
        for i, day in enumerate(days):
            # Get day of the week and convert current day to a date object
            day_of_week = pd.to_datetime(day, format="%d-%m-%Y").day_name()
            current_day = pd.to_datetime(day, format="%d-%m-%Y").date()

            # Skip marking as absent if it's a public holiday
            if current_day in holidays:
                absent_days[i] = 0  # Mark holidays as not absent (ignore them)
                continue  # Skip further checks for this day

            # Calculate Total Present Days
            if status[i] in ['P']:  # Present or Half Present status
                if in_times[i] != 'NaT' or out_times[i] != 'NaT':  # Either InTime or OutTime should be available
                    total_present_days += 1  # Count this day as present
            if status[i] in ['½P']:
                if in_times[i] != 'NaT' or out_times[i] != 'NaT':
                    total_present_days += 0.5

            # Calculate Absent Days (skip weekly off days)
            if status[i] == 'WO':  # Weekly off
                absent_days[i] = 0  # Mark weekly offs as not absent (ignore them)
            elif status[i] == 'A' or (in_times[i] == 'NaT' and out_times[i] == 'NaT'):
                absent_days[i] = 1  # Mark day as absent
            else:
                absent_days[i] = 0  # Mark day as not absent

            # Adjust for Saturday Absence
            if absent_days[i] == 1 and day_of_week == 'Saturday' and not saturday_adjusted:
                absent_days[i] = 0  # Ignore one Saturday absence
                saturday_adjusted = True  # Mark that a Saturday absence has been adjusted

        # Calculate Total Absent Days (after adjusting for one Saturday)
        total_absent_days = sum(absent_days)

        # Add calculated values back to employee_dict
        employee_dict[employee]['AbsentDays'] = absent_days
        employee_dict[employee]['TotalAbsentDays'] = total_absent_days
        employee_dict[employee]['TotalPresentDays'] = total_present_days

    return employee_dict


def adjust_wop_hours(employee_dict):
    # Helper function to convert time string (e.g., "10:34") to timedelta
    def convert_to_timedelta(time_str):
        try:
            hours, minutes = map(int, time_str.split(':'))
            return timedelta(hours=hours, minutes=minutes)
        except Exception as e:
            print(f"Error converting time string {time_str}: {e}")
            return timedelta(0)

    # Loop through all employees in the employee_dict
    for employee in employee_dict:
        # Convert totalOverTime to timedelta
        total_overtime = convert_to_timedelta(employee_dict[employee].get('totalOverTime', '0:00'))
        comp_off_sunday = employee_dict[employee].get('comp_off_sunday', 0)  # Get existing comp_off or start at 0

        print(f"Initial totalOverTime for {employee}: {total_overtime}")

        # Adjust overtime by adding WOP hours and updating comp_off
        for i, status in enumerate(employee_dict[employee]['Status']):
            daily_working_hours = convert_to_timedelta(employee_dict[employee]['DailyWorkingHours'][i])

            if status == 'WOP':
                # Add daily working hours to total overtime if WOP
                total_overtime += daily_working_hours

                # Add to comp_off based on working hours
                if daily_working_hours >= timedelta(hours=6):
                    comp_off_sunday += 1  # Full comp off for more than 6 hours
                else:
                    comp_off_sunday += 0.5  # Half comp off for less than 6 hours

                print(f"Added {daily_working_hours} to totalOverTime for {employee}. New total: {total_overtime}")

                # Change the status from WOP to WO
                employee_dict[employee]['Status'][i] = 'WO'

            elif status == 'WO½P':
                # Add daily working hours to total overtime if WO½P
                total_overtime += daily_working_hours

                # Add to comp_off based on working hours
                if daily_working_hours >= timedelta(hours=6):
                    comp_off_sunday += 1  # Full comp off for more than 6 hours
                else:
                    comp_off_sunday += 0.5  # Half comp off for less than 6 hours

                print(f"Added {daily_working_hours} to totalOverTime for {employee}. New total: {total_overtime}")
                # Change the status from WO½P to WO
                employee_dict[employee]['Status'][i] = 'WO'

        # Update totalOverTime in HH:MM format
        total_hours, remainder = divmod(total_overtime.total_seconds(), 3600)
        total_minutes = remainder // 60
        employee_dict[employee]['totalOverTime'] = f"{int(total_hours):02}:{int(total_minutes):02}"
        # Update comp_off key in employee_dict
        employee_dict[employee]['comp_off_sunday'] = comp_off_sunday

    return employee_dict


def compOffCalculation(employee_dict):
    """
    Calculates compensatory off (comp-off) for each employee based on their Saturday attendance.

    Args:
        employee_dict (dict): A dictionary where each key is an employee's name and the value is a
                              dictionary containing their attendance information.

    Returns:
        dict: Updated employee_dict with comp-off days calculated for each employee.
    """
    # Iterate over all employees
    for employee in employee_dict.keys():
        # List to hold all Saturdays in the month
        saturdays = []
        # Iterate over all days in the month
        for i, day in enumerate(employee_dict[employee]['Days']):
            # Assuming day is in 'dd-mm-yyyy' format, adjust as necessary
            day_date = datetime.strptime(day, '%d-%m-%Y')
            if day_date.strftime('%A') == 'Saturday':  # Check if it's a Saturday
                saturdays.append(i)

        # Check if any Saturday has an absence (status 'A')
        has_absent_on_saturday = any(employee_dict[employee]['Status'][i] == 'A' for i in saturdays)

        # Set comp_off based on attendance on Saturdays
        if has_absent_on_saturday:
            employee_dict[employee]['comp_off'] = 0  # Absence found, comp_off remains 0
        else:
            employee_dict[employee]['comp_off'] = 1  # No absence found, set comp_off to 1

    return employee_dict


def total_workingdays_calculation(employee_dict, holidays=[]):
    """
    Calculates the total number of office working days for each employee based on weekends, holidays,
    and other conditions like non-working days.

    Args:
        employee_dict (dict): A dictionary where each key is an employee's name and the value is a
                              dictionary containing their attendance information.
        holidays (list): A list of holidays in the format 'dd-mm-yyyy'.

    Returns:
        dict: Updated employee_dict with total office working days calculated for each employee.
    """
    # Iterate over all employees
    for employee in employee_dict.keys():
        # Initialize totalOfficeWorkingDays if it doesn't exist
        if 'totalOfficeWorkingDays' not in employee_dict[employee]:
            employee_dict[employee]['totalOfficeWorkingDays'] = 0

        # List to store all weekend (WO) days
        weekends = [i for i, status in enumerate(employee_dict[employee]['Status']) if status == 'WO']

        # List to store all holiday indices
        holidays_indices = []
        for i, day in enumerate(employee_dict[employee]['Days']):
            if day in holidays:
                holidays_indices.append(i)

        # Count total days in the month
        total_days_in_month = len(employee_dict[employee]['Days'])

        # Calculate total office working days
        # Subtract weekends (WO), holidays, and subtract 1 (as per your logic)
        total_wo_days = len(weekends)
        total_holiday_days = len(holidays_indices)

        total_office_working_days = total_days_in_month - total_wo_days - total_holiday_days - 1

        # Update employee_dict with the calculated totalOfficeWorkingDays
        employee_dict[employee]['workingDaysAccordingToCal'] = total_office_working_days
        employee_dict[employee]['totalOfficeWorkingDays'] = total_office_working_days

    return employee_dict


def halfDaysCalculation(employee_dict):
    for employee, data in employee_dict.items():
        daily_working_hours = data['DailyWorkingHours']
        status_list = data['Status']  # Assuming the status list is under 'Status'

        # Define half day criteria (7 hours and 30 minutes)
        half_day_limit = pd.to_timedelta('7:30:00')

        # Reset status to 'P' for days that are '½P' or 'P', excluding 'A' and 'WO'
        for idx, status in enumerate(status_list):
            if status in ['½P', 'P']:
                status_list[idx] = 'P'

        # Initialize lists to store half day info
        is_half_day = []
        total_half_day = 0

        # Loop through daily working hours to determine half days
        for idx, working_hours in enumerate(daily_working_hours):
            # Exclude days with status 'WO'
            if status_list[idx] == 'WO':
                is_half_day.append(0)  # Not a half day
                continue

            if working_hours != 'NaT':
                # Ensure the time is in 'hh:mm:ss' format by appending ':00' if necessary
                if len(working_hours) == 5:  # If the time is in 'hh:mm' format
                    working_hours += ':00'

                # Convert string to timedelta
                try:
                    working_duration = pd.to_timedelta(working_hours)
                except ValueError as e:
                    print(f"Error converting time {working_hours}: {e}")
                    is_half_day.append(0)
                    continue

                # Check if working duration is less than half-day limit
                if working_duration < half_day_limit:
                    is_half_day.append(1)
                    total_half_day += 1
                    # Update the status to '½P'
                    status_list[idx] = '½P'
                else:
                    is_half_day.append(0)
            else:
                # If NaT (absent day or weekly off), not a half day
                is_half_day.append(0)

        # Add the new keys to employee data
        employee_dict[employee]['isHalfDay'] = is_half_day
        employee_dict[employee]['totalHalfDay'] = total_half_day
        employee_dict[employee]['Status'] = status_list  # Update the status list in employee data

    return employee_dict


def lateAndEarlyLeaveCalculation(employee_dict):
    for employee, data in employee_dict.items():
        in_times = data['InTime']
        out_times = data['OutTime']
        working_hours = data['DailyWorkingHours']
        is_half_day = data.get('isHalfDay', [])  # Retrieve isHalfDay if available

        # Initialize lists to store late and early leave info
        is_late = []
        early_leave = []
        total_late_punch = 0
        total_early_leave_duration = timedelta(0)  # Initialize as a timedelta object

        # Define shift start times and duration expectations
        shift_start_time = pd.to_datetime('09:30:00', format='%H:%M:%S').time()
        latest_allowed_time = pd.to_datetime('10:00:00', format='%H:%M:%S').time()
        work_duration = pd.to_timedelta('9:00:00')  # 9-hour working day

        # Loop through the in_times and out_times to calculate late coming and early leave
        for i, (in_time, out_time, daily_hours, half_day) in enumerate(
                zip(in_times, out_times, working_hours, is_half_day)):
            # Late coming check
            if in_time != 'NaT':
                in_time_obj = pd.to_datetime(in_time, format='%H:%M').time()
                if in_time_obj > latest_allowed_time:
                    is_late.append(1)
                    total_late_punch += 1
                else:
                    is_late.append(0)
            else:
                is_late.append(0)

            # Early leave check
            if out_time != 'NaT' and in_time != 'NaT' and half_day == 0:
                in_time_obj = pd.to_datetime(in_time, format='%H:%M')
                out_time_obj = pd.to_datetime(out_time, format='%H:%M')

                # Calculate the expected out time (in time + 9 hours)
                expected_out_time = in_time_obj + work_duration

                # Check if the employee left early
                if out_time_obj < expected_out_time:
                    early_duration = expected_out_time - out_time_obj

                    # Format the early leave duration to HH:MM by stripping "days"
                    early_leave_formatted = str(early_duration).split(' ')[-1][:5]  # Extract only HH:MM
                    early_leave.append(early_leave_formatted)
                    total_early_leave_duration += early_duration  # Accumulate early leave time
                else:
                    early_leave.append('00:00')
            else:
                early_leave.append('00:00')  # No early leave if half day or absent

        # Calculate latePunchMinus based on total_late_punch
        latePunchMinus = total_late_punch // 3  # Every 3 late marks count as 1 half-day
        latePunchMinus = round(latePunchMinus / 2, 0)

        # Convert the total_early_leave_duration to HH:MM format
        total_hours, remainder = divmod(total_early_leave_duration.seconds, 3600)
        total_minutes = remainder // 60
        total_early_leave_formatted = f"{total_hours:02}:{total_minutes:02}"

        # Add the new keys to employee data
        employee_dict[employee]['isLate'] = is_late
        employee_dict[employee]['totalLatePunch'] = total_late_punch
        employee_dict[employee]['earlyLeave'] = early_leave
        employee_dict[employee]['totalEarlyLeave'] = total_early_leave_formatted
        employee_dict[employee]['latePunchMinus'] = latePunchMinus  # Add latePunchMinus to employee data

    return employee_dict


def convert_time_to_timedelta(time_str):
    """Convert a time string like '05:09' to a timedelta object."""
    if time_str == 'NaT' or time_str == '00:00':
        return timedelta(0)
    hours, minutes = map(int, time_str.split(':'))
    return timedelta(hours=hours, minutes=minutes)


def finalProcessing(employee_dict):
    # Loop through each employee in the dictionary
    for employee, data in employee_dict.items():
        # 1. Add totalHalfDay/2 to TotalAbsentDays
        if data['TotalAbsentDays'] != 0:
            data['TotalAbsentDays'] = data['TotalAbsentDays'] + (data['totalHalfDay'] / 2) - data['comp_off']
            data['comp_off'] = 0

        if data['TotalAbsentDays'] < 0:
            data['comp_off'] = data['comp_off'] + abs(data['TotalAbsentDays'])
            data['TotalAbsentDays'] = 0

        # 2. Calculate adjustableOverTime = totalOverTime - realTotalOverTime
        total_overtime = convert_time_to_timedelta(data['totalOverTime'])
        real_total_overtime = convert_time_to_timedelta(data['realTotalOverTime'])

        adjustable_overtime = total_overtime - real_total_overtime
        data['adjustableOverTime'] = str(adjustable_overtime)[:-3]  # store in 'HH:MM' format

        if data['TotalPresentDays'] > data['totalOfficeWorkingDays']:
            extra_day = data['TotalPresentDays'] - data['totalOfficeWorkingDays']
            data['comp_off'] = data['comp_off'] + extra_day
            data['TotalPresentDays'] = data['TotalPresentDays'] - extra_day
            
        data['TotalCompOff'] = data['comp_off'] + data['comp_off_sunday']
    return employee_dict


def dict_to_dataframe(employee_dict):
    # Convert the dictionary to a DataFrame
    df = pd.DataFrame.from_dict({
        key: {**value, 'Employee': key} for key, value in employee_dict.items()
    }, orient='index')

    # Reset index to make 'Employee' a column
    df.reset_index(drop=True, inplace=True)

    # Define the desired column order
    column_order = [
        'Employee', 'totalOfficeWorkingDays', 'TotalAbsentDays', 'TotalPresentDays', 'latePunchMinus', 'totalHalfDay',
        'TotalCompOff',
        'totalLatePunch', 'TotalWorkingHours', 'AverageWorkingHours',
        'totalOverTime', 'realTotalOverTime', 'adjustableOverTime', 'totalEarlyLeave',

    ]

    # Reorder the columns
    df = df.reindex(columns=column_order)
    return df


########################

def process_employee_hroneData(file_path):
    # Read the Excel file
    df = pd.read_excel(file_path)

    # Extract the columns with date data (adjust month filtering as needed)
    date_columns = [col for col in df.columns if 'Aug' in col or 'Jul' in col or 'Sep' in col or 'Jan' in col
                    or 'Feb' in col or 'Mar' in col or 'Apr' in col or 'May' in col or 'Jun' in col or 'Oct' in col
                    or 'Nov' in col or 'Dec' in col]

    # Initialize the employee dictionary
    employee_dict = {}

    # Loop through each employee
    for idx, row in df.iterrows():
        employee_name = row['Full name']  # Assuming 'Full name' is the column for employee names
        employee_dict[employee_name] = {"Days": [], "Status": [], "InTime": [], "OutTime": []}

        # Process each date column
        for date in date_columns:
            shift_data = str(row[date])  # Get the shift data for that day

            if '|' in shift_data:
                # Split the shift data by '|' and extract InTime and OutTime
                shift_parts = shift_data.split('|')

                # Handle InTime and OutTime: if '--:--', return NaT
                in_time = shift_parts[2].strip() if len(shift_parts) > 2 and shift_parts[
                    2].strip() != '--:--' else 'NaT'
                out_time = shift_parts[3].strip() if len(shift_parts) > 3 and shift_parts[
                    3].strip() != '--:--' else 'NaT'
            else:
                # If the data is missing or not properly formatted
                in_time, out_time = 'NaT', 'NaT'

            # Append the date, InTime, and OutTime to the employee's dictionary
            employee_dict[employee_name]["Days"].append(date)
            employee_dict[employee_name]["InTime"].append(in_time)
            employee_dict[employee_name]["OutTime"].append(out_time)
            employee_dict[employee_name]["Status"].append('')  # Status remains empty for now

    return employee_dict


from datetime import datetime


def dict_cleaning(employee_dict):
    # Loop through each employee in the dictionary
    for employee, data in employee_dict.items():
        # Extract the list of days and their corresponding statuses
        days = data['Days']
        status = data['Status']

        # Loop through the days to find Sundays and update the status
        for i, day in enumerate(days):
            # Convert the string day to a datetime object
            date_object = pd.to_datetime(day, format="%d %b %Y")
            # Get the day of the week
            day_of_week = date_object.day_name()  # e.g., 'Monday'
            # Format the date to 'DD-MM-YYYY, Day'
            formatted_day = date_object.strftime('%d-%m-%Y') + ', ' + day_of_week

            # Update the Days with the formatted date
            days[i] = formatted_day

            # Check if the day is a Sunday and update the status accordingly
            if day_of_week == 'Sunday':
                status[i] = 'WO'  # Update status to 'WO' for Sundays

        # Update the employee's data with the modified lists
        data['Days'] = days
        data['Status'] = status

    # Return the updated employee dictionary
    return employee_dict


def statusFilling(employee_dict):
    # Iterate over each employee in the dictionary
    for employee, data in employee_dict.items():
        # Get the lists of InTime, OutTime, and Status for the employee
        in_times = data['InTime']
        out_times = data['OutTime']
        status = data['Status']

        # Iterate over each day and fill in the status
        for i in range(len(status)):
            # If the status is already 'WO', skip the day
            if status[i] == 'WO':
                continue

            # Check InTime and OutTime for filling status
            in_time = in_times[i]
            out_time = out_times[i]

            if in_time == 'NaT' and out_time == 'NaT':
                # Absent if both InTime and OutTime are NaT
                status[i] = 'A'
            elif in_time != 'NaT' and out_time != 'NaT':
                # Present if both InTime and OutTime are valid
                status[i] = 'P'
            else:
                # Half-Day if one of them is NaT
                status[i] = 'P'

        # Update the dictionary with the modified status list
        employee_dict[employee]['Status'] = status

    return employee_dict


def minorprocessing(employee_dict):
    for employee, data in employee_dict.items():
        if 'Days' in data:
            # Iterate over the list of dates
            updated_days = []
            for day in data['Days']:
                # Split the string by comma and take only the date part
                date_part = day.split(',')[0].strip()
                updated_days.append(date_part)

            # Update the 'Days' list with the modified dates
            employee_dict[employee]['Days'] = updated_days
    return employee_dict


def merge_dictionaries(employee_dict, employee_dict_hrone):
    # Iterate through each key-value pair in employee_dict_hrone
    for employee, data in employee_dict_hrone.items():
        # Check if the employee key is not already in employee_dict
        if employee not in employee_dict:
            # Add the employee and their data to employee_dict
            employee_dict[employee] = data

    return employee_dict


