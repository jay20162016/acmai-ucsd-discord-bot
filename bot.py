import discord
from urllib import request
import json
import re

def get(url):
    url = url[6:] # 'https:[6]//www. etc . etc'
#    url = request.quote(url)
    url = 'https:' + url
#    print('GET:', url)
    return json.loads(request.urlopen(url).read())

def tinyurl(url):
    data = json.dumps({'destination': url, 'domain': { 'fullName': 'rebrand.ly' } }).encode('utf-8')
    req = request.Request('https://api.rebrandly.com/v1/links', data=data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Apikey', 'c28baba3245f47f58e800b7c6f470ff9')
    req.add_header('Workspace', 'f1cd3f60b0d043bbbc6d0ae550e0b375')
    return 'https://rebrand.ly/' + json.loads(request.urlopen(req).read())['slashtag']

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

async def tournaments(message):
    tourneys = get_tourneys()
    tourneys = [dot_sep(t)[1] for t in tourneys]
    embed = ( discord.Embed(title='UCSD ACM AI Competitions').
              add_field(name=f'Tournaments', value='\n'.join(tourneys))
              .set_footer(text='Made by Jason Zeng') )
    await message.channel.send(embed=embed)

async def ranks(message):
    page = 0
    tourney = None
    for chunk in message.content.split():
        tourney = get_tourney(chunk) if get_tourney(chunk) is not None else tourney
        try:
            page = int(chunk)
        except:
            pass
    tourney = get_tourney('') if tourney is None else tourney
    if tourney is None:
        embed = ( discord.Embed(title='UCSD ACM AI Competitions',
                              description='Sorry, I cannot find the tournament you were looking for...')
                              .set_footer(text='Made by Jason Zeng') )
        await message.channel.send(embed=embed)
        return

    dim, tourney = dot_sep(tourney)

    req = get(
f'https://compete.ai.acmucsd.com/api/dimensions/{dim}/tournaments/{tourney}/ranks?limit=10&offset={page*10}')

    #data = [ ''.join([ spaced(req['ranks'][i]['player']['username'], 20),
    #                    spaced(req['ranks'][i]['player']['tournamentID']['name'], 20) ])
    #         for i in range(len(req['ranks'])) ]
    usernames = [ req['ranks'][i]['player']['username'] for i in range(len(req['ranks'])) ]
    botnames = [ req['ranks'][i]['player']['tournamentID']['name'] for i in range(len(req['ranks'])) ]

    scores = [ str(round(req['ranks'][i]['rankState']['rating']['score'], 2))
               for i in range(len(req['ranks'])) ]
#    sigma = [ str(round(req['ranks'][i]['rankState']['rating']['sigma'], 2))
#              for i in range(len(req['ranks'])) ]
#    mu = [ str(round(req['ranks'][i]['rankState']['rating']['mu'], 2))
#           for i in range(len(req['ranks'])) ]

    embed = ( discord.Embed(title='UCSD ACM AI Competition', description='**Leaderboard**').
                   add_field(name=f'User Name', value='\n'.join(usernames)).
                   add_field(name=f'Bot Name', value='\n'.join(botnames)).
                   add_field(name=f'Score', value='\n'.join(scores)).
#                   add_field(name=f'µ', value='\n'.join(mu)).
#                   add_field(name=f'σ', value='\n'.join(sigma))
                   add_field(name=f'Page', value=f'#{page}', inline=False)
              .set_footer(text='Made by Jason Zeng') )

    await message.channel.send(embed=embed)

async def users(message):
    page = 0
    for chunk in message.content.split():
        try:
            page = int(chunk)
        except:
            pass
    users = get_users()[page*10:(page+1)*10]
    embed = ( discord.Embed(title='UCSD ACM AI Competitions').
              add_field(name=f'Users', value='\n'.join(users)).
              add_field(name=f'Page', value=f'#{page}', inline=False)
              .set_footer(text='Made by Jason Zeng') )
    await message.channel.send(embed=embed)

async def user(message):
    user = "Jay_jayjay"
    for chunk in message.content.split():
        user = get_user(chunk) if get_user(chunk) is not None else user

    if user is None:
        embed = ( discord.Embed(title='UCSD ACM AI Competitions',
                              description='Sorry, I cannot find the user you were looking for...')
                              .set_footer(text='Made by Jason Zeng') )
        await message.channel.send(embed=embed)
        return

    for t in get_tourneys():
        dim, _ = dot_sep(t)
        try:
            req = get(f'https://compete.ai.acmucsd.com/api/dimensions/{dim}/users/{user}')
            break
        except:
            pass
    else:
        return

    statistics = req['user']['statistics']

    comps = []
    bnames = []
    scores = []

    for tourney, stat in statistics.items():
        comps.append(tourney)
        bnames.append(stat['player']['tournamentID']['name'])
        scores.append(str(round(stat['rankState']['rating']['score'], 2)))

    embed = ( discord.Embed(title='UCSD ACM AI Competitions', description=f'**Stats for User {user}**').
              add_field(name='Tournament', value='\n'.join(comps)).
              add_field(name='Bot Name', value='\n'.join(bnames)).
              add_field(name='Score', value='\n'.join(scores)) )

    await message.channel.send(embed=embed)

async def match(message):
    for chunk in message.content.split():
        try:
            matchid = chunk
            matches = show_match(matchid)
            assert matches is not None
            break
        except:
            pass
    else:
        embed = ( discord.Embed(title='UCSD ACM AI Competitions',
                              description='Sorry, I cannot find the match you were looking for...')
                              .set_footer(text='Made by Jason Zeng') )
        await message.channel.send(embed=embed)
        return


    matches = zip(*matches)
    matches = ['\n'.join(col) for col in matches]

    mid, *players = matches

    embed = discord.Embed(title='UCSD ACM AI Competitions', description=f'**Match {matchid}**').add_field(
                                                            name='Match ID', value=mid)
    for place, player in enumerate(players):
        embed.add_field(name=f'{place}', value=f'{player}')

    embed.set_footer(text='Made by Jason Zeng')

    await message.channel.send(embed=embed)

async def player_matches(message):
    user = "Jay_jayjay"
    tourney = get_tourney('')
    page = 0
    for chunk in message.content.split():
        tourney = get_tourney(chunk) if get_tourney(chunk) is not None else tourney
        user = get_user(chunk) if get_user(chunk) is not None else user
        try:
            page = int(chunk)
        except:
            pass

    if user is None:
        embed = ( discord.Embed(title='UCSD ACM AI Competitions',
                              description='Sorry, I cannot find the user you were looking for...')
                              .set_footer(text='Made by Jason Zeng') )
        await message.channel.send(embed=embed)
        return

    if tourney is None:
        for t in get_tourneys():
            dim, tourn = dot_sep(t)
            try:
                mids = get(
                    f'https://compete.ai.acmucsd.com/api/dimensions/{dim}/tournaments/{tourn}/players/{user}/match?offset={page*5}&limit=5&order=-1')

                break
            except:
                pass
        else:
            return
    else:
        dim, tourn = dot_sep(tourney)
        mids = get(f'https://compete.ai.acmucsd.com/api/dimensions/{dim}/tournaments/{tourn}/players/{user}/match?offset={page*5}&limit=5&order=-1')

    mids = [ m['id'] for m in mids['matches'] ]
    matches = show_match(mids)
    matches = zip(*matches)
    matches = ['\n'.join(col) for col in matches]

    mid, *players = matches

    embed = discord.Embed(title='UCSD ACM AI Competitions', description=f'**Matches of user {user}**').add_field(
                                                            name='Match ID', value=mid)
    for place, player in enumerate(players):
        embed.add_field(name=f'{place}', value=f'{player}')

    embed.add_field(name=f'Page', value=f'#{page}', inline=False).set_footer(text='Made by Jason Zeng')

    await message.channel.send(embed=embed)

def show_match(matchids):
    if type(matchids) is str:
        matchids = [matchids]

    totcols = []
    for i in matchids:
        for t in get_tourneys():
            dim, tourn = dot_sep(t)
            try:
                req = get(f'https://compete.ai.acmucsd.com/api/dimensions/{dim}/tournaments/{tourn}/match/{i}')['match']

                cols = []
                replay = get(f'https://compete.ai.acmucsd.com/api/dimensions/{dim}/tournaments/{tourn}/match/{i}/replay')
                cols.append(f'[{i}]({tinyurl(replay["url"])})')

                for agent in range(len(req['results']['ranks'])):
                    agentid = req['results']['ranks'][agent]['agentID']
                    name = req['results']['stats'][str(agentid)]['name']
                    try:
                        errorlog = get(f'https://compete.ai.acmucsd.com/api/dimensions/{dim}/tournaments/{tourn}/match/{i}/agents/{agentid}/logs')
                        cols.append(f'[{name}]({tinyurl(errorlog["url"])})')
                    except:
                        cols.append(f'{name}')

                totcols.append(cols)
                break
            except:
                pass
        else:
            return

    return totcols

def dot_sep(tourney):
    dim = tourney.split('.')[0]
    tourney = '.'.join(tourney.split('.')[1:])
    return dim, tourney

def get_tourneys():
    dims = list(get('https://compete.ai.acmucsd.com/api/dimensions')['dimensions'].keys())
    tourneys = []
    for dim in dims:
        tourneys += [ dim + '.' + x for x in get(
                    f'https://compete.ai.acmucsd.com/api/dimensions/{dim}/tournaments'
                    )['tournaments'].keys() ]
    return tourneys

def get_tourney(name):
    tourneys = get_tourneys()
    for tourney in tourneys:
        if name.lower() in tourney.lower():
            return tourney

def get_users():
    tourneys = get_tourneys()
    usernames = []
    for tourney in tourneys:
        dim, tourn = dot_sep(tourney)
        req = get(f'https://compete.ai.acmucsd.com/api/dimensions/{dim}/tournaments/{tourn}/ranks')
        t_usernames = [ req['ranks'][i]['player']['username'] for i in range(len(req['ranks'])) ]
        usernames += t_usernames
    return [*{*usernames}]

def get_user(name):
    users = get_users()
    for user in users:
        if name.lower() in user.lower():
            return user

commands = {
    r'.*(tournament).*': tournaments,
    r'.*(rank|leaderboard).*': ranks,
    r'.*(users|players).*': users,
    r'.*(user|player).*': user,
    r'.*(matche?s).*': player_matches,
    r'.*(match).*': match,
}

@client.event
async def on_message(message):
    if not message.content.startswith('?') or message.author == client.user:  # Don't respond to self
        return

    message.content = message.content.strip('?')

    for k, v in commands.items():
        if re.match(k, message.content):
            await v(message)
            break

with open('.token.txt') as f:
    token = f.read().strip()

client.run(token)
