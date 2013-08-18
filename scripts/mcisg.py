#! /usr/bin/env python

import os, sys, json, re, shutil, urllib2
from pprint import pprint

filmDir = "/home/user/Public/Videos"
publicPath = "file://192.168.1.1/public/videos"
projectBase = os.path.dirname(os.path.abspath(os.path.dirname(sys.argv[0])))
dbDir = projectBase+"/db/"
webDir = "/var/www/films/"
imgDir = webDir+"img/"
templateDir = projectBase+"/templates/"

formatsReadable = [".avi", ".mp4"]
formatsMightBeUnreadable = [".flv", ".m4v", ".mkv", ".mov", ".wmv"]
formatsUnknown = []

filmsList = []
try:
	with open(dbDir+'_unknown.json', 'r') as knownUnfoundFilms:
		filmsNotFound = json.load(knownUnfoundFilms)
except:
	filmsNotFound = []


def makeFilmPage(film):
	fileName = film['FileName']
	try:
		shutil.copy(templateDir+'_film.html', webDir+fileName+'.html')
		with open(webDir+fileName+'.html', "r") as source:
			lines = source.readlines()
		with open(webDir+fileName+'.html', "w") as source:
			for line in lines:
				oldLine = line
				for elmt in film:
					if '$'+elmt.upper()+'$' in line:
						line = line.replace('$'+elmt.upper()+'$', film[elmt].encode('ascii', 'ignore'))
				try:
					source.write(line)
				except:
					source.write(oldLine)
		return True
	except:
		raise
		return False


def makeFilmIndex(filmsList):
	out = ""
	for film in filmsList:
		try:
			out += """<div class="listfilm"><a href="%s.html">%s</a><br />
			\t<span>%s - %s - %s/10</span>
			\t<p>%s</p>
			</div><hr />
			""" % (film['FileName'], film['Title'],
					film['Runtime'], film['Year'], film['imdbRating'],
					film['Plot'])
		except:
			print "problem for an entry while creating index list:"
			pprint(film)
			raise
	try:
		shutil.copy(templateDir+'_index.html', webDir+'index.html')
		out = out.encode('ascii', 'ignore')
		with open(webDir+'index.html', "r") as source:
			lines = source.readlines()
		with open(webDir+'index.html', "w") as source:
			for line in lines:
				oldLine = line
				if '$LIST$' in line:
					line = line.replace('$LIST$', out)
				try:
					source.write(line)
				except:
					source.write(oldLine)
	except:
		print "could not create film index"
		raise


def identifyFilm(fileName):
	filmYear = re.search('\((\d{4})\)', fileName)
	if filmYear:
		filmYear = filmYear.group(1)
		filmName = fileName.replace('('+filmYear+')', "")
		filmName = filmName.strip()
	else:
		filmName = fileName.strip()
		filmYear = ''
	return filmName, filmYear


def findFilm(filmName, filmYear):
	filmDataURI = "http://omdbapi.com/?t="+urllib2.quote(filmName)+(("&y="+filmYear) if filmYear else '')
	film = json.load(urllib2.urlopen(filmDataURI))
	if film['Response'] == 'True' and film['Type'] == "movie":
		film['PlotFull'] = json.load(urllib2.urlopen(filmDataURI+"&plot=full"))['Plot']
		return film

	filmDataURI = "http://mymovieapi.com/?&q="+urllib2.quote(filmName)+(("&year="+filmYear) if filmYear else '')
	film = json.load(urllib2.urlopen(filmDataURI))
	if 'error' not in film:
		filmDataURI = "http://omdbapi.com/?i="+film[0]['imdb_id']
		film = json.load(urllib2.urlopen(filmDataURI))
		if film['Response'] == 'True' and film['Type'] == "movie":
			film['PlotFull'] = json.load(urllib2.urlopen(filmDataURI+"&plot=full"))['Plot']
			return film

	filmDataURI = "http://deanclatworthy.com/imdb?&q="+urllib2.quote(filmName)+(("&year="+filmYear) if filmYear else '')
	film = json.load(urllib2.urlopen(filmDataURI))
	if 'error' not in film:
		filmDataURI = "http://omdbapi.com/?i="+film['imdbid']
		film = json.load(urllib2.urlopen(filmDataURI))
		if film['Response'] == 'True' and film['Type'] == "movie":
			film['PlotFull'] = json.load(urllib2.urlopen(filmDataURI+"&plot=full"))['Plot']
			return film

	return False


def getFilmPoster(film):
	global imgDir, webDir
	if "N/A" not in film['Poster']:
		localPosterName = imgDir+film['FileName']+".jpg"
		posterImage = urllib2.urlopen(film['Poster'])
		with open(localPosterName, 'w') as poster:
			poster.write(posterImage.read())
		film['Poster'] = localPosterName.replace(webDir, '')
	return film['Poster']


def updateFilm(film, fileName, filmFilePaths, isReadable="no"):
	film['FileName'] = fileName
	for elmt in filmFilePaths:
		film[elmt] = elmt
	film['Readable'] = isReadable
	film['Poster'] = getFilmPoster(film)
	return film

print "Getting film names:"
for path, dirs, files in os.walk(filmDir):
	for file in files:
		pass
	for dir in dirs:
		for fileName in sorted(os.listdir(path+'/'+dir)):
			filmFilePaths = {"LocalPath": path+'/'+dir+'/'+fileName,
									"PublicPath": publicPath+'/'+dir+'/'+fileName}

			fileName, ext = os.path.splitext(fileName)
			if ext in formatsReadable or ext in formatsMightBeUnreadable:
				if ext in formatsReadable:
					filmReadable = "yes"
				elif ext in formatsMightBeUnreadable:
					filmReadable = "maybe"

				filmName, filmYear = identifyFilm(fileName)
				fileName = ''.join(c for c in filmName if c.isalnum())+filmYear
				filmDBpath = dbDir+fileName+".json"

				if fileName not in filmsNotFound:
					try:
						with open(filmDBpath, 'rb') as readFile:
							film = json.load(readFile)
							filmsList.append(film)
					except:
						film = findFilm(filmName, filmYear)
						if film:
							updateFilm(film, fileName, filmFilePaths, filmReadable)
							with open(filmDBpath, 'w') as outFile:
								json.dump(film, outFile)
							filmsList.append(film)
						else:
							filmsNotFound.append(fileName)

					if fileName not in filmsNotFound:
						makeFilmPage(film)

			elif ext == '.srt':
				pass
			else:
				if ext not in formatsUnknown:
					formatsUnknown.append(ext)


print "OK: %d films" % (len(filmsList))
print "Untreated extensions: %d" % (len(formatsUnknown))
if formatsUnknown:
	print formatsUnknown
print "Not found: %d" % (len(filmsNotFound))
pprint(filmsNotFound)
with open(dbDir+'_unknown.json', 'w') as outFile:
	json.dump(filmsNotFound, outFile)

makeFilmIndex(filmsList)

print "done"
