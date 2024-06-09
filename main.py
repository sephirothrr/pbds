import json
import os
import time

import pbds
import downloader
import slack
import pathlib
from base64 import b64encode as b64e
import protests

from flask import Flask, send_from_directory, redirect, url_for, request
from flask import render_template

urls = {"nsc2023": "https://hdwhite.org/qb/pacensc2023/json/", "nsc2024": "https://hdwhite.org/qb/tournaments/pacensc2024/json/"}

pools = []
app = Flask(__name__)
app.config['DEBUG'] = True
domain = 'https://pbds-39c532296638.herokuapp.com/'


def get_games_from_json(tournament):
    games = []
    for f in os.listdir(f'data/{tournament}/games'):
        if f.endswith('.json'):
            with open(f'data/{tournament}/games/{f}', 'r') as file:
                parsed = f.replace('.json', " ").split("_")
                parsed[1] = parsed[1].replace("-", " ")
                parsed[2] = parsed[2].replace("-", " ")
                data = json.load(file)
                rnd = int(parsed[0])
                print(data.keys())
                try:
                    tuh = max([int(key) for key in data['tutotals'].keys()])
                    team1 = data['team1']['name']
                    team2 = data['team2']['name']
                    team1tuscore = data['team1']['score'] - data['team1']['bonuses']
                    team2tuscore = data['team2']['score'] - data['team2']['bonuses']
                    team1bscore = data['team1']['bonuses']
                    team2bscore = data['team2']['bonuses']
                except KeyError:
                    continue

                games.append(pbds.Game(rnd, tuh, team1, team1tuscore, team1bscore, team2, team2tuscore, team2bscore))
    return games


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

def generate_teams(tournament, phase):
    teams = {}
    with open(f'data/{tournament}/phases/{phase}/assignments.txt', 'r') as file:
        assignments = file.read().splitlines()
        for a in assignments:
            team, bracket = a.split('\t')[0], a.split('\t')[1]
            teams[team] = pbds.Team(team, bracket)
    return teams

def process_game(game, teams):
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
    return teams

def get_teams(games, roundstart, roundend, teams={}):
    for game in games:
        if game.round < roundstart or game.round > roundend:
            continue
        if game.tuh >= 20:
            teams = process_game(game, teams)
    return dict(sorted(teams.items()))


def get_pools(tournament, phase, teams):
    pools = []
    poolnames = []
    with open(f'data/{tournament}/phases/{phase}/pools.txt', 'r') as file:
        poolnames = file.read().splitlines()
        # print(poolnames)
        for p in poolnames:
            pools.append(pbds.Pool(p))
    with open(f'data/{tournament}/phases/{phase}/assignments.txt', 'r') as file:
        assignments = file.read().splitlines()
        # print(poolnames)
        for a in assignments:
            team, pool = a.split('\t')[0], a.split('\t')[1]
            pools[poolnames.index(pool)].teams.append(teams[team])
    return pools


class Phase:
    def __init__(self, name: str):
        self.name = name
        self.carry = []
        self.start = 1
        self.end = 15
        if name == "prelims":
            self.start = 1
            self.end = 5
        elif name == "playoffs":
            self.start = 6
            self.end = 10
        elif name == "superplayoffs":
            self.start = 11
            self.end = 16
            self.carry = [6, 7, 8, 9, 10]


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'images/slack.svg', mimetype='image')


@app.route('/<tournament>/<phase>')
def index(tournament, phase):
    global pools

    phase = Phase(phase)
    all_protests = protests.read_google_sheet()

    # tournament = 'nsc2023'

    statsurl = 'https://hdwhite.org/qb/tournaments/pacensc2024/qbj/'

    loader = downloader.Downloader(urls[tournament], start_round=phase.start, end_round=phase.end)

    filenames = loader.get_filenames_from_url()
    filenames = loader.files_not_updated(filenames, f'data/{tournament}/games')
    loader.downloads(filenames, f'data/{tournament}/games')

    games = get_games_from_json(tournament)

    teams = generate_teams(tournament, phase.name)
    teams = get_teams(games, phase.start, phase.end, teams)
    pools = get_pools(tournament, phase.name, teams)
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
    if len(phase.carry):
        for game in games:
            if game.round in phase.carry and teams[game.team1].bracket == teams[game.team2].bracket:
                teams = process_game(game, teams)

    print("Done!")
    print(f'Recording protests in rounds {phase.start} to {phase.end}')
    for protest in all_protests:
        # print(protest['result'])
        # print(f"Protest in round {protest['round']}")
        if protest['round'] in [str(x) for x in range(phase.start, phase.end + 1)]:
            print(f"Recording protest in round {protest['round']}")
            if protest['result'] != "MOOT" and protest['result'] != "RESOLVED":
                print(f'Recording live protest between {protest["team1"]} and {protest["team2"]}')
                teams[protest['team1']].protest = True
                teams[protest['team2']].protest = True
    with open(f'data/{tournament}/phases/{phase.name}/output.txt', 'w+') as file:
        file.write(output)
    for pool in pools:
        pathlib.Path(f'static/generated/{tournament}/{phase.name}').mkdir(parents=True, exist_ok=True)
        with open(f'static/generated/{tournament}/{phase.name}/{pool.name}.html', 'w+') as file:
            file.write(render_template('pool.html', pool=pool))
    return render_template('index.html', pools=pools, phase=phase, encoder=b64e)


@app.route('/<tournament>/<phase>/<bracket>')
def pool(tournament, phase, bracket):
    return send_from_directory(f'static/generated/{tournament}/{phase}', f'{bracket}.html')


@app.route('/initialize/<tournament>/<phase>')
def initialize(tournament, phase):
    pools = []
    with open(f'data/{tournament}/phases/{phase}/pools.txt', 'r') as file:
        poolnames = file.read().splitlines()
        for p in poolnames:
            pools.append(pbds.Pool(p))
    debug = os.getenv('DEBUG') == "True"

    slackclient = slack.SlackClient('record-confirmation', slack.getToken())

    for pool in pools:
        url = url_for('pool', tournament=tournament, phase=phase, bracket=pool.name, _external=True)
        print(url)
        slackclient.sendBrackets([pool.name])
        time.sleep(1)
        slackclient.sendRecordConfirmation(pool.name, f"Please confirm your bracket's records and protest status at {url}")
        time.sleep(1)
        if debug:
            break
    return redirect(f'/{tournament}/{phase}')


@app.route('/slackify', methods=['POST'])
def slackify():
    jsonData = request.get_json()
    print(jsonData)
    print(jsonData["bracket"])
    slackclient = slack.SlackClient("record-confirmation", slack.getToken())
    slackclient.sendRecordConfirmation(jsonData["bracket"], jsonData["message"])
    return
