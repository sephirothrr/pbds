import json
import os
import pbds
import requests

from flask import Flask
from flask import render_template

from urllib.parse import urlparse
from urllib.parse import urljoin
from bs4 import BeautifulSoup

app = Flask(__name__)

tournament = 'nsc2023'
url = 'https://hdwhite.org/qb/pacensc2023/qbj/'
start_round = 1
end_round = 5

teams = {}
pools = []
games = []


def get_games(tournament):
    games = []
    for f in os.listdir(f'data/{tournament}/games'):
        if f.endswith('.json'):
            with open(f'data/{tournament}/games/{f}', 'r') as file:
                parsed = f.replace('.json', " ").split("_")
                parsed[1] = parsed[1].replace("-", " ")
                parsed[2] = parsed[2].replace("-", " ")
                data = json.load(file)
                rnd = int(parsed[0])
                tuh = data['tossups_read']
                team1 = data['match_teams'][0]['team']['name']
                team1tuscore = 0
                team2tuscore = 0
                team1bscore = data['match_teams'][0]['bonus_points']
                team2bscore = data['match_teams'][1]['bonus_points']

                for player in data['match_teams'][0]['match_players']:
                    buzzes = player['answer_counts']
                    if len(buzzes):
                        for buzz in buzzes:
                            team1tuscore += (buzz['answer']['value'] * buzz['number'])

                for player in data['match_teams'][1]['match_players']:
                    buzzes = player['answer_counts']
                    if len(buzzes):
                        for buzz in buzzes:
                            team2tuscore += (buzz['answer']['value'] * buzz['number'])

                team2 = data['match_teams'][1]['team']['name']
                games.append(pbds.Game(rnd, tuh, team1, team1tuscore, team1bscore, team2, team2tuscore, team2bscore))
    return games


def get_teams(games, roundstart, roundend):
    teams = {}
    for game in games:
        if game.round < roundstart or game.round > roundend:
            continue
        if game.team1 not in teams:
            teams[game.team1] = pbds.Team(game.team1)
        if game.team2 not in teams:
            teams[game.team2] = pbds.Team(game.team2)
        teams[game.team1].games += 1
        teams[game.team2].games += 1
        teams[game.team1].tuh += game.tuh
        teams[game.team2].tuh += game.tuh
        teams[game.team1].tupoints += game.team1tuscore
        teams[game.team1].bpoints += game.team1bscore
        teams[game.team2].tupoints += game.team2tuscore
        teams[game.team2].bpoints += game.team2bscore
        if game.team1score > game.team2score:
            teams[game.team1].wins += 1
            teams[game.team2].losses += 1
        elif game.team1score < game.team2score:
            teams[game.team2].wins += 1
            teams[game.team1].losses += 1
    return dict(sorted(teams.items()))


def get_pools(tournament, phase, teams):
    pools = []
    with open(f'data/{tournament}/phases/{phase}/pools.txt', 'r') as file:
        poolnames = file.read().splitlines()
        for p in poolnames:
            pools.append(pbds.Pool(p))
    with open(f'data/{tournament}/phases/{phase}/assignments.txt', 'r') as file:
        assignments = file.read().splitlines()
        for a in assignments:
            team, pool = a.split('\t')[0], a.split('\t')[1]
            pools[poolnames.index(pool)].teams.append(teams[team])
    return pools

def get_filenames_from_url():
    # Send a GET request to the URL
    response = requests.get(url)
    response.raise_for_status()  # Check if the request was successful

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all the links in the HTML
    links = soup.find_all('a')

    filenames = []
    for link in links:
        href = link.get('href')
        if href:
            # Construct the full URL
            full_url = urljoin(url, href)
            # Extract the file name from the URL
            filename = full_url.split('/')[-1]
            # Filter out any irrelevant links (e.g., directories or navigation links)
            if '.' in filename:
                filenames.append(filename)
    
    return filenames

def files_not_in_location(file_list, directory):

    if not os.path.exists(directory):
        # Create the directory and all intermediate directories
        os.makedirs(directory)

    # Get the set of files already in the directory
    existing_files = set(os.listdir(directory))
    
    # Find files in file_list that are not in the existing_files
    missing_files = [file for file in file_list if file not in existing_files]

    ret_files = []
    for file in missing_files:
        rn = int(file.split('_')[0])
        
        if start_round <= rn <= end_round:
            ret_files.append(file)
    
    return ret_files


def download_file_from_url(filename, download_location):
    # Ensure the download location exists
    os.makedirs(download_location, exist_ok=True)

    # Construct the full URL
    full_url = urljoin(url, filename)

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

def downloads(filenames, download_location):
    for file in filenames:
        download_file_from_url(file, download_location)

@app.route('/')
def index():
    phase = "prelim"

    filenames = get_filenames_from_url()
    filenames = files_not_in_location(filenames, f'data/{tournament}/games')
    downloads(filenames, f'data/{tournament}/games')
    
    games = get_games(tournament)
    teams = get_teams(games, 1, 5)
    pools = get_pools(tournament, phase, teams)
    output = ""
    for pool in pools:
        if len(pool.teams):
            output += f"{pool.name}\n"
            for status in pool.findStatus:
                output += status
                output += "\n"
        else:
            pools.remove(pool)
        output += "\n"
    print("Done!")
    with open(f'data/{tournament}/phases/{phase}/output.txt', 'w+') as file:
        file.write(output)
    return render_template('index.html', pools=pools)
