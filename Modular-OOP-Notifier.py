import datetime
import gspread
import pandas as pd
import numpy as np
from pushbullet import Pushbullet


class SheetNotice:
    def __init__(self,
                 notice_api_key,  # The PushBullet API Key for the user as a string
                 admin_api_key,  # The PushBullet API Key for the admin as a string
                 gsheet_json_path,  # The location of the JSON file used to access the Google Account
                 gsheet_workbook_name,  # The name of the workbook to be accessed
                 gsheet_worksheet_name,  # The name of the sheet to be used
                 gsheet_target_date_column,  # The letter i.e. 'B' of the column containing the date field
                 start_date,  # The date to start checking for missing dates from
                 date_exceptions_list_strings,  # Dates to exclude in the missing check a list of "YYYY-MM-DD" strings
                 admin_copy_msg=False,  # Set as True to send the Admin a copy of all messages
                 admin_all_copy_mode=False,  # Set as True to send the Admin a copy of all, even non-detections
                 dupe_threshold=2,  # Set the threshold for duplicate date detection. i.e 2 would be 2 or more dupes
                 project_name="Default Project Name"):  # The name of the project to show in push notifications
        self.notice_api_key = notice_api_key
        self.gsheet_json_path = gsheet_json_path
        self.gsheet_workbook_name = gsheet_workbook_name
        self.gsheet_worksheet_name = gsheet_worksheet_name
        self.gsheet_target_date_column = gsheet_target_date_column
        self.start_date = start_date
        self.dupe_threshold = dupe_threshold
        self.project_name = project_name
        self.admin_api_key = admin_api_key
        self.admin_copy_msg = admin_copy_msg
        self.admin_all_copy_mode = admin_all_copy_mode

        # Initialising error message list
        error_msgs = []

        # |||||||||||||||||||||||||||||||||||||||||
        # Getting list of dates in date from gsheet
        # |||||||||||||||||||||||||||||||||||||||||

        try:

            # Connect to JSON for access
            sa = gspread.service_account(filename=gsheet_json_path)
            # Create workbook object
            sh = sa.open(gsheet_workbook_name)
            # Create sheet object
            wks = sh.worksheet(gsheet_worksheet_name)
            # Get column with dates in them for checking. Drops header
            dates_list1 = wks.get('%s:%s' % (gsheet_target_date_column, gsheet_target_date_column))[1:]
            # Drop any cells where the value was blank (they are lists)
            dates_list2 = [x for x in dates_list1 if len(x) > 0]
            # Convert list to datetime objects
            dates_list3 = [datetime.datetime.strptime(x[0], '%m/%d/%Y') for x in dates_list2]
            # Reduce to date objects, safe to object
            self.dates_list = [datetime.date(x.year, x.month, x.day) for x in dates_list3]

        except Exception as e:
            # Add the error to the error list
            error_msgs.append(["GSheet Date Column Pull", getattr(e, 'message', repr(e))])

        # |||||||||||||||||||||||||||||||||||||||||||||||||||
        # Establish current datetime, truncate to date object
        # |||||||||||||||||||||||||||||||||||||||||||||||||||

        try:

            today_datetime = datetime.datetime.now()
            self.today_date = datetime.date(today_datetime.year, today_datetime.month, today_datetime.day)
            self.today_date_string = self.today_date.strftime("%Y-%m-%d")

        except Exception as e:
            # Add the error to the error list
            error_msgs.append(["Get Current Date Time", getattr(e, 'message', repr(e))])

        # ||||||||||||||||||||||||
        # Prepare exceptions list
        # ||||||||||||||||||||||||

        try:

            if len(date_exceptions_list_strings) > 0:
                # Convert list of strings to datetime objects
                date_exceptions_list1 = [datetime.datetime.strptime(x, '%Y-%m-%d') for x in
                                         date_exceptions_list_strings]
                # Convert to date objects, save to class
                self.date_exceptions_list = [x.date() for x in date_exceptions_list1]
                self.exclusions_bool = True
            else:
                self.date_exceptions_list = []
                self.exclusions_bool = False

        except Exception as e:
            # Add the error to the error list
            error_msgs.append(["Prepare Exceptions List", getattr(e, 'message', repr(e))])

        # ||||||||||||||||||||||||||||||||||
        # Prepare list of dates to check for
        # ||||||||||||||||||||||||||||||||||

        try:

            # Generate date range for checking
            needed_dates_datetime = pd.date_range(start_date, self.today_date - datetime.timedelta(days=1))
            self.needed_dates_date_list = [datetime.date(x.year, x.month, x.day) for x in needed_dates_datetime]

        except Exception as e:
            # Add the error to the error list
            error_msgs.append(["Date Range for Checking", getattr(e, 'message', repr(e))])

        # |||||||||||||||||||||||||
        # Define missing dates list
        # |||||||||||||||||||||||||

        try:

            missing_dates_no_exceptions = [x for x in self.needed_dates_date_list if x not in self.date_exceptions_list]
            self.missing_dates = [x for x in missing_dates_no_exceptions if x not in self.dates_list]

        except Exception as e:
            # Add the error to the error list
            error_msgs.append(["Define Missing Dates", getattr(e, 'message', repr(e))])

        # |||||||||||||||||||||||||||
        # Define duplicate dates list
        # |||||||||||||||||||||||||||

        try:

            date_series = pd.Series(self.dates_list)
            date_df1 = date_series.to_frame()
            # Column containing the number 1
            date_df1["Number"] = 1
            date_df2 = date_df1.rename(columns={0: 'Dates'})
            # Pivoting to count occurrences of each date
            counted_dates_df1 = date_df2.pivot_table(values="Number", index="Dates", aggfunc=np.sum)
            # Pulling the date field out of the index
            counted_dates_df2 = counted_dates_df1.reset_index()
            # Subsetting to columns over the set duplicate amount
            counted_dates_df3 = counted_dates_df2.loc[counted_dates_df2["Number"] >= dupe_threshold]
            # Copying to avoid the setting with copy error
            counted_dates_df4 = counted_dates_df3.copy()
            # New column with date formatted as string
            counted_dates_df4["Date as String"] = counted_dates_df4["Dates"].apply(lambda x: x.strftime("%Y-%m-%d"))
            # New column with formatted string showing date and duplicate count
            counted_dates_df4["Dupe Result"] = counted_dates_df4["Date as String"] + " | " + \
                                               "Duplicated " + counted_dates_df4["Number"].astype(str) + " times"
            # Saving that as a list and adding it as an attribute
            dupe_dates_list = counted_dates_df4['Dupe Result'].tolist()
            self.dupe_dates_list = dupe_dates_list

        except Exception as e:
            # Add the error to the error list
            error_msgs.append(["Define duplicate dates", getattr(e, 'message', repr(e))])

        # |||||||||||||||||||||||||||||
        # Building the Notification message
        # |||||||||||||||||||||||||||||

        # Values to determine if a message needs to be sent
        # _________________________________________________

        try:

            # Missing dates detection
            if len(self.missing_dates) > 0:
                self.missing_dates_detected = True
            else:
                self.missing_dates_detected = False

            # Dupe detection
            if len(self.dupe_dates_list) > 0:
                self.dupe_detected = True
            else:
                self.dupe_detected = False

            # Combined to determine if any message needs to made
            if self.missing_dates_detected or self.dupe_detected:
                self.message_exists = True
            else:
                self.message_exists = False

        except Exception as e:
            # Add the error to the error list
            error_msgs.append(["Message send boolean values", getattr(e, 'message', repr(e))])

        # Building individual message content
        # _________________________________________________

        try:

            # Defining the message title
            self.msg_title = self.project_name + " Notice | " + self.today_date_string

            # Building Missing dates message

            formatted_dates = [x.strftime("%Y-%m-%d") for x in self.missing_dates]
            # Multi-line string has to be right up to the left to get correct formatting
            self.missing_dates_msg = ("""Missing data for...
%s

(Date format is Year, Month, Day)

Please enter the data ASAP
before you forget how the 
day went!""" % ("\n".join(formatted_dates)))

            # Building Duplicate Dates Message

            self.dupe_dates_msg = """Duplicate dates detected... 
%s

Please fix this in the data""" % ("\n".join(self.dupe_dates_list))

            # Creating combined message
            # _________________________________________________

            # if we have missing dates and dupes
            if self.missing_dates_detected and self.dupe_detected:
                self.combined_msg = self.missing_dates_msg + "\n\n" + "-Additionally-" + "\n\n" + self.dupe_dates_msg
            # if we only have missing dates
            elif self.missing_dates_detected and not self.dupe_detected:
                self.combined_msg = self.missing_dates_msg
            # if we only have dupe dates
            elif not self.missing_dates_detected and self.dupe_detected:
                self.combined_msg = self.dupe_dates_msg
            # if we have nothing to notify
            else:
                self.combined_msg = "Nothing to notify - Admin Only Message"

        except Exception as e:
            # Add the error to the error list
            error_msgs.append(["Building Message Content", getattr(e, 'message', repr(e))])

        # |||||||||||||||||||||||
        # Error Handling Endpoint
        # |||||||||||||||||||||||

        # Add error messages as attribute
        self.error_msgs = error_msgs
        # Check if any errors occurred
        if len(self.error_msgs) > 0:
            self.error_detected = True
        else:
            self.error_detected = False

        # Building Error Message
        self.error_msg_notice = ("""ADMIN ONLY NOTICE:
            
There were errors running the script...

%s""" % self.error_msgs)

    # ||||||||||||||||||||
    # Sending the messages
    # ||||||||||||||||||||

    def notify(self):
        # Send error messages to admin if they exist
        if self.error_detected:
            # Create PushBullet API Object for admin
            pb_api_admin_obj = Pushbullet(self.admin_api_key)
            # Send the message
            pb_api_admin_obj.push_note(self.msg_title, self.error_msg_notice)
        # If no errors, proceed as usual
        else:
            # Create PushBullet API Object for notice
            pb_api_obj = Pushbullet(self.notice_api_key)

            # Send the message if the message exists
            if self.message_exists:
                pb_api_obj.push_note(self.msg_title, self.combined_msg)
                # If admin copy is on, also send the message to the admin
                if self.admin_copy_msg:
                    # Create PushBullet API Object for admin
                    pb_api_admin_obj = Pushbullet(self.admin_api_key)
                    # Send message
                    pb_api_admin_obj.push_note(self.msg_title + " | ADMIN COPY", self.combined_msg)
            else:
                # If admin all copy is on, send the message even if no detections occurred
                if self.admin_all_copy_mode:
                    # Create PushBullet API Object for admin
                    pb_api_admin_obj = Pushbullet(self.admin_api_key)
                    # Send message
                    pb_api_admin_obj.push_note(self.msg_title + " | ADMIN MESSAGE", self.combined_msg)


# ||||||||||||||||||||||||||||||||||||||||
# Example Object creation and method usage
# ||||||||||||||||||||||||||||||||||||||||

# Create the SheetNotice object
ExampleObject = SheetNotice(
    notice_api_key="api key for the user",
    admin_api_key="api key for the admin",
    gsheet_json_path=r"The file path for the gsheet json file",
    gsheet_workbook_name="Workbook Name",
    gsheet_worksheet_name="Sheet1",
    gsheet_target_date_column="C",
    start_date="2022-02-26",
    date_exceptions_list_strings=["2022-05-12"],
    admin_copy_msg=True,
    admin_all_copy_mode=True,
    dupe_threshold=3,
    project_name="My Example Project")

# Print the attributes of the new object
from pprint import pprint
pprint(vars(ExampleObject))

# Run the notify method to send any required messages
ExampleObject.notify()
