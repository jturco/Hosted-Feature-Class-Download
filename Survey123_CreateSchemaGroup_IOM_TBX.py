import os, shutil, zipfile, glob
import urllib, urllib2, datetime, arcpy, json
import ConfigParser, logging

##Config##
groupname = arcpy.GetParameterAsText(0)
surveyName = arcpy.GetParameterAsText(1)
username=arcpy.GetParameterAsText(2)
password=arcpy.GetParameterAsText(3)

def ConfigSectionMap(section):
	dict1 = {}
	options = Config.options(section)
	for option in options:
		try:
			dict1[option] = Config.get(section, option)
			if dict1[option] == -1:
				print "Skip: " + option
		except:
			print "Exception on " + option
			dict1[option] = None 
	return dict1

# username='username'
# password='password'
# groupname = "IOM Survey Group"
# surveyName = "RoundIISurvey"

configfile = r'C:\Data\IOM\Scripts\CONFIG.INI'
####CONFIG FILE PARAMETERS##########################
Config = ConfigParser.ConfigParser()
Config.read(configfile)

conn = ConfigSectionMap("ALL")['databaseconnection']
wksp = ConfigSectionMap("ALL")['workspace']
orgurl = ConfigSectionMap("ALL")['orgurl']
logfile = ConfigSectionMap("ALL")['logfile']

logging.basicConfig(filename=logfile + "CreateSchemaLog.log", level=logging.DEBUG)

def getToken(username, password):
	'''Gets a token from the ArcGIS Online or Portal Account'''
	'''Organization URL is specified in the Config.ini file'''

	arcpy.AddMessage("Getting Token for Organization Account...")
	logging.debug("Getting Token for Organization Account...")
	gtUrl = 'https://www.arcgis.com/sharing/rest/generateToken'
	gtValues = {'username' : username,
	'password' : password,
	'referer' : 'http://www.arcgis.com',
	'f' : 'json' }
	gtData = urllib.urlencode(gtValues)
	gtRequest = urllib2.Request(gtUrl, gtData)
	gtResponse = urllib2.urlopen(gtRequest)
	gtJson = json.load(gtResponse)
	token = gtJson['token']
	logging.debug("Successfully received token: " + token)
	arcpy.AddMessage("Successfully received token...")
	
	return token

def getItemsGroup(token):
	'''Find the Item based on the Survey Name'''
	'''This is already built to handle multiple names'''

	print "Finding Survey in Group " + groupname
	arcpy.AddMessage("Finding Survey in Group " + groupname)

	itemdict = {}
	gtUrl = 'http://www.arcgis.com/sharing/rest/community/self'
	gtValues = {'token' : token ,
	'referer' : 'http://www.arcgis.com',
	'f' : 'json'}
	gtData = urllib.urlencode(gtValues)
	gtRequest = urllib2.Request(gtUrl, gtData)
	gtResponse = urllib2.urlopen(gtRequest)
	parsed_json = json.load(gtResponse)
	gtResponse.close()

	groups = parsed_json['groups']
	
	#get the groupid
	for group in groups:
		print group['title']
		if group['title'] == groupname:
			print group['id']
			groupid = group['id']

	gtUrl = orgurl + '/sharing/rest/content/groups/' + groupid
	gtValues = {'token' : token ,
	'referer' : 'http://www.arcgis.com',
	'f' : 'json'}
	gtData = urllib.urlencode(gtValues)
	gtRequest = urllib2.Request(gtUrl, gtData)
	gtResponse = urllib2.urlopen(gtRequest)
	parsed_json = json.load(gtResponse)
	gtResponse.close()

	items = parsed_json['items']

	arcpy.AddMessage("Searching Group for: " + surveyName)
	
	for item in items:
		if item['type'] == "Feature Service" and item['title'] == surveyName:
			arcpy.AddMessage("Fround Hosted Feature Service: " + item['title'])
			itemid = item['id']
			itemurl = item['url']
			itemdict[itemid] = itemurl

	print "Hosted Feature Servicce URL: " + itemurl
	arcpy.AddMessage("Hosted Feature Servicce URL: " + itemurl)

	#get number of layers for CreateReplica
	serviceURL = itemurl
	gtValues = {'token' : token , 'f' : 'json'}
	gtData = urllib.urlencode(gtValues)
	gtRequest = urllib2.Request(serviceURL, gtData)
	serviceREQ = urllib2.urlopen(gtRequest)
	service_json = json.load(serviceREQ)
	layers = service_json['layers']
	tables = service_json['tables']
	numlayers = len(layers) + len(tables)
	
	print "Found " + str(len(layers)) + " layers, and " + str(len(tables)) + " tables."
	arcpy.AddMessage("Found " + str(len(layers)) + " layers, and " + str(len(tables)) + " tables.")

	lyrlist =  []
	lyrQueryList = []
	num = 0
	while numlayers > 0:
		lyrlist.append(str(num))
		lyrQueryList.append('"' +str(num)+ '":{"queryOption":"all"}')
		num += 1
		numlayers -= 1
	layers = ','.join(lyrlist)
	lyrQueryList = ",".join(lyrQueryList)
	lyrQueryList = "{" + lyrQueryList + "}"
	arcpy.AddMessage(lyrQueryList)

	serviceREQ.close()
	return itemdict, layers, lyrQueryList

def getReplica(token, itemdict, layers, layerQueries):

	crUrl = itemdict.itervalues().next() + '/CreateReplica'
	crValues = {
	'f' : 'json',
	'layers' : layers,
	'layerQueries' : layerQueries,
	'returnAttachments' : 'false',
	'syncModel' : 'none',
	'dataFormat': 'filegdb',
	'token' : token}

	crData = urllib.urlencode(crValues)
	crRequest = urllib2.Request(crUrl, crData)
	crResponse = urllib2.urlopen(crRequest)
	crJson = json.load(crResponse)
	replicaUrl = crJson['responseUrl']
	zippedfile = wksp + "\\Temp\\" + itemdict.iterkeys().next() + ".zip"
	urllib.urlretrieve(replicaUrl, zippedfile)
	zip_ref = zipfile.ZipFile(zippedfile, 'r')
	zip_ref.extractall("c:\data\IOM\Temp\\")
	zip_ref.close()

	return

def TrimFields(table):

	print "Trimming fields for: " + table
	arcpy.AddMessage("Trimming fields for: " + table)
	fields = arcpy.ListFields(table)

	for field in fields:
		if len(field.name) > 30:
			trim_amount = len(field.name) - 30
			trimmed_name = "F" + field.name[:-trim_amount]
			arcpy.AlterField_management(table, field.name, trimmed_name)
		elif field.name == "end":
			new_name = field.name + "_"
			arcpy.AlterField_management(table, field.name, new_name)
		elif field.name.startswith("_"):
			#Hanndles the F appending needed by database for fields that start with underscores
			new_name = "F" + field.name
			arcpy.AlterField_management(table, field.name, new_name)
	return

def ProcessReplica(conn):
	#Get the Extracted Geodatabase Name
	for file in os.listdir(wksp + "\\Temp\\"):
		if file.endswith(".gdb"):
			extracted_gdb = wksp + "\\Temp\\" + file
	
	arcpy.env.workspace = extracted_gdb
	surveytable = arcpy.ListTables()
	surveyfc = arcpy.ListFeatureClasses()

	#Trim All Field & Tables Here
	for fc in surveyfc:
		TrimFields(fc)

	for table in surveytable:
		TrimFields(table)

	arcpy.env.workspace = conn
	sde_tables = arcpy.ListTables()
	sde_fcs = arcpy.ListFeatureClasses()

	for fc in surveyfc:
		if not arcpy.Exists(conn + "\\" + fc):
			print "Feature class does not exists"
			arcpy.env.workspace = extracted_gdb
			arcpy.DeleteRows_management(extracted_gdb + "\\"+ fc)
			for table in surveytable:
				if not arcpy.Exists(conn + "\\" + table):
					arcpy.DeleteRows_management(fc)
				else:
					print "Table already exists in database"
					arcpy.AddMessage("Table already exists in database")
					#handle table here

			arcpy.Copy_management(fc, conn + "\\" + fc)
		else:
			print "Survey already exists in database"
			arcpy.AddMessage("Survey already exists in database")
	return

if __name__ == '__main__':
	logging.debug("Starting script...")
	#Delete\Recreate Temp Directory
	shutil.rmtree(wksp + "\\Temp\\")
	os.makedirs(wksp + "\\Temp\\")

	token = getToken(username, password)
	itemdict, layers, layerQueries = getItemsGroup(token)
	getReplica(token, itemdict, layers, layerQueries)

	ProcessReplica(conn)
	
