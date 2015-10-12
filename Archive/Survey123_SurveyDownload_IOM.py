import os, shutil, zipfile, glob
import urllib, urllib2, datetime, arcpy, json

##Config##
username='jturco_DBS'
password='shannon1717'
wksp = r'C:\Data\IOM'
conn = r'C:\Data\IOM\IOM.sde'
surveyName = "RoundIISurvey"
CSVLocation = r'C:\Data\IOM'

def getToken(username, password):
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
	print "Successfully received token from AGOL"
	return token


def getItems(token):
	'''Find the Item based on the Survey Name'''
	'''This is already built to handle multiple names'''

	itemdict = {}
	gtUrl = 'https://www.arcgis.com/sharing/rest/content/users/' + username
	gtValues = {'token' : token ,
	'referer' : 'http://www.arcgis.com',
	'f' : 'json'}
	gtData = urllib.urlencode(gtValues)
	gtRequest = urllib2.Request(gtUrl, gtData)
	gtResponse = urllib2.urlopen(gtRequest)
	parsed_json = json.load(gtResponse)
	gtResponse.close()

	items = parsed_json['items']
	for item in items:
		if item['type'] == "Feature Service" and item['title'] == surveyName:
			print item['title']
			itemid = item['id']
			itemurl = item['url']
			itemdict[itemid] = itemurl

	folders = parsed_json['folders']
	for items in folders:
		folderID = items['id']
		folderURL = 'https://www.arcgis.com/sharing/rest/content/users/' + username + '/' + folderID
		gtData = urllib.urlencode(gtValues)
		gtRequest = urllib2.Request(folderURL, gtData)
		folderREQ = urllib2.urlopen(gtRequest)
		folderItems = json.load(folderREQ)
		newitems = folderItems['items']
		for item in newitems:
			if item['type'] == "Feature Service" and item['title'] == surveyName:
				print item['title']
				itemid = item['id']
				itemurl = item['url']	
				itemdict[itemid] = itemurl

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
	
	lyrlist =  []
	num = 0
	while numlayers > 0:
		lyrlist.append(str(num))
		num += 1
		numlayers -= 1
	layers = ','.join(lyrlist)
	print layers

	serviceREQ.close()
	return itemdict, layers

def getReplica(token, itemdict, layers):

	#crUrl = 'http://services1.arcgis.com/g2TonOxuRkIqSOFx/arcgis/rest/services/service_e0e0cde7356549138e6b82d078b3b5c0/FeatureServer/CreateReplica'
	crUrl = itemdict.itervalues().next() + '/CreateReplica'
	crValues = {
	'f' : 'json',
	'layers' : layers,
	'layerQueries' : '{"0":{"queryOption": "none"}, "1":{"queryOption": "none"}, "2":{"queryOption":"none"}}',
	'returnAttachments' : 'false',
	'syncModel' : 'none',
	'dataFormat': 'filegdb',
	'token' : token}

	#find a way to handle different levels of relates

	crData = urllib.urlencode(crValues)
	crRequest = urllib2.Request(crUrl, crData)
	crResponse = urllib2.urlopen(crRequest)
	crJson = json.load(crResponse)
	print crJson
	replicaUrl = crJson['responseUrl']
	print "Downloading and unzipping Fgdb"
	zippedfile = wksp + "\\Temp\\" + itemdict.iterkeys().next() + ".zip"
	urllib.urlretrieve(replicaUrl, zippedfile)
	zip_ref = zipfile.ZipFile(zippedfile, 'r')
	zip_ref.extractall("c:\data\IOM\Temp\\")
	zip_ref.close()
	return

def ProcessReplica(conn):

	for file in os.listdir(wksp + "\\Temp\\"):
		if file.endswith(".gdb"):
			arcpy.env.workspace = wksp + "\\Temp\\" + file
			gdb = file
	
	# This could be changed as there may only be 1 fc per survey
	stables = arcpy.ListTables()
	surveyfc = arcpy.ListFeatureClasses()

	sdeenv = conn
	sdefc = None
	fgdbenv = wksp + "\\Temp\\" + gdb
	fgdbfc = None

	for fc in surveyfc:
		fgdbfc = fgdbenv + "\\" + fc
		#Trimming Lengthy Fields
		fields = arcpy.ListFields(fc)
		print "Trimming field over 29 characters"
		for field in fields:
			if len(field.name) > 29:
				newname = field.name[:-2]
				arcpy.AlterField_management(fc, field.name, newname)
		
		arcpy.env.workspace = conn
		gdbtables = arcpy.ListTables()
		gdbfcs = arcpy.ListFeatureClasses()

		if not gdbfcs:
			sdefc = conn + "\\" + surveyName
			arcpy.Copy_management(fgdbfc, sdefc)
		else:
			for gfc in gdbfcs:
				if fc == gfc[8:]:
					sdefc = sdeenv + "\\" + gfc
					print "Feature class already exists, appending new data..."
					#Build out row id list by search existing SDE
					sdelayer = arcpy.SearchCursor(sdefc)
					existingROWID = []
					
					for row in sdelayer:
						existingROWID.append(row.getValue("ROWID"))
						del row
					del sdelayer
					print existingROWID
					
					#Compare rowid and delete if it is already there
					fgdblayer = arcpy.UpdateCursor(fgdbfc)

					for row in fgdblayer:
						if row.getValue("ROWID") in existingROWID:
							print "Row Already exists"
							fgdblayer.deleteRow(row)
						del row
					del fgdblayer
					arcpy.Append_management(fgdbfc, sdefc, "NO_TEST")
				else:
					sdefc = sdeenv + "\\" + surveyName
					arcpy.Copy_management(fgdbfc, sdefc)
	return

def exportCSV():

	for file in os.listdir(wksp + "\\Temp\\"):
		if file.endswith(".gdb"):
			arcpy.env.workspace = wksp + "\\Temp\\" + file
			gdb = wksp + "\\Temp\\" + file
	
	# This could be changed as there may only be 1 fc per survey
	stables = arcpy.ListTables()
	for table in stables:
		print table
		arcpy.TableToExcel_conversion(table, CSVLocation + '\\' + table + ".xls")

	surveyfc = arcpy.ListFeatureClasses()
	for fc in surveyfc:
		print fc
		arcpy.TableToExcel_conversion(fc, CSVLocation + '\\' + fc + ".xls")

	return

if __name__ == '__main__':

	#Delete\Recreate Temp Directory
	shutil.rmtree(wksp + "\\Temp\\")
	os.makedirs(wksp + "\\Temp\\")

	token = getToken(username, password)
	itemdict, layers = getItems(token)
	getReplica(token, itemdict, layers)
	ProcessReplica(conn)
	#exportCSV()
