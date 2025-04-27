from phBot import *
from threading import Thread
from threading import Timer
from enum import Enum
from time import sleep
import phBotChat
import QtBind
import struct
import random
import json
import os
import sqlite3
from binascii import hexlify  # for debugging

debug = 3
pName = 'PVPWepSwitcher'
logPrefix = pName + '-plugin: '
pVersion = '1.0.0'
pUrl = 'https://raw.githubusercontent.com/JellyBitz/phBot-xPlugins/master/xControl.py'

IgnoreJobSuit = False
ignoreDuplicateStartFromScript = False
TrainingProfile = None
# ______________________________ Initializing ______________________________ #
gui = QtBind.init(__name__,pName)

gui_window_padding_x = 30
gui_window_padding_y = 70


gui_register_x = gui_window_padding_x
gui_register_y = gui_window_padding_y

gui_ignore_unequip_x = gui_register_x
gui_ignore_unequip_y = gui_register_y + gui_window_padding_y

gui_disable_x = gui_ignore_unequip_x
gui_disable_y = gui_ignore_unequip_y + 20

gui_allow_disconnect_x = gui_disable_x
gui_allow_disconnect_y = gui_disable_y + 20

gui_allow_register_x = gui_allow_disconnect_x
gui_allow_register_y = gui_allow_disconnect_y + 20


QtBind.createLabel(gui, 'Register for Styria:', gui_register_x, gui_register_y)
QtBind.createButton(gui, 'EquipTwoHand', 'Register for Styria', gui_register_x, gui_register_y + 20)
gui_ignore_unequip_jobItem_chkBox = QtBind.createCheckBox(gui, 'cbxAuto_clicked','ignore unequpping job item ', gui_ignore_unequip_x, gui_ignore_unequip_y)
gui_disable_plugin_chkBox = QtBind.createCheckBox(gui, 'cbxAuto_clicked','disable plugin ', gui_disable_x, gui_disable_y)
gui_allow_disconnect_chkBox = QtBind.createCheckBox(gui, 'cbxAuto_clicked','disconnect after styria complete ', gui_allow_disconnect_x, gui_allow_disconnect_y)
gui_allow_register_chkBox = QtBind.createCheckBox(gui, 'cbxAuto_clicked','let plugin register to styria ', gui_allow_register_x, gui_allow_register_y)

btnLoadConfig = QtBind.createButton(gui,'LoadConfigIfJoined',"   load config    ",400,280)
btnSaveConfig = QtBind.createButton(gui,'SaveConfigIfJoined',"   save config    ",500,280)

# ______________________________ Methods ______________________________ #
def LogMsg(logstr):
	log(logPrefix + logstr)

class JobItemStatus(Enum):
    NOT_EQUIPPED = 1
    EQUIPPED = 2
    EQUIP_INPROGRESS = 3

def PvPWepSwitcher(arguments):
	EquipTwoHand()
	return 0


def EquipTwoHand():
	twoHand = getTwoHand(6)
	LogMsg("test")
	if twoHand['slot'] == 6:
		LogMsg('two hand already equipped')
		return

	elif twoHand['slot'] > 6:
		LogMsg('equpping two hand')
		Inject_InventoryMovement(0,twoHand['slot'],6,twoHand['name'])	
	else:
		LogMsg('failed equipping two hand is failed. make sure you have one two hand in inventory')

def EquipDualAxe():
	axe = getAxe(6)
	LogMsg("test")
	if axe['slot'] == 6:
		LogMsg('axe already equipped')
		return

	elif axe['slot'] > 6:
		LogMsg('equpping two hand')
		Inject_InventoryMovement(0,axe['slot'],6,axe['name'])	
	else:
		LogMsg('failed equipping axe. make sure you have one in inventory')

def EquipOneHand():
	oneHand = getOneHand(6)
	shield = getShield(7)

	if shield['slot'] > 7:
		LogMsg('equpping shield')
		Inject_InventoryMovement(0,shield['slot'],7,shield['name'])	
	else:
		LogMsg('failed equipping shield. make sure you have one in inventory')

	if oneHand['slot'] == 6:
		LogMsg('onehand already equipped')
		return
	
	elif oneHand['slot'] > 6:
		LogMsg('equpping oneHand')
		Timer(0.2, Inject_InventoryMovement,[0,oneHand['slot'],6,oneHand['name']]).start()
	else:
		LogMsg('failed equipping oneHand. make sure you have one in inventory')

	
def Inject_InventoryMovement(movementType,slotInitial,slotFinal,logItemName,quantity=0):
	p = struct.pack('<B',movementType)
	p += struct.pack('<B',slotInitial)
	p += struct.pack('<B',slotFinal)
	p += struct.pack('<H',quantity)
	LogMsg('Moving item "'+logItemName+'"...')
	# CLIENT_INVENTORY_ITEM_MOVEMENT
	inject_joymax(0x7034,p,False)

def getTwoHand(startslot):
	item = GetItemByExpression(lambda sname: sname.startswith('ITEM_EU_TSWORD'),startslot)
	LogMsg('looking for two hand')
	if item:
		return item
	
def getAxe(startslot):
	item = GetItemByExpression(lambda sname: sname.startswith('ITEM_EU_AXE'),startslot)
	LogMsg('looking for Axe')
	if item:
		return item
	
def getOneHand(startslot):
	item = GetItemByExpression(lambda sname: sname.startswith('ITEM_EU_STAFF'),startslot)
	LogMsg('looking for Onehand')
	if item:
		return item

def getShield(startslot):
	item = GetItemByExpression(lambda sname: sname.startswith('ITEM_EU_SHIELD'),startslot)
	LogMsg('looking for shield')
	if item:
		return item


# Search an item by name or servername through lambda expression and return his information
def GetItemByExpression(_lambda,start=0,end=0):
	#printInventoryItems()
	inventory = get_inventory()
	items = inventory['items']
	if end == 0:
		end = inventory['size']
	# check items between intervals
	for slot, item in enumerate(items):
		if start <= slot and slot <= end:
			if item:
				# Search by lambda
				if _lambda(item['servername']):
					# Save slot location
					item['slot'] = slot
					return item
	return None

# Finds an empty slot, returns -1 if inventory is full
def GetEmptySlot():
	items = get_inventory()['items']
	# check the first empty
	for slot, item in enumerate(items):
		if slot >= 13:
			if not item:
				return slot
	return -1
 
#______________________________config methods________________________________#

def LoadConfigIfJoined():
	if(charInGame()):
		LoadConfig()

# Return folder path
def SaveConfigIfJoined():
	if(charInGame()):
		# Save all data
		data = {}
		data['DisablePlugin'] = QtBind.isChecked(gui,gui_disable_plugin_chkBox)
		data['IgnoreJobItemEquipmen'] = QtBind.isChecked(gui,gui_ignore_unequip_jobItem_chkBox)
		data['DisconectAfterStyria'] = QtBind.isChecked(gui,gui_allow_disconnect_chkBox)
		data['AllowAutoRegister'] = QtBind.isChecked(gui,gui_allow_register_chkBox)
		# Override
		with open(getConfig(),"w") as f:
			f.write(json.dumps(data, indent=4, sort_keys=True))


def LoadConfig():
	if os.path.exists(getConfig()):
		data = {}
		with open(getConfig(),"r") as f:
			data = json.load(f)
		# Check to load config
		if 'DisablePlugin' in data and data['DisablePlugin']:
			QtBind.setChecked(gui,gui_disable_plugin_chkBox,True)
		if 'IgnoreJobItemEquipmen' in data and data['IgnoreJobItemEquipmen']:
			QtBind.setChecked(gui,gui_ignore_unequip_jobItem_chkBox,True)
		if 'DisconectAfterStyria' in data and data['DisconectAfterStyria']:
			QtBind.setChecked(gui,gui_allow_disconnect_chkBox,True)
		if "AllowAutoRegister" in data and data['AllowAutoRegister']:
			QtBind.setChecked(gui, gui_allow_register_chkBox, True)
	else:
		SaveConfigIfJoined()


def getPath():
	return get_config_dir() + pName + "\\"

# Return character configs path (JSON)
def getConfig():
	global CharacterName
	if(CharacterName == None):
		charData = get_character_data()
		CharacterName = charData['name']
	return getPath() + pName + '_' + CharacterName + '.json'

if os.path.exists(getPath()):
	# Adding RELOAD plugin support
	LogMsg('path already exist')
else:
	# Creating configs folder
	os.makedirs(getPath())

#______________________________ Helper Methods ______________________________ #
def inject_client(opcode, data, encrypted):
    global debug
    if debug >= 3:
        log('[%s] DEBUG3: bot to client' % (__name__))
        log('[%s] DEBUG3:  └ opcode: 0x%02X' % (__name__, opcode))
        if data is not None:
            log('[%s] DEBUG3:  └ data: %s' % (__name__, hexlify(data)))
    return inject_silkroad(opcode, data, encrypted)


def inject_server(opcode, data, encrypted):
    global debug
    if debug >= 3:
        log('[%s] DEBUG3: bot to server' % (__name__))
        log('[%s] DEBUG3:  └ opcode: 0x%02X' % (__name__, opcode))
        if data is not None:
            log('[%s] DEBUG3:  └ data: %s' % (__name__, hexlify(data)))
    return inject_joymax(opcode, data, encrypted)

def charInGame():
	global CharacterName
	character_data = get_character_data()
	if(character_data):
		CharacterName = character_data['name']
		return True
	else:
		return False

# ______________________________ Events ______________________________ #

#allows us to load config when game loads.
def teleported():
	LoadConfigIfJoined()