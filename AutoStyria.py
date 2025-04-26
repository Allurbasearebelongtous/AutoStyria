from phBot import *
from threading import Thread
from threading import Timer
from enum import Enum
from time import sleep
from datetime import datetime, timedelta
import asyncio
import time
import threading
import QtBind
import struct
import random
import json
import os
import webbrowser
from binascii import hexlify  # for debugging

pName = 'AutoStyria'
logPrefix = pName + '-plugin: '
pVersion = '1.0.1'
pUrl = 'https://github.com/Allurbasearebelongtous/AutoStyria'
pUrlEnglish = 'https://github.com/Allurbasearebelongtous/AutoStyria/wiki'
pUrlTurkish = 'https://github.com/Allurbasearebelongtous/AutoStyria/wiki/Bilgiler'
glb_char_data = None
glb_training_profile = None
glb_registered_for_styria = False
glb_styria_started = False

# Global event to control the stop condition
glb_stop_event = threading.Event()
glb_thread_started = False
glb_thread_lock = threading.Lock()

#______________________________ENUMS________________________________________#
class JobItemStatus(str,Enum):
    NOT_EQUIPPED = 1
    EQUIPPED = 2
    EQUIP_INPROGRESS = 3

class REGION(Enum):
	BAGDAD_TOWN = 22618
	ALEXS_TOWN = 23088
	ALEXN_TOWN = 23603
	HOTAN_TOWN = 23687
	JANGAN_TOWN = 25000
	DW_TOWN = 26265
	CONST_TOWN = 26959
	SAMARKAND_TOWN = 27244
	STYRIA_A1 = 31985
	STYRIA_A2 = 31986
	STYRIA_B1 = 32241
	STYRIA_B2 = 32242

class CONDITION_DAY_TYPE(Enum):
	SUNDAY = 75
	MONDAY = 76
	TUESDAY = 77
	WEDNESDAY = 78
	THURSDAY = 79
	FRIDAY =  80
	SATURDAY = 81
	
FRM_TELEPORT_TO_NPC = {
    REGION.BAGDAD_TOWN: '''terminate,transport
wait,2000
walk,-8530,-734,-236
wait,5000
teleport,Baghdad,Alexandria (South)
wait,5000
walk,-16633,-324,863
walk,-16628,-304,864
walk,-16627,-297,862
''',
    REGION.ALEXS_TOWN: '''terminate,transport
wait,2000
walk,-16633,-324,863
walk,-16628,-304,864
walk,-16627,-297,862
''',
    REGION.ALEXN_TOWN: '''terminate,transport
wait,2000
walk,-16119,51,1537
walk,-16127,58,1531
wait,5000
teleport,Alexandria (North),Alexandria (South)
wait,5000
walk,-16633,-324,863
walk,-16628,-304,864
walk,-16627,-297,862
''',
    REGION.HOTAN_TOWN: '''terminate,transport
wait,2000
walk,117,21,244
walk,122,29,244
walk,127,41,244
walk,127,48,244
''',
    REGION.JANGAN_TOWN: '''terminate,transport
wait,2000
walk,6434,1093,-32
walk,6429,1086,-32
walk,6424,1073,-32
walk,6421,1059,-32
walk,6419,1050,-32
''',
    REGION.DW_TOWN: '''terminate,transport
wait,2000
walk,3549,2071,-106
walk,3549,2083,-106
''',
    REGION.CONST_TOWN: '''terminate,transport
wait,2000
walk,-10659,2606,83
walk,-10669,2612,83
walk,-10683,2614,83
walk,-10696,2612,83
walk,-10703,2605,83
walk,-10710,2592,83
''',
    REGION.SAMARKAND_TOWN: '''terminate,transport
wait,2000
walk,-5155,2832,180
walk,-5151,2859,180
walk,-5149,2879,180
'''
}

# ______________________________ Initializing ______________________________ #
gui = QtBind.init(__name__,pName)

gui_window_padding_x = 30
gui_window_padding_y = 70
gui_checkbox_padding_y = 20

gui_ignore_unequip_x = gui_window_padding_x
gui_ignore_unequip_y = gui_window_padding_y + gui_window_padding_y

gui_disable_x = gui_ignore_unequip_x
gui_disable_y = gui_ignore_unequip_y + gui_checkbox_padding_y

gui_allow_disconnect_x = gui_disable_x
gui_allow_disconnect_y = gui_disable_y + gui_checkbox_padding_y

gui_allow_register_x = gui_allow_disconnect_x
gui_allow_register_y = gui_allow_disconnect_y + gui_checkbox_padding_y

gui_registerTimeLabel_x = 340
gui_registerTimeLabel_y = 100
gui_registerTimeLine_x = gui_registerTimeLabel_x + 115
gui_registerTimeLine_y = gui_registerTimeLabel_y - 5

gui_preparationTimeLabel_x = gui_registerTimeLabel_x
gui_preparationTimeLabel_y = gui_registerTimeLine_y + gui_checkbox_padding_y * 2
gui_preparationTimeLine_x = gui_registerTimeLine_x
gui_preparationTimeLine_y = gui_preparationTimeLabel_y

gui_register_x = gui_registerTimeLabel_x
gui_register_y = gui_preparationTimeLine_y + 50

gui_day1_label_x = 580
gui_day1_label_y = 90

gui_day2_label_x = 650
gui_day2_label_y = 90

gui_day_mon_y = gui_day1_label_y + gui_checkbox_padding_y
gui_day_tue_y = gui_day_mon_y + gui_checkbox_padding_y
gui_day_wed_y = gui_day_tue_y + gui_checkbox_padding_y
gui_day_thu_y = gui_day_wed_y + gui_checkbox_padding_y
gui_day_fri_y = gui_day_thu_y + gui_checkbox_padding_y
gui_day_sat_y = gui_day_fri_y + gui_checkbox_padding_y
gui_day_sun_y = gui_day_sat_y + gui_checkbox_padding_y

QtBind.createLabel(gui,'AutoStyria plugin handles your char to return town, leave party, equip job item and walk to Arena NPC and register to styria!',10, 20)
QtBind.createLabel(gui,'Once styria ends,the plugin unequips job item (if required), disconnect (to recover shard fatigue) or change back to your profile to continue botting',10, 40)

QtBind.createLabel(gui, 'Information Page (Bilgi Sayfasi)',  10, 70)
gui_guideEng = QtBind.createButton(gui,'OpenGuidePageEng',"English!",10,85)
gui_guideTurkish = QtBind.createButton(gui,'OpenGuidePageTurkish',"Turkish",85,85)


gui_ignore_unequip_jobItem_chkBox = QtBind.createCheckBox(gui, 'cbxAuto_clicked','ignore unequpping job item ', gui_ignore_unequip_x, gui_ignore_unequip_y)
gui_disable_plugin_chkBox = QtBind.createCheckBox(gui, 'cbxAuto_clicked','disable plugin ', gui_disable_x, gui_disable_y)
gui_allow_disconnect_chkBox = QtBind.createCheckBox(gui, 'cbxAuto_clicked','disconnect after styria complete ', gui_allow_disconnect_x, gui_allow_disconnect_y)
gui_allow_register_chkBox = QtBind.createCheckBox(gui, 'cbxAuto_clicked','let plugin register to styria ', gui_allow_register_x, gui_allow_register_y)

gui_registerTimeLabel = QtBind.createLabel(gui,'register at:',gui_registerTimeLabel_x, gui_registerTimeLabel_y)
gui_registerTimeLine = QtBind.createLineEdit(gui,"22:00",gui_registerTimeLine_x,gui_registerTimeLine_y,50,20)

gui_prepareTimeInfoLabel = QtBind.createLabel(gui,'preperation will start at',gui_preparationTimeLabel_x, gui_preparationTimeLabel_y)
gui_prepareTimeLabel = QtBind.createLabel(gui,"21:50",gui_preparationTimeLine_x,gui_preparationTimeLine_y)

QtBind.createLabel(gui, 'Generate conditions and jsons.', gui_register_x, gui_register_y)
QtBind.createLabel(gui, 'Beware!This will add conditions to current profile.', gui_register_x, gui_register_y + 20)
QtBind.createButton(gui, 'generate_autostyria_conditions', 'Generate', gui_register_x, gui_register_y + 40)

QtBind.createLabel(gui, 'Styria Day 1',  gui_day1_label_x, gui_day1_label_y)
QtBind.createLabel(gui, 'Styria Day 2',  gui_day2_label_x, gui_day2_label_y)
gui_day1_checkbox_mon = QtBind.createCheckBox(gui, 'cbxMon_clicked','Mon', gui_day1_label_x, gui_day_mon_y)
gui_day1_checkbox_tue = QtBind.createCheckBox(gui, 'cbxTue_clicked','Tue', gui_day1_label_x, gui_day_tue_y)
gui_day1_checkbox_wed = QtBind.createCheckBox(gui, 'cbxWed_clicked','Wed', gui_day1_label_x, gui_day_wed_y)
gui_day1_checkbox_thu = QtBind.createCheckBox(gui, 'cbxThu_clicked','Thur', gui_day1_label_x, gui_day_thu_y)
gui_day1_checkbox_fri = QtBind.createCheckBox(gui, 'cbxFri_clicked','Fri', gui_day1_label_x, gui_day_fri_y)
gui_day1_checkbox_sat = QtBind.createCheckBox(gui, 'cbxSat_clicked','Sat', gui_day1_label_x, gui_day_sat_y)
gui_day1_checkbox_sun = QtBind.createCheckBox(gui, 'cbxSun_clicked','Sun', gui_day1_label_x, gui_day_sun_y)

gui_day2_checkbox_mon = QtBind.createCheckBox(gui, 'cbxMonb_clicked','Mon', gui_day2_label_x, gui_day_mon_y)
gui_day2_checkbox_tue = QtBind.createCheckBox(gui, 'cbxTueb_clicked','Tue', gui_day2_label_x, gui_day_tue_y)
gui_day2_checkbox_wed = QtBind.createCheckBox(gui, 'cbxWedb_clicked','Wed', gui_day2_label_x, gui_day_wed_y)
gui_day2_checkbox_thu = QtBind.createCheckBox(gui, 'cbxThub_clicked','Thur', gui_day2_label_x, gui_day_thu_y)
gui_day2_checkbox_fri = QtBind.createCheckBox(gui, 'cbxFrib_clicked','Fri', gui_day2_label_x, gui_day_fri_y)
gui_day2_checkbox_sat = QtBind.createCheckBox(gui, 'cbxSatb_clicked','Sat', gui_day2_label_x, gui_day_sat_y)
gui_day2_checkbox_sun = QtBind.createCheckBox(gui, 'cbxSunb_clicked','Sun', gui_day2_label_x, gui_day_sun_y)

btnLoadConfig = QtBind.createButton(gui,'LoadConfig',"   load config    ",gui_window_padding_x,280)
btnSaveConfig = QtBind.createButton(gui,'SaveConfigIfJoined',"   save config    ",gui_window_padding_x + 100,280)

glb_checkbox_by_day1 = {
    CONDITION_DAY_TYPE.MONDAY: gui_day1_checkbox_mon,
    CONDITION_DAY_TYPE.TUESDAY: gui_day1_checkbox_tue,
    CONDITION_DAY_TYPE.WEDNESDAY: gui_day1_checkbox_wed,
    CONDITION_DAY_TYPE.THURSDAY: gui_day1_checkbox_thu,
    CONDITION_DAY_TYPE.FRIDAY: gui_day1_checkbox_fri,
    CONDITION_DAY_TYPE.SATURDAY: gui_day1_checkbox_sat,
    CONDITION_DAY_TYPE.SUNDAY: gui_day1_checkbox_sun
}

glb_checkbox_by_day2 = {
    CONDITION_DAY_TYPE.MONDAY: gui_day2_checkbox_mon,
    CONDITION_DAY_TYPE.TUESDAY: gui_day2_checkbox_tue,
    CONDITION_DAY_TYPE.WEDNESDAY: gui_day2_checkbox_wed,
    CONDITION_DAY_TYPE.THURSDAY: gui_day2_checkbox_thu,
    CONDITION_DAY_TYPE.FRIDAY: gui_day2_checkbox_fri,
    CONDITION_DAY_TYPE.SATURDAY: gui_day2_checkbox_sat,
    CONDITION_DAY_TYPE.SUNDAY: gui_day2_checkbox_sun
}
# ______________________________ logger ______________________________ #
def LogMsg(logstr):
	log(logPrefix + logstr)

def OpenGuidePageEng():
	webbrowser.open(pUrlEnglish)

def OpenGuidePageTurkish():
	webbrowser.open(pUrlTurkish)
#_______________________________Gui methods__________________________________#

#sadly, callback returns true or false and not the insance of the checkbox hence we need to create this gazillion callbacks.
def disable_all_except(active_day_enum, checkbox_by_day1):
    for day_enum, checkbox in checkbox_by_day1.items():
        QtBind.setChecked(gui, checkbox, day_enum == active_day_enum)

#day1
def cbxMon_clicked(checked):
	if checked:
		disable_all_except(CONDITION_DAY_TYPE.MONDAY, glb_checkbox_by_day1)

def cbxTue_clicked(checked):
    if checked:
        disable_all_except(CONDITION_DAY_TYPE.TUESDAY, glb_checkbox_by_day1)
		

def cbxWed_clicked(checked):
    if checked:
        disable_all_except(CONDITION_DAY_TYPE.WEDNESDAY, glb_checkbox_by_day1)

def cbxThu_clicked(checked):
    if checked:
        disable_all_except(CONDITION_DAY_TYPE.THURSDAY, glb_checkbox_by_day1)

def cbxFri_clicked(checked):
    if checked:
        disable_all_except(CONDITION_DAY_TYPE.FRIDAY, glb_checkbox_by_day1)

def cbxSat_clicked(checked):
    if checked:
        disable_all_except(CONDITION_DAY_TYPE.SATURDAY, glb_checkbox_by_day1)

def cbxSun_clicked(checked):
    if checked:
        disable_all_except(CONDITION_DAY_TYPE.SUNDAY, glb_checkbox_by_day1)

#day2
def cbxMonb_clicked(checked):
    if checked:
        disable_all_except(CONDITION_DAY_TYPE.MONDAY, glb_checkbox_by_day2)

def cbxTueb_clicked(checked):
    if checked:
        disable_all_except(CONDITION_DAY_TYPE.TUESDAY, glb_checkbox_by_day2)

def cbxWedb_clicked(checked):
    if checked:
        disable_all_except(CONDITION_DAY_TYPE.WEDNESDAY, glb_checkbox_by_day2)

def cbxThub_clicked(checked):
    if checked:
        disable_all_except(CONDITION_DAY_TYPE.THURSDAY, glb_checkbox_by_day2)

def cbxFrib_clicked(checked):
    if checked:
        disable_all_except(CONDITION_DAY_TYPE.FRIDAY, glb_checkbox_by_day2)

def cbxSatb_clicked(checked):
    if checked:
        disable_all_except(CONDITION_DAY_TYPE.SATURDAY, glb_checkbox_by_day2)

def cbxSunb_clicked(checked):
    if checked:
        disable_all_except(CONDITION_DAY_TYPE.SUNDAY, glb_checkbox_by_day2)

def validate_time_string(time_str):
    try:
        time.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        LogMsg(f"❌ Invalid time format: '{time_str}'. Expected format is HH:MM.")
        return False


#________________________________profile.Json file generation___________________________#
# Helper: Convert HH:MM to total minutes
def time_to_minutes(tstr):
    t = time.strptime(tstr, "%H:%M")
    return t.tm_hour * 60 + t.tm_min

# Helper: Convert total minutes to HH:MM
def minutes_to_time_str(minutes):
	minutes = minutes % (24 * 60)  # wrap around after 1440 minutes
	hours = minutes // 60
	mins = minutes % 60
	return f"{hours:02}:{mins:02}"

def make_entry_condition(day_enum, time_start, enabled):
    return {
        "Enabled": enabled,
        "if": [
            {"if": day_enum.value, "op": 2, "value_1": "", "value_2": ""},
            {"if": 47, "op": 1, "value_1": time_start, "value_2": ""},
			{"if": 58, "op": 2, "value_1": "", "value_2": ""}, #not botting
			{"if": 59, "op": 2, "value_1": "", "value_2": ""}, #not tracing
			{"if": 52, "op": 2, "value_1": "", "value_2": ""}, #not equipped job
        ],
        "then": [
            {"then": 17, "value": "autostyria_register", "value_2": ""},
			{"then": 74, "value": "", "value_2": ""}
        ]
    }

def make_preparation_condition(day_enum, time_str,time_end, enabled):
    return {
        "Enabled": enabled,
        "if": [
            {"if": day_enum.value, "op": 2, "value_1": "", "value_2": ""},
            {"if": 47, "op": 1, "value_1": time_str, "value_2": ""},
            {"if": 47, "op": 4, "value_1": time_end, "value_2": ""}
        ],
        "then": [
            {"then": 17, "value": "autostyria_prepare", "value_2": ""}
        ]
	}

def has_autostyria_condition(conditions):
    for cond in conditions:
        for action in cond.get("then", []):
            if "autostyria" in action.get("value"):
                return True
    return False

def remove_autostyria_conditions(conditions):
    return [
        cond for cond in conditions
        if not any( "autostyria" in action.get("value") for action in cond.get("then", []))
    ]

def get_selected_day(checkbox_by_day):
    for day, checkbox in checkbox_by_day.items():
        if QtBind.isChecked(gui, checkbox):
            return day
    return None  # If no checkbox is selected

#preparation can happen if the bot logs in after the registration time.
#or if there is not enough time to prepare before the registration time.
#this function handles these edge cases to ensure there is always enough time for preperations!
def update_registration_time_conditions(conditions, start_delay_minutes=5):
	now_struct = time.localtime()
	now_minutes = now_struct.tm_hour * 60 + now_struct.tm_min
	# Read threshold from GUI and convert to minutes
	threshold_str = QtBind.text(gui, gui_registerTimeLine)
	threshold_struct = time.strptime(threshold_str, "%H:%M")
	threshold_minutes = threshold_struct.tm_hour * 60 + threshold_struct.tm_min
	# Decide the new start time
	if now_minutes < (threshold_minutes - start_delay_minutes): #if we have enough time use the current settings
		start_time = threshold_str
	else:
		# Add 5 minutes and convert back to "HH:MM"
		new_minutes = (now_minutes + 5) % (24 * 60) #need to move forward the registration time to get enough preperation time.
		hour = new_minutes // 60
		minute = new_minutes % 60
		start_time = f"{hour:02d}:{minute:02d}"

    # Update all 47-type conditions
	for condition in conditions:
		if "if" in condition:
			for condition_if in condition["if"]:
				condition_if["value_1"] = start_time

def enable_autostyria_registration_conditions(conditions, is_enabled):
		for condition in conditions:
			condition["Enabled"] = is_enabled

def get_preperation_start_timestr(timestr, before_minutes):
	time = time_to_minutes(timestr) - before_minutes
	time_str = minutes_to_time_str(time)
	return time_str

def get_preperation_end_timestr(timestr, after_minutes):
	time = time_to_minutes(timestr) + after_minutes
	time_str = minutes_to_time_str(time)
	return time_str

def generate_autostyria_conditions():
	entry_time_start = QtBind.text(gui,gui_registerTimeLine)
	if(not validate_time_string(entry_time_start)):
		return

	# start time for preperation. (10 min before the registration starts)
	preparation_time_start = get_preperation_start_timestr(entry_time_start, 10)

	# end time for preperation. (5 min before the registration ends AKA 40 min after the preperation starts)
	# note the reason we have this 40 min gap because even if a bot enters to game world after 
	# the styria registration starts, it can still try to register. 
	preparation_time_end = get_preperation_end_timestr(preparation_time_start, 40)
	QtBind.setText(gui, gui_prepareTimeLabel, preparation_time_start)

	glb_training_profile = get_profile() #store current profile to be recovered later once styria ends.
	LogMsg(str(glb_training_profile))
	configDirectory = get_config_dir()
	LogMsg(str(configDirectory))
	original_profile_json = get_config_path()
	LogMsg(str(original_profile_json))
	character_data = get_character_data()
	autostyria_profile_json = configDirectory + character_data['server'] + "_" + character_data['name'] + "." + pName + ".json"
	
	# Load the original JSON data
	with open(original_profile_json, 'r', encoding='utf-8') as file:
		original_data = json.load(file)

	#check if the currentprofile is already containing autostyria post fix
	if(glb_training_profile == pName):
		LogMsg("❌ Your training profile is same as the AutoStyria profile! This profile should only be used by the plugin!")
		LogMsg("Check your current profile under Auto Configure tab in the bot!")
		return
	
	day1 = get_selected_day(glb_checkbox_by_day1)
	day2 = get_selected_day(glb_checkbox_by_day2)
    # Define the prepare conditions.
	if (day1 is not None):
		prep_condition_day1 = make_preparation_condition(day1, preparation_time_start,preparation_time_end, True)
		entry_condition_day1 = make_entry_condition(day1, entry_time_start, False)
	    #complete_condition_day1 = make_complete_condition(CONDITION_DAY_TYPE.FRIDAY, completion_time, False)
	else:
		LogMsg("❌ No valid date is selected for Syria day 1")
		return

	if (day2 is not None):
		prep_condition_day2 = make_preparation_condition(day2, preparation_time_start,preparation_time_end, True)
		entry_condition_day2 = make_entry_condition(day2, entry_time_start, False)
	    #complete_condition_day2 = make_complete_condition(CONDITION_DAY_TYPE.SATURDAY, completion_time, False)
	else:
		LogMsg("❌ No valid date is selected for Syria day 2")
		return

	# Make sure "Conditions" field exists
	if "Conditions" not in original_data:
		LogMsg("Conditions field not found in the original json file")
		original_data["Conditions"] = []

	# check if original profile has any autostyria conditions. if they exist remove them all.
	if(has_autostyria_condition(original_data["Conditions"])):
		original_data["Conditions"] = remove_autostyria_conditions(original_data.get("Conditions", []))

	# create a new cloned data. any modification made any further won't be part of the original json file.
	modified_data = json.loads(json.dumps(original_data))  # Deep copy

	# Insert conditions if they dont exist
	original_data["Conditions"].append(prep_condition_day1)
	LogMsg(f"preparation condition for styria day 1 added in to profile {glb_training_profile}")
	original_data["Conditions"].append(prep_condition_day2)
	LogMsg(f"preparation condition for styria day 2 added in to profile {glb_training_profile}")

	# Replace the conditions with an empty one if it exists. this ensures no conditions are passed from copied json profile.
	if "Conditions" in modified_data and isinstance(modified_data["Conditions"], list):
		modified_data["Conditions"] = []  # remove all the conditions!

	# Set all boolean entries under "Loop" to False, this ensures no issues with scripts or unnessary returns while we waiting for registry.
	loop_data = modified_data.get("Loop", {})
	for key, value in loop_data.items():
		if isinstance(value, bool):  # Check if the value is a boolean
			modified_data["Loop"][key] = False

	# Set all boolean entries under "Party" to False, this is to ensure no party creation during styria
	loop_data = modified_data.get("Party", {})
	for key, value in loop_data.items():
		if isinstance(value, bool):  # Check if the value is a boolean
			modified_data["Party"][key] = False

	#add the only conditions we need!
	modified_data["Conditions"].append(entry_condition_day1)
	LogMsg("register condition for styria day 1 added in to profile " + pName)
	modified_data["Conditions"].append(entry_condition_day2)
	LogMsg("register condition for styria day 2 added in to profile " + pName)

	# Save modified data into new json
	with open(autostyria_profile_json, 'w', encoding='utf-8') as file:
		json.dump(modified_data, file, indent=4)

	# === Save Preparation Conditions Back to Original File ===
	with open(original_profile_json, "w", encoding="utf-8") as f:
		json.dump(original_data, f, indent=4)

	SaveConfigIfJoined()

	set_profile(pName)
	LogMsg(f"✅ AutoStyria profile generated succesfully and Auto styria preperation conditions succesfully added to your profile {original_profile_json}")
	Timer(1.0, set_profile, [glb_training_profile]).start() #wait than swap the profile.

#_______________________________Async methods________________________#
async def async_check_stop_event():
    """Async-friendly stop event checker."""
    if glb_stop_event.is_set():
        LogMsg("Background thread interrupted via callback.")
        return True
    return False

async def async_task_with_sleep(duration):
    for i in range(duration):  # Sleep in chunks of 1 second to check periodically
        if await async_check_stop_event():
            return 0
        
        await asyncio.sleep(1)  # Sleep for 1 second (can be adjusted)

async def asynch_random_sleep(min, max):
	LogMsg(f"randomly waiting between {min} and {max} second to avoid overloading")
	delay = int(random.uniform(float(min), float(max)))
	await async_task_with_sleep(int(delay))
	LogMsg("random delay is finished. proceeding to next step...")

async def async_returnTown():
	condition_met = use_return_scroll()
	max_tries = 3
	tries = 0

	try:
		#loop untill the condition is met or tries exceeds the max_tries
		while not condition_met and tries < max_tries:
			LogMsg("trying to use return scroll...")
			condition_met = use_return_scroll()
			await async_task_with_sleep(1)
			tries += 1
	except asyncio.TimeoutError:
		LogMsg("❌ Timeout: failed using return scroll")
		return False
	except Exception as e:
		LogMsg(f"❌  Error in async_stop_bot: {e}")
		return False
	
	if(not condition_met):
		LogMsg("❌ cannot return town! make sure there are return scrolls in player's inventory")

	return condition_met

async def async_leave_party():
	condition_met = not get_party()
	if(condition_met):
		LogMsg("not in party!")
	max_tries = 3
	tries = 0

	try:
		#loop untill the condition is met or tries exceeds the max_tries
		while not condition_met and tries < max_tries:
			print("trying to leave party...")
			leave_party()
			await async_task_with_sleep(1)
			condition_met = not get_party()
			if(condition_met):
				LogMsg("succesfully left party")
			tries += 1
		
		return condition_met
	except asyncio.TimeoutError:
		LogMsg("❌ Timeout: leaving party task took too long")
		return False
	except Exception as e:
		LogMsg(f"❌ Error in async_leave_party: {e}")
		return False		

async def async_stop_bot():
	condition_met = False
	max_tries = 3
	tries = 0

	try:
		#loop untill the condition is met or tries exceeds the max_tries
		while not condition_met and tries < max_tries:
			LogMsg("Waiting for bot to stop...")
			condition_met = stop_bot()
			await async_task_with_sleep(1)
			tries += 1
		return condition_met
	except asyncio.TimeoutError:
		LogMsg("❌ Timeout: Bot stop task took too long")
		return False
	except Exception as e:
		LogMsg(f"❌ Error in async_stop_bot: {e}")
		return False		

async def async_start_bot():
	condition_met = start_bot()
	max_tries = 3
	tries = 0

	try:
		#loop untill the condition is met or tries exceeds the max_tries
		while not condition_met and tries < max_tries:
			LogMsg("Waiting for bot to start...")
			condition_met = start_bot()
			await async_task_with_sleep(2)
			tries += 1
		return condition_met
	except asyncio.TimeoutError:
		LogMsg("❌ Timeout: Bot start task took too long")
		return False
	except Exception as e:
		LogMsg(f"❌ Error in async_start_bot: {e}")
		return False

async def async_register_styria():
	if QtBind.isChecked(gui,gui_allow_register_chkBox) is True:
		NpcID = GetNPCUniqueID('Arena Manager')
		if NpcID == 0:
			LogMsg('⚠️ Plugin: "Arena Manager" is not near. Be sure to use the script command near to the NPC')
			return False
		else:
			LogMsg("trying to register for styria")
			p = bytearray(struct.pack('<H', NpcID))
			p += b'\x00\x00'
			SelectBatleArenaNPC(p)
			await async_task_with_sleep(4)
			SelectStyriaRegisterOption(p)
			await async_task_with_sleep(4)
			sendRegisterStyria()
			await async_task_with_sleep(4)
			return True
	else:
		LogMsg("⚠️ Auto register disabled. you need to regiser manually via bot manager.")
		LogMsg("if you want plug in to do the registration. please activate the option in bot's plugin tab")
		return False
	
async def async_equipJobItemIfExist():
	jobItemEquipped = equipJobItemIfExist()
	await async_task_with_sleep(1)
	if(jobItemEquipped == JobItemStatus.NOT_EQUIPPED):
		return False
	elif(jobItemEquipped == JobItemStatus.EQUIP_INPROGRESS):
		LogMsg("In progress...waiting 40 seconds to equip job item")
		await async_task_with_sleep(40)
	return True

async def async_unequipJobItem():
	item = getJobItem(8)
	if item:
		UnequipItem(item)
		LogMsg("Waiting for 30 seconds...")
		await async_task_with_sleep(30)

async def async_autostyria_prepare():

	global glb_training_profile
	glb_training_profile = get_profile()
	LogMsg(f"storing default profile {glb_training_profile} to be recovered later")	
	#try stopping bot
	success = await async_stop_bot()

	#need to modify the autostyria conditions. 
	configDirectory = get_config_dir()
	character_data = get_character_data()
	autostyria_profile_json = configDirectory + character_data['server'] + "_" + character_data['name'] + "." + pName + ".json"
	# Load the original JSON data
	with open(autostyria_profile_json, 'r', encoding='utf-8') as file:
		json_data = json.load(file)

	if "Conditions" in json_data:
		#ensure the times are up to date. 
		update_registration_time_conditions(json_data['Conditions'], 5)
		enable_autostyria_registration_conditions(json_data['Conditions'], True)
	else:
		LogMsg(f"❌ Preperation cannot continue because no autostyria conditions found in profile {pName}")
		return 0

	# === Save Preparation Conditions Back to Original File ===
	with open(autostyria_profile_json, "w", encoding="utf-8") as f:
		json.dump(json_data, f, indent=4)

	LogMsg(str(autostyria_profile_json))

	success = set_profile(pName)
	if(not success):
		LogMsg("AutoStyria profile for this character is not found! make sure you generated one!")
		return 0

	await asynch_random_sleep(1,10) 

	#try returning town
	success = await async_returnTown()
	if not success: 
		return 0
	LogMsg("Waiting for 1 minute...")
	await async_task_with_sleep(60)

	LogMsg("Checking to ensure the char didnt die during teleport")
	character_data = get_character_data()
	if(character_data['dead']):
		LogMsg("Char is dead. returning town")
		success = await async_returnTown()
		if not success: 
			return 0
		await async_task_with_sleep(40)
	else:
		LogMsg("All good! Character should now be in town!")

	#check for stop event
	if await async_check_stop_event():
		return 0
	
	LogMsg('try leaving party ')
	await async_leave_party()
		
	#check for stop event
	if await async_check_stop_event():
		return 0
	
	LogMsg('try equipping job item')
	success = await async_equipJobItemIfExist()
	if not success:
		LogMsg('❌ job item is not equipped! This can be because of : ')
		LogMsg('  A: your char is constantly accepting party invitation in town while equipping the item or...')
		LogMsg('  B: your char is set to use party matching system or...')
		LogMsg('  C: you have a job item that you cannot wear in your inventory...')
		return 0

	#check for stop event
	if await async_check_stop_event():
		return 0

	LogMsg("getting player's current region")
	character_data = get_character_data()	
	region = character_data['region']
	LogMsg(str(region))
	scriptToNPC = None
	try:
		scriptToNPC = FRM_TELEPORT_TO_NPC[REGION(region)]
	except (ValueError, KeyError):
		LogMsg("⚠️ no script can be found from current location! make sure you are in teleport area!")
		return 0
	
	if(scriptToNPC):
		LogMsg("walking to npc from the current region")
		start_script(scriptToNPC)
		LogMsg("waiting for 1 minute to script to finish...")
		await async_task_with_sleep(60)
		LogMsg("script should finish by now. if not... something is wrong!")
	
	LogMsg("✅ Preperations in the background task completed successfully!")
	if QtBind.isChecked(gui,gui_allow_register_chkBox) is False:
		LogMsg("⚠️'let plugin register to styria option' disabled in plug in menu! Because of this you need to manually register to Styria")
	else:
		LogMsg("AutoStyria will now wait till registration condition to meet before starting the registration process")

	return 0

async def async_autostyria_complete():
	await asynch_random_sleep(1,10)
	LogMsg("Wait for additonal 1 min... This is to ensure the plugin doesnt interfare other plugins relying on teleport such as RewardCollecter")
	await async_task_with_sleep(60)
	await async_stop_bot()
	await async_leave_party()
	if QtBind.isChecked(gui,gui_ignore_unequip_jobItem_chkBox) is False:
		await async_unequipJobItem()
	else:
		LogMsg("ignored unequipping job due to plugin settings.")
	set_profile(glb_training_profile)
	await async_task_with_sleep(1)

	if QtBind.isChecked(gui,gui_allow_disconnect_chkBox) is True:
		LogMsg("✅ Styria completed. disconnecting due to plugin settings")
		disconnect()
	else:
		LogMsg("")
		await async_start_bot()
		LogMsg("✅ Styria completed. Reverted back to training profile to" + glb_training_profile + "and resuming botting!")
	global glb_registered_for_styria
	glb_registered_for_styria = False
	return 0

async def async_autostyria_register():
	await asynch_random_sleep(1,10)
	try:
		success = await async_register_styria()
		global glb_registered_for_styria
		glb_registered_for_styria = True
		if success:
			LogMsg("✅ Syria registration complete!")
		else:
			LogMsg("failed registring to styria")
	except asyncio.TimeoutError:
			LogMsg("Timed out waiting styria registration")
	except Exception as e:
		LogMsg(f"Error in async_autostyria_register: {e}")

	
	return 0
#__________________________________methods___________________________#
# Wrapper to run the coroutine in a thread
def run_async_autostyria(arguments):
	prepare = "Prepare" in arguments
	register = "Register" in arguments
	complete = "Complete" in arguments
	global glb_thread_started
	if(prepare):
		try:
			asyncio.run(async_autostyria_prepare())
		except Exception as e:
			LogMsg(f"Error in async_autostyria_prepare: {e}")
		finally:
			LogMsg("Background task finished")
			with glb_thread_lock:
				glb_thread_started = False
	elif(register):
		try:
			asyncio.run(async_autostyria_register())
		except Exception as e:
			LogMsg(f"Error in async_autostyria_register: {e}")
		finally:
			LogMsg("Background task finished")
			with glb_thread_lock:
				glb_thread_started = False
	elif(complete):
		try:
			asyncio.run(async_autostyria_complete())
		except Exception as e:
			LogMsg(f"Error in async_autostyria_complete: {e}")
		finally:
			LogMsg("Background task finished")
			with glb_thread_lock:
				glb_thread_started = False

	else:
		LogMsg("argument is not recognised! exiting without doing anything")
	
	return 0

def autostyria_prepare():
	if QtBind.isChecked(gui,gui_disable_plugin_chkBox) is False:
		global glb_thread_started
		with glb_thread_lock:
			if (glb_thread_started):
				return 0
			glb_thread_started = True

		LogMsg("Create and start a non-daemon background thread for PREPERATION tasks")
		arguments = ["Prepare"]
		thread = Thread(target=run_async_autostyria, args=(arguments,))
		thread.daemon = False  # Non-daemon thread
		thread.start()
		LogMsg("Preparation tasks are running in background thread! Please dont do anything till tasks are complete")
	return 0

def autostyria_register():
	if QtBind.isChecked(gui,gui_disable_plugin_chkBox) is False:
		global glb_thread_started
		with glb_thread_lock:
			if (glb_thread_started):
				return 0
			glb_thread_started = True

		LogMsg("Create and start a non-daemon background thread for REGISTRATION tasks")
		arguments = ["Register"]
		thread = Thread(target=run_async_autostyria, args=(arguments,))
		thread.daemon = False  # Non-daemon thread
		thread.start()
		LogMsg("Registration tasks are running in background thread! Please dont do anything till tasks are complete")
	return 0

def autostyria_complete():
	global glb_thread_started
	with glb_thread_lock:
		if (glb_thread_started):
			return 0
		glb_thread_started = True

	LogMsg("Create and start a non-daemon background thread for Auto stria COMPLETION tasks")
	arguments = ["Complete"]
	thread = Thread(target=run_async_autostyria, args=(arguments,))
	thread.daemon = False  # Non-daemon thread
	thread.start()
	LogMsg("Completion tasks are running in background thread! Please dont do anything till tasks are complete")

def UnequipItem(item):
	# find an empty slot
	slot = GetEmptySlot()
	if slot == -1:
		LogMsg('⚠️ ignored unequipping job item. No empty slot available')
	elif item['slot'] != 8:
		LogMsg('⚠️ ignored unequipping job item. No equipped job item is found!')
	else:
		Inject_InventoryMovement(0,item['slot'],slot,item['name'])

def Inject_InventoryMovement(movementType,slotInitial,slotFinal,logItemName,quantity=0):
	p = struct.pack('<B',movementType)
	p += struct.pack('<B',slotInitial)
	p += struct.pack('<B',slotFinal)
	p += struct.pack('<H',quantity)
	LogMsg('Moving item "'+logItemName+'"...')
	# CLIENT_INVENTORY_ITEM_MOVEMENT
	inject_joymax(0x7034,p,False)

def getJobItem(startslot):
	item = GetItemByExpression(lambda sname: sname.startswith('ITEM_EU_W_NEW_TRADE'),startslot)
	if item:
		return item
	item = GetItemByExpression(lambda sname: sname.startswith('ITEM_EU_M_NEW_TRADE'),startslot)
	if item:
		return item
	item = GetItemByExpression(lambda sname: sname.startswith('ITEM_CH_W_NEW_TRADE'),startslot)
	if item:
		return item
	item = GetItemByExpression(lambda sname: sname.startswith('ITEM_CH_M_NEW_TRADE'),startslot)
	if item:
		return item
	return None

def GetItemByExpression(_lambda, start=0, end=0):
    inventory = get_inventory()
    items = inventory['items']
    
    if end == 0:
        end = inventory['size']
    
    for slot, item in enumerate(items):
        if start <= slot <= end:
            if item and _lambda(item['servername']):
                item['slot'] = slot
                return item
    return None

def leave_party():
	LogMsg("AutoStyria-plugin: Leaving the party..")
	inject_joymax(0x7061,b'',False)

def equipJobItemIfExist():
	jobItem = getJobItem(8)

	if jobItem['slot'] == 8:
		LogMsg('jop item already equipped')
		return JobItemStatus.EQUIPPED
	
	elif jobItem['slot'] > 8:
		LogMsg('equpping job items. this will take some time')
		Inject_InventoryMovement(0,jobItem['slot'],8,jobItem['name'])
		return JobItemStatus.EQUIP_INPROGRESS
	
	else:
		LogMsg('failed equipping job items. make sure you have one usable job item in inventory')
		return JobItemStatus.NOT_EQUIPPED

# Finds an empty slot, returns -1 if inventory is full
def GetEmptySlot():
	items = get_inventory()['items']
	# check the first empty
	for slot, item in enumerate(items):
		if slot >= 13:
			if not item:
				return slot
	return -1
    
def SelectBatleArenaNPC(p):
	LogMsg("Selecting samarkand battle arena NPC")
	# = b'\x77\x01\x00\x00'
	opcode = 0x7045 #target opcode
	LogMsg('[%s] └ data: %s' % (__name__, hexlify(p)))
	inject_joymax(opcode, p, False)

def SelectStyriaRegisterOption(p):
	LogMsg("selecting styria option")
	#p = b'\x77\x01\x00\x00'
	opcode = 0x704B
	LogMsg('[%s] └ data: %s' % (__name__, hexlify(p)))
	inject_joymax(opcode, p, False)

def sendRegisterStyria():
	LogMsg("styria registration")
	p = b'\x01\x05\x04'
	opcode = 0x74D3
	LogMsg('[%s] └ data: %s' % (__name__, hexlify(p)))
	inject_joymax(opcode, p, False)


def GetNPCUniqueID(name):
	NPCs = get_npcs()
	if NPCs:
		name = name.lower()
		for UniqueID, NPC in NPCs.items():
			NPCName = NPC['name'].lower()
			if name in NPCName:
				return UniqueID
	return 0
# ______________________________ Events _____________________________________ #
def joined_game():
	LoadConfig() # this almost never works because char data is usually not avaiable here!

def teleported():
	LoadConfig() #best place to get char data. so load the config after teleportation.
	if(glb_registered_for_styria): #handles autostyria stopping condition 
		currentProfile = get_profile()
		if(currentProfile == pName): #only care when profile is in autostyria
			LogMsg("getting player's current region")
			character_data = get_character_data()	
			region = character_data['region']
			global glb_styria_started
			if(not glb_styria_started): #check on each teleportation to see if we are in styria region.
				region_enum = REGION(region)
				try:
					if region_enum  in {REGION.STYRIA_A1, REGION.STYRIA_A2, REGION.STYRIA_B1, REGION.STYRIA_B2}:
						LogMsg("Styria region detected! more likely we are in styria world!")
						glb_styria_started = True
				except ValueError:
					LogMsg(f"While waiting for styria, unknown styria or town region ID {region} detected during teleport! Ignore this if you messing around while waiting for styria")

			else: #check on each teleportation to see if we are out of styria region.
				region_enum = REGION(region)
				try:
					if region_enum not in {REGION.STYRIA_A1, REGION.STYRIA_A2, REGION.STYRIA_B1, REGION.STYRIA_B2}:
						autostyria_complete() #we are out! styria must be complete!
						glb_styria_started = False
				except ValueError:
					LogMsg(f"while in styria unknown styria or town region ID {region} detected during teleport! More likely you manually quit the Styria! or your bot is using return scroll for some reason!")

def finished():
	LogMsg("#signal the background thread to finish.")
	glb_stop_event.set()

#______________________________config methods________________________________#

def CharInGame():
	global glb_char_data
	character_data = get_character_data()
	if(character_data is None): #only update if the character data is none.
		LogMsg("char data doesn't exist! trying to retrive from bot")
		if not (character_data and "name" in character_data and character_data["name"]):
			character_data = None
		glb_char_data = character_data
	return character_data

def getPath():
	return get_config_dir() + pName + "/"

# Return character configs path (JSON)
def getConfig():
	global glb_char_data
	if(glb_char_data is None):
		glb_char_data = get_character_data()
	
	path = getPath() + pName + '_' + glb_char_data['server'] + '_' + glb_char_data['name'] + '.json'
	LogMsg(f"getConfig(): {path}")
	return path

# Load config if exists
def LoadConfig():
	if(CharInGame):
		if not os.path.exists(getPath()):
			os.makedirs(getPath())
			LogMsg(f'Plugin: {pName} folder has been created')
		else:
			config = getConfig()
			LogMsg(str(config))
			if(os.path.exists(config)):
				data = {}
				with open(config,"r") as f:
					data = json.load(f)

				# Basic fields
				QtBind.setChecked(gui, gui_disable_plugin_chkBox, data.get('DisablePlugin', False))
				QtBind.setChecked(gui, gui_ignore_unequip_jobItem_chkBox, data.get('IgnoreJobItemEquipmen', False))
				QtBind.setChecked(gui, gui_allow_disconnect_chkBox, data.get('DisconectAfterStyria', False))
				QtBind.setChecked(gui, gui_allow_register_chkBox, data.get('AllowAutoRegister', False))
				registerAt = data.get('RegisterAt', '22:00')
				QtBind.setText(gui, gui_registerTimeLine, data.get('RegisterAt', registerAt))
				QtBind.setText(gui, gui_prepareTimeLabel, get_preperation_start_timestr(registerAt, 10))


				# Days for styria day 1
				day1 = data.get('styria day 1', {})
				QtBind.setChecked(gui, gui_day1_checkbox_mon, day1.get('Monday', False))
				QtBind.setChecked(gui, gui_day1_checkbox_tue, day1.get('Tuesday', False))
				QtBind.setChecked(gui, gui_day1_checkbox_wed, day1.get('Wednesday', False))
				QtBind.setChecked(gui, gui_day1_checkbox_thu, day1.get('Thursday', False))
				QtBind.setChecked(gui, gui_day1_checkbox_fri, day1.get('Friday', True))
				QtBind.setChecked(gui, gui_day1_checkbox_sat, day1.get('Saturday', False))
				QtBind.setChecked(gui, gui_day1_checkbox_sun, day1.get('Sunday', False))

				# Days for styria day 2
				day2 = data.get('styria day 2', {})
				QtBind.setChecked(gui, gui_day2_checkbox_mon, day2.get('Monday', False))
				QtBind.setChecked(gui, gui_day2_checkbox_tue, day2.get('Tuesday', False))
				QtBind.setChecked(gui, gui_day2_checkbox_wed, day2.get('Wednesday', False))
				QtBind.setChecked(gui, gui_day2_checkbox_thu, day2.get('Thursday', False))
				QtBind.setChecked(gui, gui_day2_checkbox_fri, day2.get('Friday', False))
				QtBind.setChecked(gui, gui_day2_checkbox_sat, day2.get('Saturday', True))
				QtBind.setChecked(gui, gui_day2_checkbox_sun, day2.get('Sunday', False))

def SaveConfigIfJoined():
	if CharInGame():
		# Save all data
		data = {
    		'DisablePlugin': QtBind.isChecked(gui, gui_disable_plugin_chkBox),
    		'IgnoreJobItemEquipmen': QtBind.isChecked(gui, gui_ignore_unequip_jobItem_chkBox),
    		'DisconectAfterStyria': QtBind.isChecked(gui, gui_allow_disconnect_chkBox),
    		'AllowAutoRegister': QtBind.isChecked(gui, gui_allow_register_chkBox),
    		'RegisterAt': str(QtBind.text(gui, gui_registerTimeLine)),
    		'styria day 1': {
        		'Monday': QtBind.isChecked(gui,gui_day1_checkbox_mon),
        		'Tuesday': QtBind.isChecked(gui,gui_day1_checkbox_tue),
        		'Wednesday': QtBind.isChecked(gui,gui_day1_checkbox_wed),
        		'Thursday': QtBind.isChecked(gui,gui_day1_checkbox_thu),
        		'Friday': QtBind.isChecked(gui,gui_day1_checkbox_fri),
        		'Saturday': QtBind.isChecked(gui,gui_day1_checkbox_sat),
        		'Sunday': QtBind.isChecked(gui,gui_day1_checkbox_sun)
				},

			'styria day 2': {
        		'Monday': QtBind.isChecked(gui,gui_day2_checkbox_mon),
        		'Tuesday': QtBind.isChecked(gui,gui_day2_checkbox_tue),
        		'Wednesday': QtBind.isChecked(gui,gui_day2_checkbox_wed),
        		'Thursday': QtBind.isChecked(gui,gui_day2_checkbox_thu),
        		'Friday': QtBind.isChecked(gui,gui_day2_checkbox_fri),
        		'Saturday': QtBind.isChecked(gui,gui_day2_checkbox_sat),
        		'Sunday': QtBind.isChecked(gui,gui_day2_checkbox_sun)
				}
		}
		# Override
		with open(getConfig(),"w") as f:
			f.write(json.dumps(data, indent=4, sort_keys=True))


# Plugin loaded
LogMsg(f'Plugin: {pName} v{pVersion} succesfully loaded')
LoadConfig() #ensure config is loaded if user presses refresh button in plugin window