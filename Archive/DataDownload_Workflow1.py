import os, shutil, zipfile, glob
import urllib, urllib2, datetime, arcpy, json

##Config##
username='jturco_DBS'
password='shannon1717'
itemid  = 'a5795596bbbb4ee28106d821e62865a8'
wksp = r'C:\Data\IOM'
conn = r'C:\Data\IOM\IOM.sde'

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

def getItems():
	return

def getReplica(token, itemid):

	crUrl = 'http://services1.arcgis.com/g2TonOxuRkIqSOFx/arcgis/rest/services/service_e0e0cde7356549138e6b82d078b3b5c0/FeatureServer/CreateReplica'
	crValues = {
	'f' : 'json',
	'layers' : '0,1,2',
	'returnAttachments' : 'false',
	'syncModel' : 'none',
	'dataFormat': 'filegdb',
	'token' : token
	}

	crData = urllib.urlencode(crValues)
	crRequest = urllib2.Request(crUrl, crData)
	crResponse = urllib2.urlopen(crRequest)
	crJson = json.load(crResponse)
	replicaUrl = crJson['responseUrl']
	print "Downloading and unzipping Fgdb"
	zippedfile = wksp + "\\Temp\\" + itemid + ".zip"
	urllib.urlretrieve(replicaUrl, zippedfile)
	zip_ref = zipfile.ZipFile(zippedfile, 'r')
	zip_ref.extractall("c:\data\IOM\Temp\\")
	zip_ref.close()

	return

def ProcessReplica(conn):
 

	surveyname = None
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
		for field in fields:
			if len(field.name) > 29:
				print "Trimming field over 29 characters"
				newname = field.name[:-2]
				arcpy.AlterField_management(fc, field.name, newname)
		
		arcpy.env.workspace = conn
		gdbtables = arcpy.ListTables()
		gdbfcs = arcpy.ListFeatureClasses()

		if not gdbfcs:
			sdefc = conn + "\\" + fc
			arcpy.Copy_management(fgdbfc, sdefc)
		else:
			for gfc in gdbfcs:
				sdefc = sdeenv + "\\" + gfc
				if fc == gfc[8:]:
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
					arcpy.Copy_management(fgdbfc, sdefc)

	return

#Parse ArcGIS Online Items/Folder for downloadable content

#Download the content thru create Replica workflow

#Decide whether or not we need to create a new table in Enterprise GDB
	#if we do then just export FC's and table to GDB
	#if we do not then we need to compare and add records


if __name__ == '__main__':

	#Delete\Recreate Temp Directory
	shutil.rmtree(wksp + "\\Temp\\")
	os.makedirs(wksp + "\\Temp\\")

	token = getToken(username, password)
	getReplica(token, itemid)
	ProcessReplica(conn)
