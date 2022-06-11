import gspread
import os
import datetime
import pandas
from pushbullet import Pushbullet

# Wrapping everything in a try-except clause, so I get a notification if something goes wrong
try:
    # Function to pull text from the first line of a text file
    def get_text(path):
        f = open(path, "r")
        lines = f.readlines()
        key = lines[0]
        f.close()
        return key

    # Link to tracker google form
    tracker_url = get_text("Tracker URL.txt")

    # Establish relative path of script file
    script_path = os.path.dirname(__file__)
    json_filename = 'gsheetnotifier-3f717654c88d.json'
    json_fullpath = os.path.join(script_path, json_filename)

    # Declare pushbullet api key variables
    API_KEY_KYLE = get_text("Pushbullet_API_KEY_KYLE.txt")
    API_KEY_OLIVIA = get_text("Pushbullet_API_KEY_OLIVIA.txt")

    # Create Pushbullet API objects
    pb_kyle = Pushbullet(API_KEY_KYLE)
    pb_olivia = Pushbullet(API_KEY_OLIVIA)

    # Connect to JSON for access
    sa = gspread.service_account(filename=json_fullpath)

    # Create workbook object
    sh = sa.open("Everything Tracker (Responses)")

    # Create sheet object
    wks = sh.worksheet("Form Responses 1")

    # Get B & C columns
    entry_data1 = wks.get('B:C')

    # Drop header row
    entry_data2 = entry_data1[1:]

    # Convert [1] to datetime objects
    entry_data3 = [[x[0], datetime.datetime.strptime(x[1], '%m/%d/%Y')] for x in entry_data2]

    # Reduce to date objects
    entry_data4 = [[x[0], datetime.date(x[1].year, x[1].month, x[1].day)] for x in entry_data3]

    # Split lists per person, remove names
    kyle_list = [x[1] for x in entry_data4 if x[0] == 'Kyle Ross']
    olivia_list = [x[1] for x in entry_data4 if x[0] == 'Olivia Hartley']

    # Establish current datetime, truncate to date object
    today_datetime = datetime.datetime.now()
    today_date = datetime.date(today_datetime.year, today_datetime.month, today_datetime.day)
    today_date_string = today_date.strftime("%Y-%m-%d")

    # Function to return first entry date for a list [Name,Date]


    def first_date(x):
        just_dates = [x[1] for x in x]
        return min(just_dates)


    # Generate date range for checking
    needed_dates_datetime = pandas.date_range('2022-02-26', today_date - datetime.timedelta(days=1))
    needed_dates_date = [datetime.date(x.year, x.month, x.day) for x in needed_dates_datetime]

    # Set list of exceptions
    kyle_exceptions = [datetime.date(2022, 5, 12)]
    olivia_exceptions = [datetime.date(2022, 5, 10)]

    # Function to get list of missing dates for a person, re-formats to strings
    # 20-05-2022: Now with the ability to add date exceptions per person!

    def missing_dates(my_list):
        missing_dates_no_exceptions = [x for x in needed_dates_date if x not in my_list]
        missing_dates_kyle_excepted = [x for x in missing_dates_no_exceptions if x not in kyle_exceptions]
        missing_dates_olivia_excepted = [x for x in missing_dates_no_exceptions if x not in olivia_exceptions]
        return missing_dates_no_exceptions, missing_dates_kyle_excepted, missing_dates_olivia_excepted

    # Check if there are any duplicate dates in a given list

    def dupe_checker(target_list, person):
        dupes_list = []

        for x in target_list:
            count_var = target_list.count(x)
            if count_var != 1:
                dupes_list.append([x, count_var])

        if len(dupes_list) != 0:
            dupes_text = [(("%s duplicates for %s") % (x[1], x[0])) for x in dupes_list]
            dupes_text_set = set(dupes_text)
            return ("""Duplicate dates detected for %s... 
    %s
    
    Please fix this in the data""" % (person, "\n".join(dupes_text_set)))

        else:
            return "No Send"

    # Function to write message for a person

    def message_write(target_list):
        formatted_dates = [x.strftime("%Y-%m-%d") for x in target_list]
        return ("""Missing data for...
    %s
    
    (Date format is Year, Month, Day)
    
    Please enter the data ASAP
    before you forget how the 
    day went!
    
    %s""" % ("\n".join(formatted_dates), tracker_url))

    # Function to send push notification if missing dates exist

    def send_push(target_list, person_name):
        title = "%s Tracker Notice - %s" % (today_date_string, person_name)
        (missing_dates_no_exceptions, missing_dates_kyle_excepted, missing_dates_olivia_excepted) = missing_dates(
            target_list)
        if person_name == "Kyle":
            if len(missing_dates_kyle_excepted) > 0:
                pb_kyle.push_note(title, message_write(missing_dates_kyle_excepted))
        if person_name == "Olivia":
            if len(missing_dates_olivia_excepted) > 0:
                pb_olivia.push_note(title, message_write(missing_dates_olivia_excepted))


    # Check if any dates have been missed since testing start
    # If yes, send a push notification to that person's phone
    send_push(kyle_list, "Kyle")
    send_push(olivia_list, "Olivia")

    # Send seperate push notifications to Kyle if duplicates are found in either list
    dupe_check_title = "Tracker Notice - Duplicate Dates"

    kyle_dupe_result = dupe_checker(kyle_list, "Kyle")
    olivia_dupe_result = dupe_checker(olivia_list, "Olivia")

    if kyle_dupe_result != "No Send":
        pb_kyle.push_note(dupe_check_title, kyle_dupe_result)
    if olivia_dupe_result != "No Send":
        pb_kyle.push_note(dupe_check_title, olivia_dupe_result)

except Exception as e:
    # Sends a push message containing the error if something goes wrong
    pb_kyle.push_note("Tracker Script Error", getattr(e, 'message', repr(e)))
