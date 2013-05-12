#! /usr/bin/env python

import os, sys, json, re, shutil, urllib2
from glob import glob
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
	with open(dbDir+'_unknown.json','r') as knownUnfoundFilms:
		filmsNotFound = json.load(knownUnfoundFilms)
except:
	filmsNotFound = []


print "Getting film names:"
out=""
for path, dirs, files in os.walk(filmDir):
	for file in files:
		pass
	for dir in dirs:
		for fileName in sorted(os.listdir(path+'/'+dir)):
			filePath = path+'/'+dir+'/'+fileName
			filePublicPath = publicPath+'/'+dir+'/'+fileName
			if fileName.endswith(tuple(formatsReadable)):
				for ext in formatsReadable:
					fileName=fileName.replace(ext,"")

				filmDataURI = "http://omdbapi.com/?t=%s" % (fileName.replace(" ","%20"))

				year = re.search('\((\d{4})\)',fileName)
				if year:
					year = year.group(1)
					fileName=fileName.replace('('+year+')',"")
					fileName=fileName.strip()
					filmDataURI = "http://omdbapi.com/?t=%s&y=%s" % (fileName.replace(" ","%20"),year)
				else:
					year=""

				fileName = ''.join(c for c in fileName if c.isalnum())+year
				filmDBpath = dbDir+fileName+".json"

				if fileName not in filmsNotFound:
					try:
						with open(filmDBpath, 'rb') as readFile:
							film = json.load(readFile)
							filmsList.append(film)
					except:
						film = json.load(urllib2.urlopen(filmDataURI))
						if film['Response'] == 'True':
							film['FileName'] = fileName
							film['LocalPath'] = filePath
							film['PublicPath'] = filePublicPath
							film['Readable'] = "yes"
							film['PlotFull'] = json.load(urllib2.urlopen(filmDataURI+"&plot=full"))['Plot']
							if "N/A" not in film['Poster']:
								localPosterName = imgDir+fileName+".jpg"
								posterImage = urllib2.urlopen(film['Poster'])
								with open(localPosterName, 'w') as poster:
									poster.write(posterImage.read())
								film['Poster'] = localPosterName.replace(webDir,'')
							with open(filmDBpath, 'w') as outFile:
								json.dump(film, outFile)
							filmsList.append(film)
						else:
							filmsNotFound.append(fileName)

					if fileName not in filmsNotFound:
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
						except:
							raise

			elif fileName.endswith(tuple(formatsMightBeUnreadable)):
				pass
			elif fileName.endswith('.srt'):
				pass
			else:
				ext = os.path.splitext(fileName)[1]
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

for film in filmsList:
	try:
		out += """<div onclick="window.location='%s.html'">%s<br />
		\t<span>%s - %s/10</span>
		\t<p>%s</p>
		</div>
		""" % (film['FileName'], film['Title'],
				 film['Runtime'], film['imdbRating'],
				 film['Plot'])
	except:
		print "problem for an entry while creating index list:"
		pprint(film)
		raise

try:
	shutil.copy(templateDir+'_index.html', webDir+'index.html')
	out=out.encode('ascii', 'ignore')
	with open(webDir+'index.html', "r") as source:
		lines = source.readlines()
	with open(webDir+'index.html', "w") as source:
		for line in lines:
			oldLine = line
			if '$LIST$' in line:
				line = line.replace('$LIST$',out)
			try:
				source.write(line)
			except:
				source.write(oldLine)
				
except:
	print "could not create film index"
	raise
print "done"
