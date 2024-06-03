# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import json
import os
import pbds
from types import SimpleNamespace

tournament = 'nsc2023'

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
    with open(f'data/{tournament}/setup/{phase}pools.txt', 'r') as file:
        poolnames = file.read().splitlines()
        for p in poolnames:
            pools.append(pbds.Pool(p))
    with open(f'data/{tournament}/setup/{phase}assignments.txt', 'r') as file:
        assignments = file.read().splitlines()
        for a in assignments:
            team, pool = a.split('\t')[0], a.split('\t')[1]
            pools[poolnames.index(pool)].teams.append(teams[team])
    return pools


if __name__ == '__main__':
    games = get_games(tournament)
    teams = get_teams(games, 1, 5)
    pools = get_pools(tournament, "prelim", teams)
    output = ""
    for pool in pools:
        if len(pool.teams):
           output += f"{pool.name}\n"
           for status in pool.findStatus:
               output += status
               output += "\n"
        output += "\n"
    print("Done!")
    with open(f'data/{tournament}/output.txt', 'w') as file:
        file.write(output)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
