import arcpy

# CSVFile = r'C:\Data\IOM\RoundIISurvey.xls'
# conn = r'C:\Data\IOM\IOM.sde'
# surveyName = "RoundIISurvey"
# FeatureClass = True


surveyName = arcpy.GetParameterAsText(0)
CSVFile = arcpy.GetParameterAsText(1)

if FeatureClass == "false":
	FeatureClass = False 
elif FeatureClass == "true":
	FeatureClass == True

#FeatureClass = arcpy.GetParameterAsText(1)
#conn = arcpy.GetParameterAsText(0)
wksp = r'C:\Data\IOM'

def  upLoadFile(file):

	table = wksp + "\\Temp\\CSV_To_Table.gdb\\"  + surveyName
	xyeventlyr = table + "XY"
	outfc = table + "FC"

	arcpy.CreateFileGDB_management(wksp + "\\Temp", "CSV_To_Table.gdb")
	if FeatureClass:
		print "Found Something"
		arcpy.ExcelToTable_conversion(CSVFile, table, "RoundIISurvey")
		#may still need to handle field type here
		arcpy.MakeXYEventLayer_management(table, "X_Coord", "Y_Coord", xyeventlyr)
		arcpy.FeatureClassToFeatureClass_conversion(xyeventlyr, wksp + "\\Temp\\CSV_To_Table.gdb", surveyName + "FC")
	else:
		arcpy.ExcelToTable_conversion(CSVFile, wksp + "\\Temp\\CSV_To_Table.gdb\\"+ surveyName, "RoundIISurvey")
	return outfc

def ProcessExcel(conn,table):
	sdefc = conn + "\\" + surveyName

	#May need to find a way to handle Geometry

	if arcpy.Exists(conn + "\\" + surveyName):
		arcpy.Append_management(table, sdefc, "NO_TEST")

	return

if __name__ == '__main__':
	table = upLoadFile(CSVFile)
	ProcessExcel(conn, table)
