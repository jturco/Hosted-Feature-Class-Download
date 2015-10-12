import arcpy

CSVFile = r'C:\Data\IOM'
conn = r'C:\Data\IOM\IOM.sde'
wksp = wksp = r'C:\Data\IOM\Temp'

def  upLoadFile(file):

	#Create Geodatabase

	#Table to Table on Excel file put in GDB



	return

def ProcessExcel(table):

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

	#Use same cleaning mechanism

	#Append leftover records to GEODatabase
	return

if __name__ == '__main__':
	upLoadFile(CSVFile)
