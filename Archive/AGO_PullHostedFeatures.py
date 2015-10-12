import os, urllib, urllib2, datetime, arcpy, json


## ============================================================================== ##
## function to update a field - basically converts longs to dates for date fields ##
## since json has dates as a long (milliseconds since unix epoch) and geodb wants ##
## a proper date, not a long.
## ============================================================================== ##
def updateValue(row,field_to_update,value):
    outputfield=next((f for f in fields if f.name ==field_to_update),None)  #find the output field
    if outputfield == None or value == None:        #exit if no field found or empty (null) value passed in
        return
    if outputfield.type == 'Date':
        if value > 0 :                                            # filter "zero" dates
            value = datetime.datetime.fromtimestamp(value/1000)   # convert to date - this is local time, to use utc time
            row.setValue(field_to_update,value)                   # change "fromtimestamp" to "utcfromtimestamp"
    else:
        row.setValue(field_to_update,value)
    return
## ============================================================================== ##

### Generate Token ###
gtUrl = 'https://www.arcgis.com/sharing/rest/generateToken'
gtValues = {'username' : 'jturco_DBS',
'password' : 'shannon1717',
'referer' : 'http://www.arcgis.com',
'f' : 'json' }
gtData = urllib.urlencode(gtValues)
gtRequest = urllib2.Request(gtUrl, gtData)
gtResponse = urllib2.urlopen(gtRequest)
gtJson = json.load(gtResponse)
token = gtJson['token']

### Create Replica ###
### Update service url HERE ###
crUrl = 'http://services1.arcgis.com/g2TonOxuRkIqSOFx/arcgis/rest/services/service_658c48f270124e5f9cf5d4ab2cca77dc/FeatureServer/CreateReplica'

crValues = {'f' : 'json',
'layers' : '0,1,2',
'returnAttachments' : 'false',
'syncModel' : 'none',
'dataFormat': 'filegdb',
'token' : token }
crData = urllib.urlencode(crValues)
crRequest = urllib2.Request(crUrl, crData)
crResponse = urllib2.urlopen(crRequest)
crJson = json.load(crResponse)
print crJson
replicaUrl = crJson['responseUrl']
print replicaUrl
urllib.urlretrieve(replicaUrl, 'c:\data\IOM\Temp\download.zip')

### Get Attachment ###
cwd = os.getcwd()
with open('myLayer.json') as data_file:
    data = json.load(data_file)

# for x in data['layers'][0]['attachments']:
#     gaUrl = x['url']
#     gaFolder = cwd + '\\photos\\' + x['parentGlobalId']
#     if not os.path.exists(gaFolder):
#         os.makedirs(gaFolder)
#     gaName = x['name']
#     gaValues = {'token' : token }
#     gaData = urllib.urlencode(gaValues)
#     urllib.urlretrieve(url=gaUrl + '/' + gaName, filename=os.path.join(gaFolder, gaName),data=gaData)

### Create Features ###

rows = arcpy.InsertCursor(cwd + '/data.gdb/myLayer')
fields = arcpy.ListFields(cwd + '/data.gdb/myLayer')

for cfX in data['layers'][0]['features']:
    pnt = arcpy.Point()
    pnt.X = cfX['geometry']['x']
    pnt.Y = cfX['geometry']['y']
    row = rows.newRow()
    row.shape = pnt

    ### Set Attribute columns HERE ###
    ## makes use of the "updatevalue function to deal with dates ##

    updateValue(row,'Field1', cfX['attributes']['Field1'])
    updateValue(row,'Field2', cfX['attributes']['Field2'])
    updateValue(row,'Field3', cfX['attributes']['Field3'])
    updateValue(row,'Field4', cfX['attributes']['Field4'])
    # leave GlobalID out - you cannot edit this field in the destination geodb

    #comment out below fields if you don't have them in your online or destination geodb (editor tracking)
    updateValue(row,'CreationDate', cfX['attributes']['CreationDate'])
    updateValue(row,'Creator', cfX['attributes']['Creator'])
    updateValue(row,'EditDate', cfX['attributes']['EditDate'])
    updateValue(row,'Editor', cfX['attributes']['Editor'])

    updateValue(row,'GlobalID_str', cfX['attributes']['GlobalID'])

    rows.insertRow(row)

del row
del rows

### Add Attachments ###
### Create Match Table ###
rows = arcpy.InsertCursor(cwd + '/data.gdb/MatchTable')

for cmtX in data['layers'][0]['attachments']:
    row = rows.newRow()

    row.setValue('GlobalID_Str', cmtX['parentGlobalId'])
    row.setValue('PhotoPath', cwd + '\\photos\\' + cmtX['parentGlobalId'] + '\\' + cmtX['name'])

    rows.insertRow(row)

del row
del rows

### Add Attachments ###
arcpy.AddAttachments_management(cwd + '/data.gdb/myLayer', 'GlobalID_Str', cwd + '/data.gdb/MatchTable', 'GlobalID_Str', 'PhotoPath')