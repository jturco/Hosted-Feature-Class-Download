import os, shutil, zipfile, glob
import urllib, urllib2, datetime, arcpy, json

##Config##
username=arcpy.GetParameterAsText(0)
password=arcpy.GetParameterAsText(1)
orgurl = arcpy.GetParameterAsText(2)
conn = arcpy.GetParameterAsText(3)
surveyName = arcpy.GetParameterAsText(4)
validation = arcpy.GetParameterAsText(5)
CSVLocation = arcpy.GetParameterAsText(6)

if validation == "false":
	validation = False 
elif validation == "true":
	validation == True

wksp = r'C:\Data\IOM'

# username='jturco_DBS'
# password='shannon1717'
# wksp = r'C:\Data\IOM'
# conn = r'C:\Data\IOM\IOM.sde'
# CSVLocation = r'C:\Data\IOM\Temp'

#validation_survey = None
#no_validation_survey = "BaseSurvey"
#surveyName = "RoundIISurvey"


def getToken(username, password):
	print "Getting Token for Organization Account..."
	arcpy.AddMessage("Getting Token for Organization Account...")
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
	print "Successfully received token..."
	arcpy.AddMessage("Successfully received token...")
	return token


def getItems(token):
	'''Find the Item based on the Survey Name'''
	'''This is already built to handle multiple names'''

	print "Finding Survey in ArcGIS Online/Portal..."
	arcpy.AddMessage("Finding Survey in ArcGIS Online/Portal...")

	itemdict = {}
	#orgurl = 'https://www.arcgis.com'
	gtUrl = orgurl +'/sharing/rest/content/users/' + username
	gtValues = {'token' : token ,
	'referer' : 'http://www.arcgis.com',
	'f' : 'json'}
	gtData = urllib.urlencode(gtValues)
	gtRequest = urllib2.Request(gtUrl, gtData)
	gtResponse = urllib2.urlopen(gtRequest)
	parsed_json = json.load(gtResponse)
	gtResponse.close()

	#Need to learn how to handle this with new validation entries
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
	num = 0
	while numlayers > 0:
		lyrlist.append(str(num))
		num += 1
		numlayers -= 1
	layers = ','.join(lyrlist)

	serviceREQ.close()
	return itemdict, layers

def getReplica(token, itemdict, layers):
	print itemdict
	#Base Survey
	#crUrl = 'http://services1.arcgis.com/g2TonOxuRkIqSOFx/ArcGIS/rest/services/service_4358578960b84c41bfbeb086294976b0/FeatureServer/CreateReplica'
	#InitialSurveyV3 shared to group
	#crUrl = 'http://services1.arcgis.com/g2TonOxuRkIqSOFx/arcgis/rest/services/service_c459498bbffc4a1cb58c3e4501fc76c7/FeatureServer/CreateReplica'
	#Deepti's RoundIISurvey
	#crUrl = 'http://services1.arcgis.com/g2TonOxuRkIqSOFx/arcgis/rest/services/service_e0e0cde7356549138e6b82d078b3b5c0/FeatureServer/CreateReplica'
	crUrl = itemdict.itervalues().next() + '/CreateReplica'
	crValues = {
	'f' : 'json',
	'layers' : layers,
	'layerQueries' : '{"0":{"queryOption": "all"}, "1":{"queryOption": "all"}, "2":{"queryOption":"all"}}',
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

	print "Trimming field over 28 characters for: " + table
	arcpy.AddMessage("Trimming field over 28 characters for: " + table)
	fields = arcpy.ListFields(table)

	for field in fields:
		if len(field.name) > 30:
			trim_amount = len(field.name) - 30
			#Find a more elegant way to do this?
			trimmed_name = "F" + field.name[:-trim_amount]
			arcpy.AlterField_management(table, field.name, trimmed_name)
		elif field.name == "end":
			print "Founnd...End"
			new_name = field.name + "_"
			arcpy.AlterField_management(table, field.name, new_name)
		elif field.name.startswith("_"):
			print "Found Starts With _ "
			new_name = "F" + field.name
			arcpy.AlterField_management(table, field.name, new_name)

	return

def getExistingRecords(table):
	RecordsList = []
	layer = arcpy.SearchCursor(table)
			
	for row in layer:
		RecordsList.append(row.getValue("ROWID"))
	#del row
	del layer
	return RecordsList

def DeleteExistingRows(table, deletes):

	print "Deleteing existing rows in : " + table

	layer = arcpy.UpdateCursor(table)
	for row in layer:
		if row.getValue("ROWID") in deletes:
			layer.deleteRow(row)
		del row
	del layer
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

	#if validation_survey:
	if validation:
		print "Validation needed for " + surveyName + " will export to Excel"
		arcpy.AddMessage("Validation needed for " + surveyName + " will export to Excel")
		for fc in surveyfc:
			print fc
			if arcpy.Exists(conn + "\\" + fc):
				arcpy.AddMessage("Feature Class Exists: " + fc)
				print "Feature Class Exists"
				arcpy.env.workspace = conn
				RowsToDelete = getExistingRecords(conn + "\\" + fc)
				arcpy.env.workspace = extracted_gdb
				DeleteExistingRows(extracted_gdb + "\\"+ fc, RowsToDelete)
				arcpy.AddField_management(fc, "X_Coord", "DOUBLE")
				arcpy.AddField_management(fc, "Y_Coord", "DOUBLE")
				arcpy.CalculateField_management(fc, "X_Coord", "!SHAPE!.firstPoint.X", "PYTHON_9.3")
				arcpy.CalculateField_management(fc, "Y_Coord", "!SHAPE!.firstPoint.Y", "PYTHON_9.3")
				arcpy.TableToExcel_conversion(fc, CSVLocation + '\\' + fc + ".xls")
				#arcpy.Append_management(fc, conn + "\\" + sde_fc, "NO_TEST")
				for table in surveytable:
					if arcpy.Exists(conn + "\\" + table):
						arcpy.TableToExcel_conversion(fc, CSVLocation + '\\' + table + ".xls")
			else:
				print "Feautre Class Does not Exists"
				arcpy.AddMessage("Feature Class Does Not Exists: " + fc)
				arcpy.AddMessage("Feature Class: " + fc + " not found.  Exporting to Excel.  Schema will be created upon uploading...")
				arcpy.Copy_management(fc, conn + "\\" + fc)
				arcpy.TableToExcel_conversion(fc, CSVLocation + '\\' + fc + ".xls")
	
	#if no_validation_survey:
	if not validation:
		print "No validation needed for " + surveyName
		arcpy.AddMessage("No validation needed for " + surveyName)
		
		for fc in surveyfc:
			if arcpy.Exists(conn + "\\" + fc):
				print "Feature Class Exists"
				arcpy.env.workspace = conn
				RowsToDelete = getExistingRecords(conn + "\\" + fc)
				arcpy.env.workspace = extracted_gdb
				DeleteExistingRows(extracted_gdb + "\\"+ fc, RowsToDelete)
				print "Appending remaining rows..."
				arcpy.Append_management(fc, conn + "\\" + fc, "NO_TEST")
				
				for table in surveytable:
					if arcpy.Exists(conn + "\\" + table):
						print "Table already exists: " + table
						arcpy.Append_management(table, conn + "\\" + table, "NO_TEST")
			else:
				print "Feautre Class Does not Exists"
				arcpy.AddMessage("Feature Class: " + fc + " not found.")
				arcpy.Copy_management(extracted_gdb + "\\"+ fc, conn + "\\" + surveyName)

		
				#have to find how to handle this
	return


if __name__ == '__main__':

	#Delete\Recreate Temp Directory
	shutil.rmtree(wksp + "\\Temp\\")
	os.makedirs(wksp + "\\Temp\\")

	token = getToken(username, password)
	itemdict, layers = getItems(token)
	getReplica(token, itemdict, layers)

	ProcessReplica(conn)
	
