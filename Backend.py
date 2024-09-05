import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# Define a function to handle file uploads and processing
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


# Helper function to convert HH:MM format to total minutes
def time_to_minutes(time_str):
    hours, minutes = map(int, time_str.split(':'))
    return hours * 60 + minutes


# Helper function to convert total minutes to HH:MM format
def minutes_to_time(total_minutes):
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f'{int(hours):02}:{int(minutes):02}'


def calculate_daily_durations(employee_dict):
    # Loop through each employee in the dictionary
    for employee, data in employee_dict.items():
        daily_durations = []  # Initialize list to hold daily durations
        total_minutes = 0  # Initialize total working minutes

        # Loop through InTime and OutTime
        for in_time_str, out_time_str in zip(data['InTime'], data['OutTime']):
            if in_time_str != 'NaT' and out_time_str != 'NaT':  # Ensure both times are valid
                # Convert time strings to datetime.time objects
                in_time = datetime.strptime(in_time_str, '%H:%M').time()
                out_time = datetime.strptime(out_time_str, '%H:%M').time()

                # Calculate the duration
                in_datetime = datetime.combine(datetime.today(), in_time)
                out_datetime = datetime.combine(datetime.today(), out_time)

                if out_datetime < in_datetime:
                    out_datetime += timedelta(days=1)  # Handle cases where OutTime is past midnight

                duration = out_datetime - in_datetime
                total_hours = duration.total_seconds() // 3600
                total_minutes_duration = (duration.total_seconds() % 3600) // 60
                # Append the duration in HH:MM format
                duration_str = f'{int(total_hours):02}:{int(total_minutes_duration):02}'
                daily_durations.append(duration_str)

                # Add the duration to total working minutes
                daily_minutes = time_to_minutes(duration_str)
                total_minutes += daily_minutes
            else:
                daily_durations.append('NaT')

        # Add the dailyDuration key to the employee's dictionary
        employee_dict[employee]['dailyDuration'] = daily_durations
        # Calculate and add totalWorkingHours
        total_working_hours = minutes_to_time(total_minutes)
        employee_dict[employee]['totalWorkingHours'] = total_working_hours

        # Calculate and add averageWorkingHours
        valid_days = len([d for d in daily_durations if d != 'NaT'])
        if valid_days > 0:
            average_minutes = total_minutes // valid_days
            employee_dict[employee]['averageWorkingHours'] = minutes_to_time(average_minutes)
        else:
            employee_dict[employee]['averageWorkingHours'] = 'NaT'

    return employee_dict


def Early_over_time_calculation(employee_dict):
    # Helper function to convert HH:MM format to total minutes
    def time_to_minutes(time_str):
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes

    # Helper function to convert total minutes to HH:MM format
    def minutes_to_time(total_minutes):
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f'{int(hours):02}:{int(minutes):02}'

    # Loop through each employee in the dictionary
    for employee, data in employee_dict.items():
        shift_time_data = {'earlyLeave': [], 'overTime': []}  # Initialize shift-related data

        # Loop through InTime and OutTime
        for in_time_str, out_time_str, duration_str in zip(data['InTime'], data['OutTime'], data['dailyDuration']):
            if in_time_str != 'NaT' and out_time_str != 'NaT':  # Ensure both times are valid
                in_time = datetime.strptime(in_time_str, '%H:%M').time()
                out_time = datetime.strptime(out_time_str, '%H:%M').time()

                in_datetime = datetime.combine(datetime.today(), in_time)
                out_datetime = datetime.combine(datetime.today(), out_time)

                if out_datetime < in_datetime:
                    out_datetime += timedelta(days=1)  # Handle cases where OutTime is past midnight

                # Determine dynamic shift end time based on InTime
                if in_time <= datetime.strptime('10:00', '%H:%M').time():
                    # If punched in between 09:30 and 10:00
                    shift_start = max(in_time, datetime.strptime('09:30', '%H:%M').time())
                else:
                    # If punched in after 10:00, shift starts when punched in
                    shift_start = in_time

                # Calculate the dynamic shift end time
                shift_end_datetime = datetime.combine(datetime.today(), shift_start) + timedelta(hours=9)
                shift_end_time = shift_end_datetime.time()

                # Early Leave Calculation based on expected shift end time
                if out_datetime < shift_end_datetime:
                    early_leave_minutes = time_to_minutes(shift_end_time.strftime('%H:%M')) - time_to_minutes(
                        out_time_str)
                    # Check if early leave is more than 4 hours (240 minutes)
                    if early_leave_minutes > 240:
                        shift_time_data['earlyLeave'].append('00:00')  # Considered half-day, so set to 00:00
                    else:
                        shift_time_data['earlyLeave'].append(minutes_to_time(early_leave_minutes))
                else:
                    shift_time_data['earlyLeave'].append('00:00')

                # Overtime Calculation
                shift_minutes = time_to_minutes(shift_end_time.strftime('%H:%M')) - time_to_minutes(in_time_str)
                daily_minutes = time_to_minutes(duration_str)
                if daily_minutes > shift_minutes:
                    overtime_minutes = daily_minutes - shift_minutes
                    shift_time_data['overTime'].append(minutes_to_time(overtime_minutes))
                else:
                    shift_time_data['overTime'].append('00:00')
            else:
                shift_time_data['earlyLeave'].append('NaT')
                shift_time_data['overTime'].append('NaT')

        # Add shiftTime data to the employee's dictionary
        employee_dict[employee]['shiftTime'] = shift_time_data

    return employee_dict


def half_day_calculation(employee_dict):
    # Helper function to convert HH:MM format to total minutes
    def time_to_minutes(time_str):
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes

    # Loop through each employee in the dictionary
    for employee, data in employee_dict.items():
        half_day_count = []  # Initialize list to hold half-day counts

        # Loop through dailyDuration
        for duration_str in data['dailyDuration']:
            if duration_str != 'NaT':  # Ensure the duration is valid
                # Convert duration string to minutes
                daily_minutes = time_to_minutes(duration_str)

                # Check if the working hours are less than 7:30 hours (450 minutes)
                if daily_minutes < 450:
                    half_day_count.append(1)
                else:
                    half_day_count.append(0)
            else:
                half_day_count.append(0)  # NaT is considered as not a half-day

        # Add the halfDayCount key to the employee's dictionary
        employee_dict[employee]['halfDayCount'] = half_day_count

    return employee_dict


def leave_calculation(employee_dict):
    # Loop through each employee in the dictionary
    for employee, data in employee_dict.items():
        absent = []  # Initialize list to hold absence counts
        missed_punch_out = []  # Initialize list to hold missed punch-out counts
        missed_punch_in = []  # Initialize list to hold missed punch-in counts

        # Loop through InTime and OutTime
        for in_time_str, out_time_str in zip(data['InTime'], data['OutTime']):
            if in_time_str == 'NaT' and out_time_str == 'NaT':
                # If both InTime and OutTime are NaT, the employee was absent
                absent.append(1)
                missed_punch_out.append(0)  # No missed punch since they were absent
                missed_punch_in.append(0)  # No missed punch since they were absent
            else:
                absent.append(0)  # The employee was present

                if in_time_str == 'NaT':
                    missed_punch_in.append(1)  # Missing punch-in
                else:
                    missed_punch_in.append(0)

                if out_time_str == 'NaT':
                    missed_punch_out.append(1)  # Missing punch-out
                else:
                    missed_punch_out.append(0)

        # Add the absent, missedPunchOut, and missedPunchIn keys to the employee's dictionary
        employee_dict[employee]['absent'] = absent
        employee_dict[employee]['missedPunchOut'] = missed_punch_out
        employee_dict[employee]['missedPunchIn'] = missed_punch_in

    return employee_dict


def latePunch_calculation(employee_dict):
    # Helper function to convert HH:MM format to total minutes
    def time_to_minutes(time_str):
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes

    # Helper function to convert total minutes to HH:MM format
    def minutes_to_time(total_minutes):
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f'{int(hours):02}:{int(minutes):02}'

    # Loop through each employee in the dictionary
    for employee, data in employee_dict.items():
        late_by = []  # Initialize list to hold late by hours
        late_mark = []  # Initialize list to hold late mark (1 or 0)

        # Loop through InTime
        for in_time_str in data['InTime']:
            if in_time_str != 'NaT':  # Ensure the time is valid
                # Convert time string to datetime.time object
                in_time = datetime.strptime(in_time_str, '%H:%M').time()
                # Calculate the difference if punched in after 10:00
                threshold_time = datetime.strptime('10:00', '%H:%M').time()
                if in_time > threshold_time:
                    late_minutes = time_to_minutes(in_time_str) - time_to_minutes('10:00')
                    late_by.append(minutes_to_time(late_minutes))
                    late_mark.append(1)
                else:
                    late_by.append('00:00')
                    late_mark.append(0)
            else:
                late_by.append('NaT')
                late_mark.append('NaT')

        # Add lateBy and lateMark to the employee's dictionary
        employee_dict[employee]['lateBy'] = late_by
        employee_dict[employee]['lateMark'] = late_mark

    return employee_dict


from datetime import datetime


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

from datetime import datetime


def finalCalculations_processing(employee_dict, holidays=None):
    # If holidays are not provided or empty, set an empty list
    if not holidays:
        holidays = []

    # Convert holidays to datetime objects for comparison if there are any holidays
    holidays = [datetime.strptime(date, '%d-%m-%Y').strftime('%d-%m-%Y') for date in holidays]

    for employee, data in employee_dict.items():
        days = data['Days']
        status = data['Status']
        missed_punch_out = data['missedPunchOut']
        missed_punch_in = data['missedPunchIn']
        late_marks = data['lateMark']
        half_day_count = data['halfDayCount']
        absent = data['absent']
        early_leave = data['shiftTime']['earlyLeave']
        overtime = data['shiftTime']['overTime']
        totalWorkingHours = data['totalWorkingHours']
        averageWorking = data['averageWorkingHours']

        # Initialize totals
        total_missed_punch_out = 0
        total_missed_punch_in = 0
        total_late_marks = 0
        total_half_days = 0
        total_absent = 0
        total_early_leave = 0
        total_overtime = 0

        filtered_days = []

        for i, day in enumerate(days):
            # Check if the day is Sunday or a holiday
            if status[i] == 'WO' or day in holidays:
                continue

            # Calculate totals
            total_missed_punch_out += missed_punch_out[i]
            total_missed_punch_in += missed_punch_in[i]
            total_late_marks += int(late_marks[i]) if late_marks[i] != 'NaT' else 0
            total_half_days += half_day_count[i]
            total_absent += absent[i]
            if early_leave[i] != 'NaT':
                total_early_leave += int(early_leave[i].split(':')[0]) * 60 + int(early_leave[i].split(':')[1])
            if overtime[i] != 'NaT':
                total_overtime += int(overtime[i].split(':')[0]) * 60 + int(overtime[i].split(':')[1])

            # Keep the day if it's not a Sunday or holiday
            filtered_days.append(day)

        # Convert total minutes into HH:MM format
        early_leave_hours = total_early_leave // 60
        early_leave_minutes = total_early_leave % 60
        total_early_leave_formatted = f"{early_leave_hours:02}:{early_leave_minutes:02}"

        overtime_hours = total_overtime // 60
        overtime_minutes = total_overtime % 60
        total_overtime_formatted = f"{overtime_hours:02}:{overtime_minutes:02}"

        # Store the totals in the employee's report dictionary
        employee_dict[employee]['report_dict'] = {
            'totalWorkingHours': totalWorkingHours,
            'averageDailyWorking': averageWorking,
            'totalAbsent': total_absent - 1,
            'totalHalfDay': total_half_days,
            'totalLatePunch': total_late_marks,
            'totalMissedPunchOut': total_missed_punch_out,
            'totalMissedPunchIn': total_missed_punch_in,
            'totalOverTime': total_overtime_formatted,
            'totalEarlyLeave': total_early_leave_formatted,
        }
        # Update the Days to only include working days (non-Sunday, non-holiday)
        employee_dict[employee]['Days'] = filtered_days
    return employee_dict


def present_calculator(employee_dict, holidays=None):
    # If holidays are not provided or empty, set an empty list
    if not holidays:
        holidays = []

    # Convert holidays to datetime objects for comparison if any are provided
    holidays = [datetime.strptime(holiday, '%d-%m-%Y') for holiday in holidays]

    # Loop through each employee in the dictionary
    for employee, data in employee_dict.items():
        days = data['Days']
        statuses = data['Status']
        absent = data['report_dict']['totalAbsent']
        halfday = data['report_dict']['totalHalfDay'] / 2
        latepunch = data['report_dict']['totalLatePunch']

        # Calculate latepunch adjustment if latepunch is 3 or more
        if latepunch >= 3:
            if latepunch % 3 == 0:
                latepunch = latepunch / 3
            else:
                if latepunch % 2 == 0:
                    for i in range(1, latepunch):
                        if (latepunch - i) % 3 == 0:
                            latepunch = (latepunch - i) / 3
                            break
                else:
                    for i in range(1, latepunch):
                        if (latepunch - i) % 3 == 0:
                            latepunch = (latepunch - i) / 3
                            break

            # After the division by 3, divide the result by 2
            latepunch = latepunch / 2
        else:
            latepunch = 0  # Set latepunch to 0 if it's less than 3

        # Calculate total working days
        total_working_days = 0
        for day, status in zip(days, statuses):
            day_date = datetime.strptime(day, '%d-%m-%Y')
            # Check if the day is not a Sunday (weekday 6) and not a holiday
            if day_date.weekday() != 6 and day_date not in holidays:
                total_working_days += 1

        total_working_days = total_working_days - 1  # Subtracting 1 based on your logic

        # Calculate total present days
        total_present_days = total_working_days - (absent + halfday)

        # Update the report_dict
        if 'report_dict' not in data:
            employee_dict[employee]['report_dict'] = {}

        employee_dict[employee]['report_dict']['totalWorkingDays'] = total_working_days
        employee_dict[employee]['report_dict']['totalPresentDays'] = total_present_days
        employee_dict[employee]['report_dict']['totalMinusBeauseLateDays'] = latepunch

    return employee_dict

def report_dataframe_creator(employee_dict):
    # Initialize an empty list to store the data for the DataFrame
    report_data = []

    # Iterate over each employee in the dictionary
    for employee, details in employee_dict.items():
        # Extract the report_dict for the current employee
        report_dict = details.get('report_dict', {})

        # Add the employee's name to the report_dict
        report_dict['Employee Name'] = employee

        # Append the report_dict as a row to the report_data list
        report_data.append(report_dict)

    # Convert the list of dictionaries into a DataFrame
    monthlyReportDataframe = pd.DataFrame(report_data)

    # Set the 'Employee Name' column as the index
    monthlyReportDataframe.set_index('Employee Name', inplace=True)

    return monthlyReportDataframe


def actual_overtime_calculation(employee_dict):
    for employee, data in employee_dict.items():
        overtimes = data['shiftTime']['overTime']
        actual_overtime = timedelta(0)  # Initialize total actual overtime

        for overtime in overtimes:
            if overtime != 'NaT':
                overtime_duration = datetime.strptime(overtime, '%H:%M') - datetime(1900, 1, 1)
                if overtime_duration > timedelta(hours=1):  # Consider only overtime more than 1 hour
                    actual_overtime += overtime_duration

        # Convert total actual overtime back to 'HH:MM' format and store in the dictionary
        total_actual_overtime = (datetime(1900, 1, 1) + actual_overtime).strftime('%H:%M')
        data['report_dict']['actualOverTime'] = total_actual_overtime

    return employee_dict


def time_str_to_timedelta(time_str):
    if time_str == 'NaT':
        return timedelta(0)
    hours, minutes = map(int, time_str.split(':'))
    return timedelta(hours=hours, minutes=minutes)


def timedelta_to_str(td):
    total_minutes = td.total_seconds() // 60
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    return f'{hours:02}:{minutes:02}'


def adjustment(employee_dict):
    for employee, data in employee_dict.items():
        daily_durations = data['dailyDuration']
        total_early_leave = time_str_to_timedelta(data['report_dict']['totalEarlyLeave'])

        # Calculate total time for durations less than 5 hours (half-day)
        total_under_5hrs = timedelta(0)

        for duration, half_day in zip(daily_durations, data['halfDayCount']):
            daily_duration_td = time_str_to_timedelta(duration)

            # If duration is less than 5 hours, consider it a half-day
            if half_day == 1:
                total_under_5hrs += daily_duration_td

        # Subtract the total time for half-days from the total early leave
        updated_total_early_leave = total_early_leave - total_under_5hrs

        # Update the report_dict in employee_dict
        data['report_dict']['totalEarlyLeave'] = timedelta_to_str(updated_total_early_leave)

    return employee_dict


def calculation_adjustments(df):
    # Helper function to convert HH:MM format to total minutes
    def time_to_minutes(time_str):
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes

    # Helper function to convert total minutes to HH:MM format
    def minutes_to_time(total_minutes):
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f'{int(hours):02}:{int(minutes):02}'

    # Convert totalOverTime and totalEarlyLeave to total minutes
    df['totalOverTimeMinutes'] = df['totalOverTime'].apply(lambda x: time_to_minutes(x) if pd.notnull(x) else 0)
    df['totalEarlyLeaveMinutes'] = df['totalEarlyLeave'].apply(lambda x: time_to_minutes(x) if pd.notnull(x) else 0)

    # Calculate adjustedOverTime in minutes (totalOverTime - totalEarlyLeave)
    df['adjustOverTimeMinutes'] = df['totalOverTimeMinutes'] - df['totalEarlyLeaveMinutes']

    # Convert adjustedOverTime back to HH:MM format
    df['adjustOverTime'] = df['adjustOverTimeMinutes'].apply(lambda x: minutes_to_time(x) if x >= 0 else '00:00')

    # Drop the intermediate minute columns (optional)
    df = df.drop(columns=['totalOverTimeMinutes', 'totalEarlyLeaveMinutes', 'adjustOverTimeMinutes'])

    # Rearrange columns in the specified order
    column_order = [
        'totalWorkingDays',
        'totalPresentDays',
        'totalWorkingHours',
        'averageDailyWorking',
        'totalAbsent',
        'totalHalfDay',
        'totalLatePunch',
        'totalMissedPunchOut',
        'totalMissedPunchIn',
        'totalEarlyLeave',
        'totalOverTime',
        'actualOverTime',
        'adjustOverTime',
        'totalMinusBeauseLateDays'
    ]

    # Reorder the DataFrame columns
    df = df[column_order]

    return df
