import arcpy

# FLAGS_FC = r'C:\Data\IOM\IOM.sde\IOM.DBO.Flags'
# surveyName = "RoundIISurvey"
# conn = r'C:\Data\IOM\IOM.sde'

FLAGS_FC = arcpy.GetParameterAsText(0)
surveyName = arcpy.GetParameterAsText(1)
conn = arcpy.GetParameterAsText(2)




def getValues(conn):
	arcpy.env.workspace = conn
	fc = surveyName

	fields = arcpy.ListFields(fc)
	rows = arcpy.SearchCursor(fc)

	edit = arcpy.da.Editor(conn)
	edit.startEditing(True)
	edit.startOperation()

	for row in rows:
		#Loop Thru Each row and 
		RowValues = {}
		for field in fields:
			#if flags come back need to raise them
			RowValues[field.name[:12]] = row.getValue(field.name)

		rowid = row.getValue("ROWID")
		flags = RaiseFlags(RowValues)

		if not flags:
			print "No Flags Raised by Row"
		else:

			da_rows = arcpy.da.SearchCursor(fc, ["ROWID","SHAPE@XY"])
			for da_row in da_rows:
				if da_row[0] == rowid:
					for flag in flags:
						#insertrow = ["FlagID", "SiteID", "SurveyID", "FlagType", "Status", "ResolutionDate", "SHAPE@XY"]
						#insertvalues = [None, None, rowid, flag, "Open",  "null" , da_row[1]]
						insertrow = ["SurveyID", "FlagType", "Status","SHAPE@XY"]
						insertvalues = [rowid, int(flag), 1, da_row[1]]
						insert_cursor = arcpy.da.InsertCursor(FLAGS_FC, insertrow)
						insert_cursor.insertRow(insertvalues)
					del insert_cursor
			del da_rows
	del rows
	edit.stopOperation()
	edit.stopEditing(True)
	return

def RaiseFlags(RowData):

	print "About to print keys..."
	FlagList = []


	if RowData["F__1_2_c_1__"] in ("2__no", "3__unknown", "4__no_answer") and RowData["F__2_1_a_1__"] > 100:
		print "CM_FLAG_1"
		#FlagList.append("CM Flag 1")
		FlagList.append(1)

	if RowData["F__1_3_c_1__"] == "1__school":
		print "CM_FLAG_2"
		#FlagList.append("CM Flag 2")
		FlagList.append(2)

	if RowData["F__1_3_c_1__"] == "1__school" and RowData["F__1_2_c_1__"] in ("2__no", "3__unknown", "4__no_answer") and RowData["F__2_1_a_1__"] > 100:
		print "CM_FLAG_3"
		#FlagList.append("CM Flag 3")
		FlagList.append(4)

	if RowData["F__2_1_a_1__"] > 100:
		print "SHELTER_FLAG_1"
		#FlagList.append("Shelter Flag 1")
		FlagList.append(8)

	if RowData["F__1_3_c_1__"] == "1__school":
		print "SHELTER_FLAG_2"
		#FlagList.append("Shelter Flag 2")
		FlagList.append(16)
	# if RowData["F__2_1_a_1__"] > 100 and RowData["F__1_6_c_1__"] != None:
	# 	print "SHELTER_FLAG_3"
	# if RowData["F__2_1_a_1__ "] > 100 and RowData["F__3_2_b__"] == "1__none":
 # 		print "SHELTER_FLAG_4"
 # 	#Keep an eye on this guy
 # 	if RowData["F__4_3_a__1_"] == "1__yes" and RowData["F__2_1_a_1__"] > 100:
	# 	print "WASH_FLAG_1"
	# if RowData["F__4_1_a_1__"] == "3__off-site_(<20_minutes)" or RowData["F__4_1_a_1__"] == "4__off-site_(>20_minutes)") and RowData["F__2_1_a_1__"] > 100:
	# 	print "WASH_FLAG_2"
	# if RowData["F__4_4_a_1__"] / RowData["F__2_1_a_1__"] > 1/50:
	# 	print "WASH_FLAG_3"
	# if RowData["F__4_8_e__"] == "1_yes" and RowData["F__2_1_a_1__"] >100:
	# 	print "WASH_FLAG_4"
	# if RowData["F__4_4_b_1__"] in ("2__no","3__unknown", "4__no_answer") and RowData["F__10_1_s_1__"] in ("2__yes,_there_is_lighting_but_i" , "3__no_lighting"):
	# 	print "WASH_FLAG_5"
	# if RowData["F__7_2_b_1__"]  in ("5__none", "7__unknown", "8__no_answer")  and RowData["F__7_2_e__"] == "2_no" and RowData["F__2_1_a_1__"] > 100 and RowData["F__7_1_b_1__"] is not None:
	# 	print "HEALTH_FLAG_1"
	# if RowData["F__10_1_a_2__"] in ("2__no", "3__unknown", "4__no_answer") and RowData["F__2_1_a_1__"] > 100:
	# 	print "HEALTH_FLAG_2"
	# if RowData["F__10_1_e_1__"] == "1__yes" and RowData["F__10_1_a_2__"] in ("2__no", "3__unknown", "4__no_answer"):
	# 	print "PROTECTION_FLAG_1"
	# if  RowData["F__10_1_a_2__"] in ("2__no", "3__unknown", "4__no_answer") and RowData["F__2_1_a_1__"] > 100:
	# 	print "PROTECTION_FLAG_2"
	return FlagList

if __name__ == '__main__':
	print "Starting Flags FC"
	getValues(conn)