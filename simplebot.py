#!/usr/bin/env python

import sys
import socket
import string
import re
import urllib2
import json
import datetime, time
from datetime import datetime, timedelta
from xml.dom.minidom import *
import os.path

CONFIG = 'config.py'

if os.path.isfile(CONFIG):
	execfile(CONFIG)
else:
	sys.exit('ERROR: Unable to open config file')


#--------------------------------------------------------------------------------
def PRIVMSG(msg):
	"""
	Send message to channel.
	"""
	reply = "PRIVMSG %s :%s\r\n" %(CHANNEL, msg)
	s.send(reply)
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
def JOIN(chan):
	"""
	Join to channel.
	"""
	reply = "JOIN %s\r\n" %chan
	print reply
	s.send(reply)
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
def PONG(msg):
	"""
	Reply to server's ping request.
	"""
	reply = "PONG %s\r\n" %msg
	print reply
	s.send(reply)
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
def Auth(nick, passwd, ident, host, realname):
	"""
	Authorization in Twitch IRC.
	"""
	s.send("PASS %s\r\n" %passwd)
	s.send("NICK %s\r\n" %nick)
	s.send("USER %s %s bla :%s\r\n" %(ident, host, realname))
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
def readwords():
	"""
	Reading words fro file to array.
	"""
	import csv
	for word, msg in csv.reader(open(wordfile)):
		wordlist[word] = msg
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
def savewords():
	"""
	Function to write base file.
	"""
	import csv
	stringfile = csv.writer(open(wordfile, 'w'))
	for word, msg in wordlist.items():
		stringfile.writerow([word, msg])
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
def addword(word, msg):
	"""
	Adding word into the base.
	"""
	wordlist[word] = msg
	savewords()
	print "*** Added word '"+word+"': "+msg
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
def delword(word):
	"""
	Delete word from the base.
	"""
	if word in wordlist:
		del wordlist[word]
		savewords()
		print "*** Deleted word: "+word
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
def GetPlayerName(steamid):
	"""
	GetPlayerName
	>>> GetPlayerName('76561197977339527')
	'twitchtvfroxerbbq'
	"""
	url = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key='+steam_key+'&steamids='+steamid+'&format=json'

	try:
		req = urllib2.urlopen(url)
		js = json.loads(req.read())

		if len(js['response']) == 1:
			for players in js['response']['players']:
					if players['personaname']:
						return str(players['personaname'])
		else:
			return 'Can\'t get player\'s info.'

	except:
		return 'Error in response.'
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
def GetCurrentServer(steamid, gameid):
	"""
	Gathering current server where user playing right now.
	"""
	url = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key='+steam_key+'&steamids='+steamid+'&format=json'

	try:
		req = urllib2.urlopen(url)
		js = json.loads(req.read())

		if len(js['response']['players']) == 1:
			for players in js['response']['players']:
				if players['gameid'] == gameid:
					for gameserverip in players['gameserverip']:
						return { "server": players['gameserverip'], "type": "IP" }
					else:
						return { "server": players['gameserversteamid'], "type": "STEAMID" }
				else:
					return {"error": "Player not in game now."}
		else:
			return { "error": "Can\'t get player\'s info."}
	except:
		return { "error": "Error in response" }
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
def GetHoursPlayed(steamid, gameid):
	"""
	Gathering hours playing in particular game.
	>>> GetHoursPlayed('76561198072015441', '252490')
	86
	"""
	if steamid != '' and gameid != '':
		url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key='+steam_key+'&steamid='+steamid+'&format=json'
		req = urllib2.urlopen(url)
		js = json.loads(req.read())

		if len(js['response']) == 2:
			for games in js['response']['games']:
				if games['appid'] == int(gameid):
					return int(games['playtime_forever'])/60
			else:
				PRIVMSG('Cat\'t find game in player\'s library.')
				return -1
		else:
			PRIVMSG('Error in request.')
			return -1
	else:
		PRIVMSG('Not enoght parameters.')
		return -1
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
def GetNameByID(steamid):
	"""
	Gathering player's name from profile by profile name or STEAMID.
	>>> GetNameByID('76561198072015441')
	'5kr1p7'
	"""
	if steamid:
		url = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key='+steam_key+'&steamids='+steamid+'&format=json'
		req = urllib2.urlopen(url)
		js = json.loads(req.read())

		if len(js['response']['players']) > 0:
			return str(js['response']['players'][0]['personaname'])
		else:
			print "Not found."
		return ''
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
def GetSteamID64(name):
	"""
	Gathering STEAM64 identifier.
	>>> GetSteamID64("5kr1p7")
	'76561198072015441'
	"""
	if name.find('http://steamcommunity.com/profiles/') != -1:
		k = name.rfind('/')
		if(k != -1):
			name = name[k+1:]

	if re.match("^[A-Za-z0-9]*$", name):
		url = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key='+steam_key+'&steamids='+name+'&format=json'
		req = urllib2.urlopen(url)
		js = json.loads(req.read())

		if len(js['response']['players']) > 0:
			return name
		else:
			url = 'http://steamcommunity.com/id/'+name+'?xml=1'
			try:
				req = urllib2.urlopen(url)
				xml = parse(req)

				steamid = xml.getElementsByTagName('steamID64')
				if steamid:
					for node in steamid:
						return str(node.childNodes[0].nodeValue)
				else:
					return ''
			except:
				return ''
	else:
		return ''
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
def OneOrMore(num, name):
	"""
	Function to auto plural numbers.
	>>> OneOrMore(5, "day")
	'5 days '
	"""
	if num > 1 or num == 0:
		name += "s"
	return str(num)+" "+name+" "
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
def MinutesToDate(sec):
	"""
	Function convert minutes to human readable date.
	>>> MinutesToDate(23182)
	'6 hours 26 minutes '
	"""
	date = ""
	if sec > 86400:
		days = int(sec / 86400)
		sec -= days * 86400
		date += OneOrMore(days, "day")
	if sec > 3600:
		hours = int(sec / 3600)
		sec -= hours * 3600
		date += OneOrMore(hours, "hour")
	if sec > 60:
		mins = int(sec / 60)
		date += OneOrMore(mins, "minute")
	return date
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
def HoursToDate(hours):
	"""Test Hours to Date.
	>>> HoursToDate(994)
	'1 month 1 week 4 days 10 hours'
	"""
	import math

	date = ''

	if hours >= 8760:
		years = math.trunc(hours/8760)
		hours -= years*8760
		date += OneOrMore(years, "year")

	if hours >= 720:
		months = math.trunc(hours/720)
		hours -= months*720
		date += OneOrMore(months, "month")

	if hours >= 168:
		weeks = math.trunc(hours/168)
		hours -= weeks*168
		date += OneOrMore(weeks, "week")

	if hours >= 24:
		days = math.trunc(hours/24)
		hours -= days*24
		date += OneOrMore(days, "day")

	date += OneOrMore(hours, "hour")
	return date.rstrip(' ')
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
def GetStreamInfo(name):
		"""
		Gathering stream information.
		"""
		twitch_url = 'https://api.twitch.tv/kraken/streams/' +name
		jtv_url = 'http://api.justin.tv/api/stream/list.json?channel=' +name
		stream = {}
		try:
		#if 1 == 1:
				req = urllib2.urlopen(twitch_url)
				js = json.loads(req.read())
				#print js
				if 'error' in js:
						return { "error": 3, "message": "Stream not found." }

				elif js["stream"]:
						stream["title"] =			js["stream"]["channel"]["status"]
						stream["viewers"] =			js["stream"]["viewers"]
						stream["game"] =			js["stream"]["game"]
						stream["name"] =			js["stream"]["channel"]["display_name"]
						stream["streamer"] =		js["stream"]["channel"]["name"]
						#stream["stream_date"] =	js["stream"]["channel"]["updated_at"]
						stream["followers"] =		js["stream"]["channel"]["followers"]
						stream["url"] =				js["stream"]["channel"]["url"]
						stream["error"] =			0

						try:
							req = urllib2.urlopen(jtv_url)
							js = json.loads(req.read())

							if len(js) > 0:
								time1 = time.strptime(str(js[0]["up_time"]), "%a %b %d %H:%M:%S %Y")
								time2 = time.strptime(str(datetime.now()-timedelta(hours=11)), "%Y-%m-%d %H:%M:%S.%f")
								stream["uptime"] = time.mktime(time2) - time.mktime(time1)
						except:
							return {"error": 4, "message": "Can't load justin API" }

						return stream
				else:
						return { "error": 2, "message": "Stream is offline." }
		except:
				return { "error": 1, "message": "Error in request." }
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
def Connect():
	global s
	s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
	s.connect((HOST, PORT))

	Auth(NICK, PASS, IDENT, HOST, REALNAME)
	JOIN(CHANNEL)
#--------------------------------------------------------------------------------

if __name__ == "__main__":
	import sys
	import doctest
	#doctest.testmod(verbose=True)
	if doctest.testmod():
		print "Test PASSED"
	else:
		print "Test FAILED"
		sys.exit(0)

readwords()
readbuffer = ""

Connect()
while 1:
#	readbuffer = readbuffer +s.recv(1024)
	readbuffer = s.recv(1024)
	if len(readbuffer) == 0:
		print "*** DISCONNECTED ***"
		Connect()
	if not readbuffer:
		break

	temp = string.split(readbuffer, "\n")
	print readbuffer
	readbuffer = temp.pop()


	for line in temp:
		line = string.rstrip(line)
		if line.find("PRIVMSG") != -1:
			result = re.match( r'^:(.*)!.* PRIVMSG (#.*) :(.*)$', line.rstrip(), re.M|re.I)
			if result:
				message = { "nick": result.group(1), "channel": result.group(2), "message": result.group(3) }

				if message["message"][0] == "!":
					cmd = { }
					cmd["argc"] = len(message["message"][1:].split(' '))-1
					cmd["command"] = message["message"][1:].split(' ')[0]

					if cmd["argc"] > 0:
						cmd["arg"] = message["message"][1:].split(' ')[1:]


					# --- WORDS ------------------------------------------------
					if cmd["command"] == "addword" and cmd["argc"] >= 3:
						addword(cmd["arg"][0], ' '.join(cmd["arg"][1:]))

					elif cmd["command"] == 'delword' and cmd["argc"] == 1:
						delword(cmd["arg"][0])

					elif cmd["command"] in wordlist:
						PRIVMSG(wordlist[cmd["command"]])


					# --- TWITCH -----------------------------------------------
					elif cmd["command"] == "stream" and cmd["argc"] == 1:
						twitch = cmd["arg"][0]
						stream = GetStreamInfo(twitch)
						if stream["error"] == 0:
							reply = "%s streaming %s for %s(%s viewers | %s followers)" %(stream["streamer"], stream["game"], MinutesToDate(stream["uptime"]), stream["viewers"], stream["followers"])
						else:
							reply = stream["message"]
						PRIVMSG(reply)


					# --- STEAM ------------------------------------------------
					elif cmd["command"] == "skill" and cmd["argc"] == 1:
						steamid = GetSteamID64(cmd["arg"][0])
						steamname = GetNameByID(steamid)

						if steamname != '' and steamid != '':
							hours_played = GetHoursPlayed(steamid, '252490')
							if hours_played > 0:
								PRIVMSG("Player %s was played RUST for %i hours (%s)" %(steamname.encode('utf-8').strip(), hours_played, HoursToDate(hours_played) ))
							else:
								PRIVMSG("Error in request")
						else:
							PRIVMSG("Player not found. Make sure you are using STEAM_ID, profilename or profile URL")

					elif cmd["command"] == "server" and cmd["argc"] == 1:
						steamid = GetSteamID64(cmd["arg"][0])
						steamname = GetNameByID(steamid)

						server = GetCurrentServer(steamid, '252490')
						if 'error' in server:
							PRIVMSG("Error: %s" %server['error'])
						else:
							PRIVMSG("Player %s playing RUST on server with %s %s now." %(steamname, server['type'], server['server']))


					# --- WORLD CLOCK ------------------------------------------
					elif cmd["command"] == "time" and cmd["argc"] >= 1:
						city = ' '.join(cmd["arg"])
						resp = urllib2.urlopen('http://api.worldweatheronline.com/free/v1/tz.ashx?key='+apikey+'&q='+city.replace(' ', '%20')+'&format=json')
						time = json.loads(resp.read())
						if 'time_zone' in time['data']:
							time = time['data']['time_zone'][0]['localtime']
							PRIVMSG('Time in %s is: %s' %(city, time))
						else:
							PRIVMSG('Error in request')


		# --- PING-PONG --------------------------------------------------------
		elif(line.find('PING') != -1):
			PONG(line.split(' ')[1].rstrip())
s.close()
