from aqt import mw
from PyQt5.QtWidgets import QAction, QMenu
from aqt.qt import *
from aqt.utils import showInfo, showWarning, tooltip
from aqt import gui_hooks

import webbrowser
import requests
from bs4 import BeautifulSoup
import datetime
import hashlib

from .Leaderboard import start_main
from .Setup import start_setup
from .Stats import Stats
from .config_manager import write_config
from .lb_on_homescreen import leaderboard_on_deck_browser

def Main():
	check_info()
	create_token()
	config = mw.addonManager.getConfig(__name__)
	if config["username"] == "":
		invoke_setup()
	else:
		#mw.progress.start()
		mw.leaderboard = start_main(season_start, season_end)
		mw.leaderboard.show()
		mw.leaderboard.raise_()
		mw.leaderboard.activateWindow()

def invoke_setup():
	mw.lb_setup = start_setup(season_start, season_end)
	mw.lb_setup.show()
	mw.lb_setup.raise_()
	mw.lb_setup.activateWindow()

def config_setup():
	s = start_setup(season_start, season_end)
	if s.exec():
		pass

def github():
	webbrowser.open('https://github.com/ThoreBor/Anki_Leaderboard/issues')

def create_token():
	config = mw.addonManager.getConfig(__name__)
	if config["token"] == None:
		token = str(mw.col.db.list("SELECT id FROM revlog LIMIT 1"))
		token = hashlib.sha1(token.encode('utf-8')).hexdigest().upper()
		write_config("token", token)

def check_info():
	try:
		url = 'https://ankileaderboardinfo.netlify.app'
		headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36 OPR/62.0.3331.116'}
		page = requests.get(url, headers=headers)
		soup = BeautifulSoup(page.content, 'html.parser')
		if soup.find(id='show_message').get_text() == "True":
			info = soup.find("div", id="Message")
			showInfo(str(info), title="Leaderboard")
		else:
			pass
	except:
		showWarning("Make sure you're connected to the internet.")

def add_username_to_friendlist():
	config = mw.addonManager.getConfig(__name__)
	if config['username'] != "" and config['username'] not in config['friends']:
		friends = config["friends"]
		friends.append(config['username'])
		write_config("friends", friends)

def background_sync():
	create_token()
	config = mw.addonManager.getConfig(__name__)
	token = config["token"]
	url = 'https://ankileaderboard.pythonanywhere.com/sync/'
	config5 = config['subject'].replace(" ", "")
	config6 = config['country'].replace(" ", "")

	streak, cards, time, cards_past_30_days, retention, league_reviews, league_time, league_retention = Stats(season_start, season_end)

	data = {'Username': config['username'], "Streak": streak, "Cards": cards , "Time": time , "Sync_Date": datetime.datetime.now(), 
	"Month": cards_past_30_days, "Subject": config5, "Country": config6, "Retention": retention, 
	"league_reviews": league_reviews, "league_time": league_time, "league_retention": league_retention,
	"Token_v3": token, "Version": "v1.6.0"}

	leaderboard_on_deck_browser()

	try:
		x = requests.post(url, data = data, timeout=20)
	except:
		showWarning("Timeout error - No internet connection, or server response took too long.")

	if x.text == "Done!":
		tooltip("Synced leaderboard successfully.")
	else:
		showWarning(str(x.text))

def season():
	url = 'https://ankileaderboard.pythonanywhere.com/season/'
	try:
		season = requests.get(url, timeout=20).json()
	except:
		showWarning("Timeout error - No internet connection, or server response took too long.")

	global season_start
	season_start = season[0]
	season_start = datetime.datetime(season_start[0],season_start[1],season_start[2],season_start[3],season_start[4],season_start[5])
	global season_end
	season_end = season[1]
	season_end = datetime.datetime(season_end[0],season_end[1],season_end[2],season_end[3],season_end[4],season_end[5])

def add_menu(Name, Button, exe, *sc):
	action = QAction(Button, mw)
	action.triggered.connect(exe)
	if not hasattr(mw, 'menu'):
		mw.menu = {}
	if Name not in mw.menu:
		add = QMenu(Name, mw)
		mw.menu[Name] = add
		mw.form.menubar.insertMenu(mw.form.menuTools.menuAction(), add)
	mw.menu[Name].addAction(action)
	for i in sc:
		action.setShortcut(QKeySequence(i))

def initialize():
	config = mw.addonManager.getConfig(__name__)
	if config["autosync"] == True:
		gui_hooks.reviewer_will_end.append(background_sync)
	if config["homescreen"] == True:
		leaderboard_on_deck_browser()

write_config("achievement", True)
add_username_to_friendlist()
season()
gui_hooks.profile_did_open.append(initialize)

add_menu('&Leaderboard',"&Leaderboard", Main, 'Shift+L')
add_menu('&Leaderboard',"&Sync and update leaderboard on the homescreen", background_sync, "Shift+S")
add_menu('&Leaderboard',"&Config", invoke_setup)
add_menu('&Leaderboard',"&Make a feature request or report a bug", github)
mw.addonManager.setConfigAction(__name__, config_setup)