﻿#cython: language_level=3

RAISE_ERROR_ON_COMMUNICATION_FAILURE 		= True
RAISE_ERROR_ON_COLLISION 					= False

DEFAULT_OPEN_LOOP_CURRENT 					= 70 	# [%]
DEFAULT_HOLDING_CURRENT						= 10 	# [%]
DEFAULT_MOTOR_SPEED							= 5000 	# [RPM]
DEFAULT_APPROACH_DISTANCE					= 0.5 	# [°]
DEFAULT_ENABLE_APPROACH 					= True
DEFAULT_SHUT_DOWN_AFTER_MOVE 				= False
DEFAULT_LOW_POWER_AFTER_MOVE 				= True

CANCOM_CONNECT_ANY_ID						= 'any'
CANCOM_FIRMWARE_CONTROL_LOOP_FREQUENCY		= 2000  # [Hz] Do not modify
CAN_COM_WATCHDOG_TIMER 						= 0.5 	# [s]
CAN_DELAY_BETWEEN_CONFIG_COMMANDS 			= 0.5 	# [s]
CAN_COM_STATUS_BROADCAST_WATCHDOG_TIMER 	= 2 	# [s]
CAN_DELAY_FOR_ASKID				 			= 0.5 	# [s]
CAN_COM_SAVE_INTERNAL_CALIB_WATCHDOG_TIMER 	= 4 	# [s]
CAN_COM_WAIT_FOR_TIMEOUT 					= 'wait'
CAN_COM_FIRMWARE_UPGRADE_TIMEOUT 			= 10 	# [s]

GUI_DEFAULT_FONT							= "Helvetica"
GUI_DEFAULT_FONT_SIZE						= 9

GUI_BOOTLOADER_WATCHDOG 					= 10 	# [s]
POS_BOOTLOADER_FIRMWARE_ID 					= '80' 	# The version identifyer of a bootloader program. Do not modify