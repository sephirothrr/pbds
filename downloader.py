from urllib.parse import urlparse
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
import os
import datetime
import time


class FileData():
    def __init__(self, filename, timestamp):
        self.filename = filename
        self.timestamp = timestamp

    def __eq__(self, other):
        return self.filename == other.filename and self.timestamp == other.timestamp

class Downloader():
    def __init__(self, url='https://hdwhite.org/qb/pacensc2023/qbj/', start_round=1, end_round=5):
        self.url = url
        self.start_round = start_round
        self.end_round = end_round


    def get_filenames_from_url(self):
        print(f"Parsing files from {self.url}")
        start = time.time()
        # Send a GET request to the URL
        response = requests.get(self.url)
        response.raise_for_status()  # Check if the request was successful

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # get each row
        rows = soup.find_all('tr')

        filedata = []
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 3:
                continue
            raw_link = cells[1].find('a')
            if raw_link:
                href = raw_link.get('href')
                if href:
                    # Construct the full URL
                    full_url = urljoin(self.url, href)
                    # Extract the file name from the URL
                    filename = full_url.split('/')[-1]
                    # Filter out any irrelevant links (e.g., directories or navigation links)
                    if '.' in filename:
                        timestamp_raw = row.find_all('td')[2].text
                        timestamp = datetime.datetime.strptime(str.rstrip(timestamp_raw), '%Y-%m-%d %H:%M')
                        filedata.append(FileData(filename, timestamp))

        print(f"Parsed {len(filedata)} files in {time.time() - start} seconds")
        return filedata

    def download_file_from_url(self, filename, download_location):
        # Ensure the download location exists
        os.makedirs(download_location, exist_ok=True)

        # Construct the full URL
        full_url = urljoin(self.url, filename)

        # Define the local path where the file will be saved
        local_path = os.path.join(download_location, filename)

        # Send a GET request to the URL
        with requests.get(full_url, stream=True) as response:
            response.raise_for_status()  # Check if the request was successful
            # Open a local file with the same name as the downloaded file
            with open(local_path, 'wb') as file:
                # Write the content of the response to the local file
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

    def files_not_updated(self, file_list, directory):
        print(f"Checking for updated files in {directory}")
        start = time.time()
        if not os.path.exists(directory):
            # Create the directory and all intermediate directories
            os.makedirs(directory)

        # Get the set of files already in the directory
        existing_files = os.listdir(directory)

        # get the modified time of existing files
        existing_file_data = []
        for file in existing_files:
            existing_file_data.append(FileData(file, datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(directory, file)))))

        # Find files in file_list that are not in the existing_files or have been updated since the last download
        missing_files = []
        for file in file_list:
            if file.filename not in existing_files:
                missing_files.append(file)
            elif file.timestamp > existing_file_data[existing_files.index(file.filename)].timestamp:
                missing_files.append(file)

        ret_files = []
        for file in missing_files:
            rn = int(file.filename.split('_')[0])

            if self.start_round <= rn <= self.end_round:
                ret_files.append(file)

        print(f"Found {len(ret_files)} updated files in {time.time() - start} seconds")
        return ret_files


    def downloads(self, filenames: list[FileData], download_location):
        print(f"Downloading {len(filenames)} files to {download_location}")
        start = time.time()
        for file in filenames:
            self.download_file_from_url(file.filename, download_location)
        print(f"Downloaded {len(filenames)} files in {time.time() - start} seconds")

#
# loader = Downloader()
#
# filenames = loader.get_filenames_from_url()
#
# filenames = loader.files_not_updated(filenames, 'data/nsc2023/games')