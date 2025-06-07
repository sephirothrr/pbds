import gspread
from oauth2client.service_account import ServiceAccountCredentials
import enum


class ProtestStatus(enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    MOOT = "MOOT"
    RESOLVED = "RESOLVED"


def read_google_sheet():
    spreadsheet_id = '1wNSMgGhnMjeJw05fe327u2XqFtPL6MsOXxqNkjVod8c'
    sheet_name = 'Form Responses 1'
    credentials_json_path = 'google-credentials.json'

    # Define the scope
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # Add credentials to the account
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_json_path, scope)

    # Authorize the clientsheet
    client = gspread.authorize(creds)

    # Get the instance of the Spreadsheet
    sheet = client.open_by_key(spreadsheet_id)

    # Get the first sheet of the Spreadsheet
    worksheet = sheet.worksheet(sheet_name)
    rowCount = worksheet.row_count
    protests = []

    start_row = 1
    end_row = 200
    start_column = 1
    end_column = 20

    r1c1_start = f'R{start_row}C{start_column}'
    r1c1_end = f'R{end_row}C{end_column}'
    r1c1_range = f'{r1c1_start}:{r1c1_end}'

    values_range = worksheet.get(r1c1_range)

    protests = []

    for row in range(1, len(values_range)):

        result = ''

        # print(len(values_range[row]))
        if len(values_range[row]) <= 19:
            result = ProtestStatus.PENDING.value
        else:
            result = ProtestStatus(values_range[row][19]).value

        if len(values_range[row]) >= 6:
            protest = {
                'team1': values_range[row][4],
                'team2': values_range[row][5],
                'result': result,
                'round': str(values_range[row][3].lower().split(' ')[-1])
            }
            # print(protest)

            protests.append(protest)

    return protests


# Example usage
# data = read_google_sheet()
# print(data)
