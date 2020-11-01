import discord
from urllib import request
import json
import re

def get(url):
    return json.loads(request.urlopen(url).read())

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

async def tournaments(message):
    tourneys = get_tourneys()
    tourneys = [".".join(t.split(".")[1:] ) for t in tourneys]
    embed = ( discord.Embed(title='UCSD ACM AI Competitions').
              add_field(name=f'Tournaments', value='\n'.join(tourneys))
              .set_footer(text="Made by Jason Zeng") )
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
    if tourney is None:
        embed = ( discord.Embed(title='UCSD ACM AI Competitions', 
                              description='Sorry, I cannot find the tournament you were looking for...')
                              .set_footer(text='Made by Jason Zeng') )
        await message.channel.send(embed=embed)
        return

    dim = tourney.split('.')[0]
    tourney = '.'.join(tourney.split('.')[1:])

    req = get(
f"https://compete.ai.acmucsd.com/api/dimensions/{dim}/tournaments/{tourney}/ranks?limit=10&offset={page*10}")

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

    embed = ( discord.Embed(title='UCSD ACM AI Competition', description="**Leaderboard**").
                   add_field(name=f'User Names', value="\n".join(usernames)).
                   add_field(name=f'Bot Names', value="\n".join(botnames)).
                   add_field(name=f'Score', value="\n".join(scores)).
#                   add_field(name=f'µ', value="\n".join(mu)).
#                   add_field(name=f'σ', value="\n".join(sigma))
                   add_field(name=f'Page', value=f'#{page}', inline=False)
              .set_footer(text="Made by Jason Zeng") )

    await message.channel.send(embed=embed)


def get_tourneys():
    dims = list(get('https://compete.ai.acmucsd.com/api/dimensions')['dimensions'].keys())
    tourneys = []
    for dim in dims:
        tourneys += [ dim + "." + x for x in get(
                    f'https://compete.ai.acmucsd.com/api/dimensions/{dim}/tournaments'
                    )['tournaments'].keys() ]
    return tourneys

def get_tourney(name):
    tourneys = get_tourneys()
    for tourney in tourneys:
        if name in tourney:
            return tourney

commands = {
    r'.*tournament.*': tournaments,
    r'.*(rank|leaderboard).*': ranks,
}

@client.event
async def on_message(message):
    if not message.content.startswith("?") or message.author == client.user:  # Don't respond to self
        return

    for k, v in commands.items():
        if re.match(k, message.content):
            await v(message)

with open(".token.txt") as f:
    token = f.read().strip()

client.run(token)
