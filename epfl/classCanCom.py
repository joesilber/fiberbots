#cython: language_level=3
import serial
import time
from serial.tools import list_ports
import DEFINES
import errors

class StatusRegistery:
	"""
	The status registry of the positioner.

	Each parameter of the positioner's status registry in normal operation mode is listed here. These are read-only values and must not be modified.

	Attributes
	----------
	SYSTEM_INITIALIZED: uint64
		Positioner has booted properly.
	CONFIG_CHANGED: uint64
		Configuration changed.
	BSETTINGS_CHANGED: uint64
		Bootloader settings changed.
	DATA_STREAMING: uint64
		Data streaming enabled. Currently unused.
	RECEIVING_TRAJECTORY: uint64
		A trajectory is currently being received.
	TRAJECTORY_ALPHA_RECEIVED: uint64
		The alpha motor trajectory was received.
	TRAJECTORY_BETA_RECEIVED: uint64
		The beta motor trajectory was received.
	LOW_POWER_AFTER_MOVE: uint64
		The positioner is configured to minimize the current of the motors after each move.
	DISPLACEMENT_COMPLETED: uint64
		This bit is set when the positioner is not moving.
	DISPLACEMENT_COMPLETED_ALPHA: uint64
		This bit is set when the alpha motor is not moving.
	DISPLACEMENT_COMPLETED_BETA: uint64
		This bit is set when the beta motor is not moving.
	COLLISION_ALPHA: uint64
		The alpha motor has detected a collision
	COLLISION_BETA: uint64
		The beta motor has detected a collision
	CLOSED_LOOP_ALPHA: uint64
		The alpha motor is configured to use the closed loop control
	CLOSED_LOOP_BETA: uint64
		The beta motor is configured to use the closed loop control
	PRECISE_POSITIONING_ALPHA: uint64
		The alpha motor is configured to perform an approach move and precise positionning each time it reaches the end of the trajectory
	PRECISE_POSITIONING_BETA: uint64
		The alpha motor is configured to perform an approach move and precise positionning each time it reaches the end of the trajectory
	COLLISION_DETECT_ALPHA_DISABLE: uint64
		The alpha motor is configured to disregard any collision
	COLLISION_DETECT_BETA_DISABLE: uint64
		The beta motor is configured to disregard any collision
	MOTOR_CALIBRATION: uint64
		The positioner is in motor calibration mode
	MOTOR_ALPHA_CALIBRATED: uint64
		The alpha motor has been calibrated
	MOTOR_BETA_CALIBRATED: uint64
		The beta motor has been calibrated
	DATUM_CALIBRATION: uint64
		The positioner is in datum calibration mode
	DATUM_ALPHA_CALIBRATED: uint64
		The alpha datum has been calibrated
	DATUM_BETA_CALIBRATED: uint64
		The beta datum has been calibrated
	DATUM_INITIALIZATION: uint64
		The positioner is in motor initialization mode
	DATUM_ALPHA_INITIALIZED: uint64
		The alpha motor has been initialized
	DATUM_BETA_INITIALIZED: uint64
		The beta motor has been initialized
	HALL_ALPHA_DISABLE: uint64
		The alpha motor hall sensors are configured to not be updated
	HALL_BETA_DISABLE: uint64
		The beta motor hall sensors are configured to not be updated
	COGGING_CALIBRATION: uint64
		The positioner is in cogging calibration mode
	COGGING_ALPHA_CALIBRATED: uint64
		The alpha cogging has been calibrated
	COGGING_BETA_CALIBRATED: uint64
		The beta cogging has been calibrated
	ESTIMATED_POSITION: uint64
		The current position is an estimated position and not the exact one
	POSITION_RESTORED: uint64
		The current position has been restored after a power loss
	SWITCH_OFF_AFTER_MOVE: uint64
		The positioner is configured to switch off the motors after each move
	CALIBRATION_SAVED: uint64
		The internal calibration values (motor, datum, hall) have been saved.
	PRECISE_MOVE_IN_OPEN_LOOP_ALPHA: uint64
		The alpha motor is configured to do its precise move in open loop (if PRECISE_POSITIONING_ALPHA is enabled only)
	PRECISE_MOVE_IN_OPEN_LOOP_BETA: uint64
		The beta motor is configured to do its precise move in open loop (if PRECISE_POSITIONING_BETA is enabled only)
	SWITCH_OFF_HALL_AFTER_MOVE: uint64
		The positioner is configured to power down the hall sensors after each move.

	Methods
	-------
	__init__:
		Initializes the class instances
	get_register_attributes:
		Returns a string with each property status
	get_indexes_from_register:
		Returns a list of all the true elements in the status.
	get_register_from_indexes:
		Returns the register from a list of indexes.

	"""

	__slots__ = (	'SYSTEM_INITIALIZED',\
					'CONFIG_CHANGED',\
					'BSETTINGS_CHANGED',\
					'DATA_STREAMING',\
					'RECEIVING_TRAJECTORY',\
					'TRAJECTORY_ALPHA_RECEIVED',\
					'TRAJECTORY_BETA_RECEIVED',\
					'LOW_POWER_AFTER_MOVE',\
					'DISPLACEMENT_COMPLETED',\
					'DISPLACEMENT_COMPLETED_ALPHA',\
					'DISPLACEMENT_COMPLETED_BETA',\
					'COLLISION_ALPHA',\
					'COLLISION_BETA',\
					'CLOSED_LOOP_ALPHA',\
					'CLOSED_LOOP_BETA',\
					'PRECISE_POSITIONING_ALPHA',\
					'PRECISE_POSITIONING_BETA',\
					'COLLISION_DETECT_ALPHA_DISABLE',\
					'COLLISION_DETECT_BETA_DISABLE',\
					'MOTOR_CALIBRATION',\
					'MOTOR_ALPHA_CALIBRATED',\
					'MOTOR_BETA_CALIBRATED',\
					'DATUM_CALIBRATION',\
					'DATUM_ALPHA_CALIBRATED',\
					'DATUM_BETA_CALIBRATED',\
					'DATUM_INITIALIZATION',\
					'DATUM_ALPHA_INITIALIZED',\
					'DATUM_BETA_INITIALIZED',\
					'HALL_ALPHA_DISABLE',\
					'HALL_BETA_DISABLE',\
					'COGGING_CALIBRATION',\
					'COGGING_ALPHA_CALIBRATED',\
					'COGGING_BETA_CALIBRATED',\
					'ESTIMATED_POSITION',\
					'POSITION_RESTORED',\
					'SWITCH_OFF_AFTER_MOVE',\
					'CALIBRATION_SAVED',\
					'PRECISE_MOVE_IN_OPEN_LOOP_ALPHA',\
					'PRECISE_MOVE_IN_OPEN_LOOP_BETA',\
					'SWITCH_OFF_HALL_AFTER_MOVE')
	def __init__(self):
		"""Initializes the class instances"""

		# Status register bits for system
		self.SYSTEM_INITIALIZED					= 0x0000000000000001
		self.CONFIG_CHANGED						= 0x0000000000000002
		self.BSETTINGS_CHANGED					= 0x0000000000000004
		self.DATA_STREAMING						= 0x0000000000000008

		# Status register bits for communication
		self.RECEIVING_TRAJECTORY				= 0x0000000000000010
		self.TRAJECTORY_ALPHA_RECEIVED			= 0x0000000000000020
		self.TRAJECTORY_BETA_RECEIVED			= 0x0000000000000040
		self.LOW_POWER_AFTER_MOVE				= 0x0000000000000080

		# Status register bits for positioning
		self.DISPLACEMENT_COMPLETED				= 0x0000000000000100
		self.DISPLACEMENT_COMPLETED_ALPHA		= 0x0000000000000200
		self.DISPLACEMENT_COMPLETED_BETA		= 0x0000000000000400
		self.COLLISION_ALPHA					= 0x0000000000000800
		self.COLLISION_BETA						= 0x0000000000001000
		self.CLOSED_LOOP_ALPHA					= 0x0000000000002000
		self.CLOSED_LOOP_BETA					= 0x0000000000004000
		self.PRECISE_POSITIONING_ALPHA			= 0x0000000000008000
		self.PRECISE_POSITIONING_BETA			= 0x0000000000010000
		self.COLLISION_DETECT_ALPHA_DISABLE		= 0x0000000000020000
		self.COLLISION_DETECT_BETA_DISABLE		= 0x0000000000040000
		
		self.MOTOR_CALIBRATION					= 0x0000000000080000
		self.MOTOR_ALPHA_CALIBRATED				= 0x0000000000100000
		self.MOTOR_BETA_CALIBRATED				= 0x0000000000200000
		self.DATUM_CALIBRATION					= 0x0000000000400000
		self.DATUM_ALPHA_CALIBRATED				= 0x0000000000800000
		self.DATUM_BETA_CALIBRATED				= 0x0000000001000000
		self.DATUM_INITIALIZATION				= 0x0000000002000000
		self.DATUM_ALPHA_INITIALIZED			= 0x0000000004000000
		self.DATUM_BETA_INITIALIZED				= 0x0000000008000000
		self.HALL_ALPHA_DISABLE					= 0x0000000010000000
		self.HALL_BETA_DISABLE					= 0x0000000020000000

		self.COGGING_CALIBRATION				= 0x0000000040000000
		self.COGGING_ALPHA_CALIBRATED			= 0x0000000080000000
		self.COGGING_BETA_CALIBRATED			= 0x0000000100000000

		self.ESTIMATED_POSITION					= 0x0000000200000000
		self.POSITION_RESTORED					= 0x0000000400000000

		self.SWITCH_OFF_AFTER_MOVE				= 0x0000000800000000
		self.CALIBRATION_SAVED 					= 0x0000001000000000
		
		self.PRECISE_MOVE_IN_OPEN_LOOP_ALPHA 	= 0x0000002000000000
		self.PRECISE_MOVE_IN_OPEN_LOOP_BETA 	= 0x0000004000000000
		
		self.SWITCH_OFF_HALL_AFTER_MOVE 		= 0x0000008000000000

	def get_register_attributes(self,status):
		"""
		Returns a string with each property status.
		Each property of the status is named with its current status ("SYSTEM_INITIALIZED : True", and so on...)

		Parameters
		----------
		status: uint64
			A 64 bits number representing the register status

		Returns
		-------
		string: the string with each property explicited

		"""
		maxLen = max([len(slot) for slot in self.__slots__])
		string = f''
		for slot in self.__slots__:
			string += f'\n{slot:{maxLen+2}s} : {bool(status&getattr(self, slot))}'

		return string

	def get_indexes_from_register(self,status):
		"""
		Returns a list of all the true elements in the status.
		
		Parameters
		----------
		status: uint64
			A 64 bits number representing the register status

		Returns
		-------
		list of int: list containing all the set bits of the register

		"""
		output = []
		i = 0
		for slot in self.__slots__:
			if bool(status&getattr(self, slot)):
				output.append(i)
			i+=1

		return output

	def get_register_from_indexes(self,indexes):
		"""
		Returns the register from a list of indexes.
		
		Parameters
		----------
		indexes: list of int
			The list of all the set bits indexes of the register

		Returns
		-------
		status: A 64 bits number representing the register status

		"""
		status = 0
		i = 0
		for slot in self.__slots__:
			if i in indexes:
				status += getattr(self, slot)
			i+=1

		return status

class BootloaderStatusRegistery:
	"""
	The bootloader status registry of the positioner.

	Each parameter of the positioner's status registry in bootloader operation mode is listed here. These are read-only values and must not be modified.

	Attributes
	----------
	BOOTLOADER_INIT: uint32
		The bootloader is initialized properly
	BOOTLOADER_TIMEOUT: uint32
		The bootloader timed out. The positioner will boot to the main firmware
	BSETTINGS_CHANGED: uint32
		The bootloader settings have changed
	RECEIVING_NEW_FIRMWARE: uint32
		A new firmware is being received
	NEW_FIRMWARE_RECEIVED: uint32
		The new firmware was received
	NEW_FIRMWARE_CHECK_OK: uint32
		The new firmware is valid and will be used as main firmware
	NEW_FIRMWARE_CHECK_BAD: uint32
		The new firmware is invalid and will be dismissed

	Methods
	-------
	__init__:
		Initializes the class instances
	get_register_attributes:
		Returns a string with each property status
	get_indexes_from_register:
		Returns a list of all the true elements in the status.
	get_register_from_indexes:
		Returns the register from a list of indexes.

	"""

	__slots__ = (	'BOOTLOADER_INIT',\
					'BOOTLOADER_TIMEOUT',\
					'BSETTINGS_CHANGED',\
					'RECEIVING_NEW_FIRMWARE',\
					'NEW_FIRMWARE_RECEIVED',\
					'NEW_FIRMWARE_CHECK_OK',\
					'NEW_FIRMWARE_CHECK_BAD')

	def __init__(self):
		"""Initializes the class instances"""

		self.BOOTLOADER_INIT 			= 0x00000001
		self.BOOTLOADER_TIMEOUT 		= 0x00000002
		self.BSETTINGS_CHANGED 			= 0x00000200
		self.RECEIVING_NEW_FIRMWARE 	= 0x00001000
		self.NEW_FIRMWARE_RECEIVED 		= 0x01000000
		self.NEW_FIRMWARE_CHECK_OK 		= 0x02000000
		self.NEW_FIRMWARE_CHECK_BAD 	= 0x04000000

	def get_register_attributes(self,status):
		"""
		Returns a string with each property status.
		Each property of the status is named with its current status ("BOOTLOADER_INIT : True", and so on...)

		Parameters
		----------
		status: uint32
			A 32 bits number representing the register status

		Returns
		-------
		string: the string with each property explicited

		"""
		maxLen = max([len(slot) for slot in self.__slots__])
		string = f''
		for slot in self.__slots__:
			string += f'\n{slot:{maxLen+2}s} : {bool(status&getattr(self, slot))}'

		return string

	def get_indexes_from_register(self,status):
		"""
		Returns a list of all the true elements in the status.
		
		Parameters
		----------
		status: uint32
			A 32 bits number representing the register status

		Returns
		-------
		list of int: list containing all the set bits of the register

		"""
		output = []
		i = 0
		for slot in self.__slots__:
			if bool(status&getattr(self, slot)):
				output.append(i)
			i+=1

		return output

	def get_register_from_indexes(self,indexes):
		"""
		Returns the register from a list of indexes.
		
		Parameters
		----------
		indexes: list of int
			The list of all the set bits indexes of the register

		Returns
		-------
		status: A 32 bits number representing the register status

		"""
		status = 0
		i = 0
		for slot in self.__slots__:
			if i in indexes:
				status += getattr(self, slot)
			i+=1

		return status

class BootloaderParameters:
	"""
	The bootloader factory parameter indexes.

	Each parameter of the positioner's factory parameters in bootloader operation mode is listed here. These are read-only values and must not be modified.

	Attributes
	----------
	POSITIONER_ID: uint32
		Positioner CAN ID
	POWER_LED_CONTROL: uint32
		Power LED control
	FIBRE_TYPE: uint32
		Fibre type installed
	ALPHA_REDUCTION: uint32
		alpha reduction ratio
	BETA_REDUCTION: uint32
		beta reduction ratio
	ALPHA_MODEL: uint32
		alpha model type
	BETA_MODEL: uint32
		beta model type
	ALPHA_CONTROL: uint32
		alpha control type
	BETA_CONTROL: uint32
		beta control type
	ALPHA_POLARITY: uint32
		alpha polarity
	BETA_POLARITY: uint32
		beta polarity
	ALPHA_MAX_SPEED: uint32
		alpha maximum speed
	BETA_MAX_SPEED: uint32
		beta maximum speed
	ALPHA_MAX_CURRENT: uint32
		alpha maximum current
	BETA_MAX_CURRENT: uint32
		beta maximum current
	ALPHA_ENCODER_RESOLUTION: uint32
		alpha encoder resolution
	BETA_ENCODER_RESOLUTION: uint32
		beta encoder resolution
	ALPHA_ENCODER_TYPE: uint32
		alpha encoder type
	BETA_ENCODER_TYPE: uint32
		beta encoder type
	ALPHA_COLLISION_DETECTION: uint32
		alpha collision detection
	BETA_COLLISION_DETECTION: uint32
		beta collision detection
	ALPHA_LOW_POS_LIMIT: uint32
		alpha lower position limit
	ALPHA_HIGH_POS_LIMIT: uint32
		alpha higher position limit
	BETA_LOW_POS_LIMIT: uint32
		beta lower position limit
	BETA_HIGH_POS_LIMIT: uint32
		beta higher position limit
	ALPHA_INTERPOLATION: uint32
		alpha interpolation type
	BETA_INTERPOLATION: uint32
		beta interpolation type
	ALPHA_MAX_ACCELERATION: uint32
		alpha maximum acceleration
	BETA_MAX_ACCELERATION: uint32
		beta maximum acceleration
	ALPHA_TORQUE_LIMIT: uint32
		alpha maximum torque limit
	BETA_TORQUE_LIMIT: uint32
		beta maximum torque limit
	POSITIONER_ROW: uint32
		positioner row position in FPS
	POSITIONER_COL: uint32
		positioner column position in FPS
	RESERVE_01: uint32
		reserve configuration value 01
	RESERVE_02: uint32
		reserve configuration value 02
	RESERVE_03: uint32
		reserve configuration value 03
	RESERVE_04: uint32
		reserve configuration value 04
	RESERVE_05: uint32
		reserve configuration value 05
	RESERVE_06: uint32
		reserve configuration value 06
	RESERVE_07: uint32
		reserve configuration value 07
	RESERVE_08: uint32
		reserve configuration value 08

	Methods
	-------
	__init__:
		Initializes the class instances
	
	"""

	__slots__ = (	'POSITIONER_ID',\
					'POWER_LED_CONTROL',\
					'FIBRE_TYPE',\
					'ALPHA_REDUCTION',\
					'BETA_REDUCTION',\
					'ALPHA_MODEL',\
					'BETA_MODEL',\
					'ALPHA_CONTROL',\
					'BETA_CONTROL',\
					'ALPHA_POLARITY',\
					'BETA_POLARITY',\
					'ALPHA_MAX_SPEED',\
					'BETA_MAX_SPEED',\
					'ALPHA_MAX_CURRENT',\
					'BETA_MAX_CURRENT',\
					'ALPHA_ENCODER_RESOLUTION',\
					'BETA_ENCODER_RESOLUTION',\
					'ALPHA_ENCODER_TYPE',\
					'BETA_ENCODER_TYPE',\
					'ALPHA_COLLISION_DETECTION',\
					'BETA_COLLISION_DETECTION',\
					'ALPHA_LOW_POS_LIMIT',\
					'ALPHA_HIGH_POS_LIMIT',\
					'BETA_LOW_POS_LIMIT',\
					'BETA_HIGH_POS_LIMIT',\
					'ALPHA_INTERPOLATION',\
					'BETA_INTERPOLATION',\
					'ALPHA_MAX_ACCELERATION',\
					'BETA_MAX_ACCELERATION',\
					'ALPHA_TORQUE_LIMIT',\
					'BETA_TORQUE_LIMIT',\
					'POSITIONER_ROW',\
					'POSITIONER_COL',\
					'RESERVE_01',\
					'RESERVE_02',\
					'RESERVE_03',\
					'RESERVE_04',\
					'RESERVE_05',\
					'RESERVE_06',\
					'RESERVE_07',\
					'RESERVE_08')

	def __init__(self):
		"""Initializes the class instances"""
		self.POSITIONER_ID	 				= 0			# 0 Positioner CAN ID
		self.POWER_LED_CONTROL	 			= 1;		# 1 Power LED control
		self.FIBRE_TYPE	 					= 2;		# 2 Fibre type installed
		self.ALPHA_REDUCTION	 			= 3;		# 3 alpha reduction ratio
		self.BETA_REDUCTION	 				= 4;		# 4 beta reduction ratio
		self.ALPHA_MODEL	 				= 5;		# 5 alpha model type
		self.BETA_MODEL	 					= 6;		# 6 beta model type
		self.ALPHA_CONTROL	 				= 7;		# 7 alpha control type
		self.BETA_CONTROL	 				= 8;		# 8 beta control type
		self.ALPHA_POLARITY	 				= 9;		# 9 alpha polarity
		self.BETA_POLARITY	 				= 10;		#10 beta polarity
		self.ALPHA_MAX_SPEED	 			= 11;		#11 alpha maximum speed
		self.BETA_MAX_SPEED	 				= 12;		#12 beta maximum speed
		self.ALPHA_MAX_CURRENT	 			= 13;		#13 alpha maximum current
		self.BETA_MAX_CURRENT	 			= 14;		#14 beta maximum current
		self.ALPHA_ENCODER_RESOLUTION	 	= 15;		#15 alpha encoder resolution
		self.BETA_ENCODER_RESOLUTION	 	= 16;		#16 beta encoder resolution
		self.ALPHA_ENCODER_TYPE	 			= 17;		#17 alpha encoder type
		self.BETA_ENCODER_TYPE	 			= 18;		#18 beta encoder type
		self.ALPHA_COLLISION_DETECTION	 	= 19;		#19 alpha collision detection
		self.BETA_COLLISION_DETECTION	 	= 20;		#20 beta collision detection
		self.ALPHA_LOW_POS_LIMIT	 		= 21;		#21 alpha lower position limit
		self.ALPHA_HIGH_POS_LIMIT	 		= 22;		#22 alpha higher position limit
		self.BETA_LOW_POS_LIMIT	 			= 23;		#23 beta lower position limit
		self.BETA_HIGH_POS_LIMIT	 		= 24;		#24 beta higher position limit
		self.ALPHA_INTERPOLATION	 		= 25;		#25 alpha interpolation type
		self.BETA_INTERPOLATION	 			= 26;		#26 beta interpolation type
		self.ALPHA_MAX_ACCELERATION	 		= 27;		#27 alpha maximum acceleration
		self.BETA_MAX_ACCELERATION	 		= 28;		#28 beta maximum acceleration
		self.ALPHA_TORQUE_LIMIT	 			= 29;		#29 alpha maximum torque limit
		self.BETA_TORQUE_LIMIT	 			= 30;		#30 beta maximum torque limit
		self.POSITIONER_ROW	 				= 31;		#31 positioner row position in FPS
		self.POSITIONER_COL	 				= 32;		#32 positioner column position in FPS
		self.RESERVE_01	 					= 33;		#33 reserve configuration value 01
		self.RESERVE_02	 					= 34;		#34 reserve configuration value 02
		self.RESERVE_03	 					= 35;		#35 reserve configuration value 03
		self.RESERVE_04						= 36;		#36 reserve configuration value 04
		self.RESERVE_05						= 37;		#37 reserve configuration value 05
		self.RESERVE_06	 					= 38;		#38 reserve configuration value 06
		self.RESERVE_07	 					= 39;		#39 reserve configuration value 07
		self.RESERVE_08	 					= 40;		#40 reserve configuration value 08

class CAN_Options:
	"""
	The CAN channel configuration parameters.
	These are read-only values and must not be modified, except for the CAN_VCP_PORT that is automatically filled during the CAN initialization (classCanCom.COM_handle.init)

	Attributes
	----------
	CAN_BAUDRATE: uint
		The CAN baudrate
	CAN_BUFFER: uint
		The data buffer size
	CAN_TIMEOUT: uint
		The CAN timeout in seconds
	CAN_VCP_PORT: int
		The port number
	CAN_ID_BIT_SHIFT: uint
		Bits to shift to input the ID in the header
	CAN_CMD_BIT_SHIFT: uint
		Bits to shift to input the command in the header
	TimeChannelSize: uint
		The data size in Bytes
	DataChannelNumel: uint
		The number of channels
	DataChannelSize: uint
		The data size in Bytes
	PacketSize: uint
		The packet size

	"""

	CAN_BAUDRATE 		= 1000000	#Baud rate
	CAN_BUFFER 			= 2**16		#Data buffer size
	CAN_TIMEOUT 		= 2			#Maximal answer waiting time [s]
	CAN_VCP_PORT		= -1		#Default initialization
	CAN_ID_BIT_SHIFT 	= 18		#Bits to shift to get ID
	CAN_CMD_BIT_SHIFT 	= 10		#Bits to shift to input the command
	TimeChannelSize		= 4			#Data size [byte]
	DataChannelNumel	= 5			#Number of channels
	DataChannelSize		= 4			#Data size [byte]
	PacketSize			= TimeChannelSize + DataChannelNumel*DataChannelSize

class RX_Options:
	"""
	The CAN input-output command IDs.
	These are read-only values and must not be modified.

	Attributes
	----------
	ABORT_ALL: uint
		The command ID to abort all the ongoing actions on the positioner
	GET_ID: uint
		The command ID to retrieve the ID of the positioner
	GET_FIRMWARE_VERSION: uint
		The command ID to retrieve the current firmware version of the positioner
	GET_STATUS: uint
		The command ID to retrieve the current state of the status registry of the positioner
	SET_STATUS_LOW: uint
		The command ID to set the 32 low bits of the status registry of the positioner
	SET_STATUS_HIGH: uint
		The command ID to set the 32 high bits of the status registry of the positioner
	SET_DEBUG_ALPHA: uint
		The command ID to set the debug mode for the alpha motor													TODO
	SET_DEBUG_BETA: uint
		The command ID to set the debug mode for the beta motor														TODO
	SEND_TRAJECTORY_NEW: uint
		The command ID to send a new trajectory to the positioner
	SEND_TRAJECTORY_DATA: uint
		The command ID to send a trajectory point to the positioner
	SEND_TRAJECTORY_DATA_END: uint
		The command ID to end the trajectory sending
	SEND_TRAJECTORY_ABORT: uint
		The command ID to abort the trajectory sending
	START_TRAJECTORY: uint
		The command ID to start the movement of the trajectory
	STOP_TRAJECTORY: uint
		The command ID to stop the movement of the positioner
	START_REVERSE_TRAJECTORY: uint
		The command ID to perform the previously sent trajectory in reverse order
	START_DEMO_TRAJECTORY: uint
		The command ID to start a demo trajectory for demonstration
	FATAL_ERROR_COLLISION: uint
		The interruption sent by the positioner when a collision is detected
	GET_DATUM_CALIB_OFFSET: uint
		The command ID to retrieve the datum calibration offset between the hardstop and the motor hall
	INIT_DATUM: uint
		The command ID to initialize the datums
	INIT_DATUM_ALPHA: uint
		The command ID to initialize the datums of the alpha motor
	INIT_DATUM_BETA: uint
		The command ID to initialize the datums of the beta motor
	START_DATUM_CALIBRATION: uint
		The command ID to start the datum calibration
	START_DATUM_CALIBRATION_ALPHA: uint
		The command ID to start the datum calibration of the alpha motor
	START_DATUM_CALIBRATION_BETA: uint
		The command ID to start the datum calibration of the beta motor
	START_MOTOR_CALIBRATION: uint
		The command ID to start the motor calibration
	START_MOTOR_CALIBRATION_ALPHA: uint
		The command ID to start the motor calibration of the alpha motor
	START_MOTOR_CALIBRATION_BETA: uint
		The command ID to start the motor calibration of the beta motor
	GET_DATUM_CALIB_ERROR: uint
		The command ID to retrieve the datum calibration errors
	GOTO_POSITION_ABSOLUTE: uint
		The command ID to move to an absolute position
	GOTO_POSITION_RELATIVE: uint
		The command ID to move to a relative position
	GET_ACTUAL_POSITION: uint
		The command ID to retrieve the current position of the positioner
	SET_ACTUAL_POSITION: uint
		The command ID to overwrite the current position of the positioner
	GET_OFFSET: uint
		The command ID to retrieve the offset (angle from datum to 0) of the positioner's axis 
	SET_OFFSET: uint
		The command ID to overwrite the offset (angle from datum to 0) of the positioner's axis 
	START_PRECISE_MOVE: uint
		The command ID to 																							TODO
	START_PRECISE_MOVE_ALPHA: uint
		The command ID to 																							TODO
	START_PRECISE_MOVE_BETA: uint
		The command ID to 																							TODO
	SET_APPROACH_DISTANCE: uint
		The command ID to change the approach angle
	SET_SPEED: uint
		The command ID to change the positioner cruise speed
	SET_CURRENT: uint
		The command ID to change the open loop current
	GET_MOTOR_HALL_POS: uint
		The command ID to retrieve the current position of the positioner as reported by the hall sensors
	GET_MOTOR_CALIBRATION_ERROR: uint
		The command ID to retrieve the morot calibration error
	RESET_All_POSITIONS: uint
		The command ID to 																							TODO
	START_COGGING_CALIBRATION: uint
		The command ID to start the cogging measurement
	START_COGGING_CALIBRATION_ALPHA: uint
		The command ID to start the cogging measurement of the alpha motor
	START_COGGING_CALIBRATION_BETA: uint
		The command ID to start the cogging measurement of the beta motor
	SAVE_INTERNAL_CALIBRATION: uint
		The command ID to save the internal calibration in the flash memory
	GET_CURRENT_AND_POS_ALPHA: uint
		The command ID to retrieve the current position and current of the alpha motor
	GET_CURRENT_AND_POS_BETA: uint
		The command ID to retrieve the current position and current of the beta motor
	GET_CURRENT: uint
		The command ID to retrieve the current current of the positioner motors
	GET_CMD_TORQUE_AND_POS_ALPHA: uint
		The command ID to retrieve the current command torque and position of the alpha motor 						TODO
	GET_CMD_TORQUE_AND_POS_BETA: uint
		The command ID to retrieve the current command torque and position of the beta motor 						TODO
	GET_CMD_TORQUE: uint
		The command ID to retrieve the current command torque of the positioner 									TODO
	SET_FACTORY_SETTING: uint
		The command ID to change a factory setting
	GET_FACTORY_SETTING: uint
		The command ID to get a factory setting
	READ_EXT_FLASH: uint
		The command ID to read the external flash memory
	WRITE_EXT_FLASH: uint
		The command ID to write to the external flash memory
	ERASE_EXT_FLASH: uint
		The command ID to erase the external flash memory
	GET_ALPHA_HALL_CALIB: uint
		The command ID to request the alpha hall sensors calibration values
	GET_BETA_HALL_CALIB: uint
		The command ID to request the beta hall sensors calibration values
	REQUEST_NB_COGGING_PTS: uint
		The command ID to request the number of points of the cogging measurement
	REQUEST_COGGING_CURVE_POS: uint
		The command ID to request the positive cogging curve data
	REQUEST_COGGING_CURVE_NEG: uint
		The command ID to request the negative cogging curve data
	REQUEST_COGGING_CURVE_HOLD: uint
		The command ID to request the holding cogging curve data
	REQUEST_COGGING_POSITION: uint
		The command ID to request the position of the cogging data
	CHANGE_COLLISION_MARGIN: uint
		The command ID to change the closed loop current offset
	CHANGE_HOLDING_CURRENT: uint
		The command ID to change the holding current value
	SEND_NEW_FIRMWARE: uint
		The command ID to start the sending of a new firmware (bootloader only)
	FIRMWARE_DATA: uint
		The command ID to send a firmware data piece (bootloader only)
	FIRMWARE_ABORT: uint
		The command ID to abort a firmware sending (bootloader only)
	GET_BOOTLOADER_VERSION: uint
		The command ID to retrieve the current bootloader version (bootloader only)
	GET_MAIN_VERSION: uint
		The command ID to retrieve the current main firmware version (bootloader only)
	GET_BACKUP_VERSION: uint
		The command ID to retrieve the current backup firmware version (bootloader only)
	REQUEST_REBOOT: uint
		The command ID to request the positioner to reset
	REQUEST_BOOT: uint
		The command ID to the positioner to exit the bootloader
	GET_ROOT_ACCESS: uint
		The command ID to get root access for certain parameters (bootloader only)
	COMMAND_ACCEPTED: uint
		The return code ID if the command was accepted
	VALUE_OUT_OF_RANGE: uint
		The return code ID if the command contained out of range data
	INVALID_TRAJECTORY: uint
		The return code ID if the trajectory is invalid
	ALREADY_IN_MOTION: uint
		The return code ID if the positioner is already moving
	NOT_INITIALIZED: uint
		The return code ID if the positioner is not initialized
	INCORRECT_AMOUNT_OF_DATA: uint
		The return code ID if the wrong amount of data has been provided
	CALIBRATION_MODE_ACTIVE: uint
		The return code ID if a calibration is in progress
	MOTOR_NOT_CALIBRATED: uint
		The return code ID if the motors are not calibrated
	COLLISION_DETECTED: uint
		The return code ID if a collision was detected
	HALL_SENSOR_DISABLED: uint
		The return code ID if the hall sensors are disabled
	INVALID_BROADCAST_COMMAND: uint
		The return code ID if the command cannot be broadcasted
	INVALID_BOOTLOADER_COMMAND: uint
		The return code ID if the command ID is invalid in bootloader mode
	INVALID_COMMAND: uint
		The return code ID if the command ID is invalid
	UNKNOWN_COMMAND: uint
		The return code ID if the command ID is unknown
	DATUM_NOT_CALIBRATED: uint
		The return code ID if the datum are not calibrated

	Methods
	-------
	get_err_description:
		Returns the return parameter name from its ID

	"""

	ABORT_ALL						= 0		# abort all
	GET_ID							= 1		# requests positioner ID
	GET_FIRMWARE_VERSION			= 2		# requests actual firmware version of positioner
	GET_STATUS						= 3		# requests for deviceStatus register
	SET_STATUS_LOW					= 4		# set status registers, low bits
	SET_STATUS_HIGH					= 5		# set status registers, high bits
	SET_DEBUG_ALPHA 				= 6
	SET_DEBUG_BETA 					= 7
	SEND_TRAJECTORY_NEW				= 10	# request for sending a new trajectory
	SEND_TRAJECTORY_DATA			= 11	# sends trajectory points (int32_t position, uint32_t time)
	SEND_TRAJECTORY_DATA_END		= 12	# sends end trajectory transmission to validate sent trajectories
	SEND_TRAJECTORY_ABORT			= 13	# aborts trajectory transmission, will reset all trajectories stored 
	START_TRAJECTORY				= 14	# starts actual trajectory
	STOP_TRAJECTORY					= 15	# stops actual trajectory
	START_REVERSE_TRAJECTORY 		= 16
	START_DEMO_TRAJECTORY 			= 17
	FATAL_ERROR_COLLISION 			= 18 	# Command the positionner sends if it detects a collision
	GET_DATUM_CALIB_OFFSET 			= 19
	INIT_DATUM						= 20	# init datums
	INIT_DATUM_ALPHA				= 21	# init datum alpha
	INIT_DATUM_BETA					= 22	# init datum beta
	START_DATUM_CALIBRATION			= 23	# calib datums
	START_DATUM_CALIBRATION_ALPHA	= 24	# calib datum alpha
	START_DATUM_CALIBRATION_BETA	= 25	# calib datum beta
	START_MOTOR_CALIBRATION			= 26	# 
	START_MOTOR_CALIBRATION_ALPHA	= 27	# 
	START_MOTOR_CALIBRATION_BETA	= 28	# 
	GET_DATUM_CALIB_ERROR 			= 29
	GOTO_POSITION_ABSOLUTE			= 30	# goto absolute position
	GOTO_POSITION_RELATIVE			= 31	# goto absolute position
	GET_ACTUAL_POSITION				= 32	# requests actual position
	SET_ACTUAL_POSITION				= 33	# sets the actual position
	GET_OFFSET						= 34
	SET_OFFSET						= 35
	START_PRECISE_MOVE				= 36	# start precise maneuver
	START_PRECISE_MOVE_ALPHA		= 37	# start precise maneuver alpha
	START_PRECISE_MOVE_BETA			= 38	# start precise maneuver beta
	SET_APPROACH_DISTANCE 			= 39 	# sets approach distyances in steps
	SET_SPEED						= 40	# sets movement speed in rpm
	SET_CURRENT						= 41	# sets the open loop current
	GET_MOTOR_HALL_POS				= 44	# get hall position relative to the motor 
	GET_MOTOR_CALIBRATION_ERROR		= 45	# get hall calibration error
	RESET_All_POSITIONS				= 46	# set all positions to 0: offset, actualposition, commandedposition hardstop_offset
	START_COGGING_CALIBRATION		= 47	# 
	START_COGGING_CALIBRATION_ALPHA	= 48	# 
	START_COGGING_CALIBRATION_BETA	= 49	# 

	SAVE_INTERNAL_CALIBRATION 		= 53 	# Saves the internal calibration parameters (motor, datum, cogging) in the flash memory
	GET_CURRENT_AND_POS_ALPHA 		= 54
	GET_CURRENT_AND_POS_BETA 		= 55
	GET_CURRENT 					= 56
	GET_CMD_TORQUE_AND_POS_ALPHA 	= 57
	GET_CMD_TORQUE_AND_POS_BETA 	= 58
	GET_CMD_TORQUE 					= 59

	SET_FACTORY_SETTING				= 60	# sets a factory setting @ref config_parameter_t
	GET_FACTORY_SETTING				= 61	# gets a factory setting @ref config_parameter_t
	READ_EXT_FLASH					= 101	# read value from external flash (uint32_t address)
	WRITE_EXT_FLASH					= 102	# writes value to external flash (uint32_t address and uint32_t value)
	ERASE_EXT_FLASH					= 103	# erases external flash
	GET_ALPHA_HALL_CALIB			= 104	# request alpha hall sensors calibration values (4 x uint16_t maxA, maxB, minA, minB)
	GET_BETA_HALL_CALIB				= 105	# request beta hall sensors calibration values (4 x uint16_t maxA, maxB, minA, minB)
	REQUEST_NB_COGGING_PTS 			= 106 	# Request for the amount of cogging calibration points
	REQUEST_COGGING_CURVE_POS		= 107 	# Get the cogging torque value of the specified index (holding current)
	REQUEST_COGGING_CURVE_NEG		= 108 	# Get the cogging torque value of the specified index (slipping current)
	REQUEST_COGGING_CURVE_HOLD		= 109	# Get the cogging torque value of the specified index (mean current)
	REQUEST_COGGING_POSITION 		= 110	# Get the position of the specified index of cogging torque
	CHANGE_COLLISION_MARGIN 		= 111 	# Changes the maximal amount of current that can be supplied to the motors in closed loop
	CHANGE_HOLDING_CURRENT 			= 112 	# Changes the current supplied to the motors when they are not moving

	SEND_NEW_FIRMWARE 				= 200	# send new firmware (size (uint32_t) and CRC32 (uint32_t))
	FIRMWARE_DATA 					= 201	# firmware data (8 bytes of data or less if last chunk)
	FIRMWARE_ABORT 					= 202	# firmware upgrade abort (no data)

	GET_BOOTLOADER_VERSION 			= 210	# request bootloader version from settings (no data)
	GET_MAIN_VERSION 				= 211	# request main firmware version from settings (no data)
	GET_BACKUP_VERSION 				= 212	# request backup firmware version from settings (no data)
	REQUEST_REBOOT 					= 213	# requests reboot to go into bootloader
	REQUEST_BOOT 					= 214 	# requests the positioner to exit the bootloader
	GET_ROOT_ACCESS 				= 222	# requests root access to be able to changed parameters (only available in bootloader)

	#list of return codes
	COMMAND_ACCEPTED				= 0		# command accepted
	VALUE_OUT_OF_RANGE				= 1		# value out of range
	INVALID_TRAJECTORY				= 2		# invalid trajectory
	ALREADY_IN_MOTION				= 3		# already in motion
	NOT_INITIALIZED					= 4		# not initialized
	INCORRECT_AMOUNT_OF_DATA		= 5		# incorrect amount of data received
	CALIBRATION_MODE_ACTIVE 		= 6		# one of the calibration modes is active: MOTOR_CALIBRATION, COGGING_CALIBRATION, DATUM_CALIBRATION, DATUM _INITIALIZATION
	MOTOR_NOT_CALIBRATED 			= 7		# the motors are not calibrated and therefore the hall sensors can't be used
	COLLISION_DETECTED 				= 8		# a collision is detected, the flag has to be first cleared with stop trajectory
	HALL_SENSOR_DISABLED 			= 9		# hall sensors are disabled and can therefore not be used
	INVALID_BROADCAST_COMMAND		= 10	# invalid broadcast command
	INVALID_BOOTLOADER_COMMAND		= 11	# invalid bootloader command
	INVALID_COMMAND					= 12	# invalid command
	UNKNOWN_COMMAND					= 13	# unknown command
	DATUM_NOT_CALIBRATED 			= 14	# datum not calibrated

	def get_err_description(self,errCode):
		"""
		Returns the return code's name from its ID.

		The return code ID is contained in the response communication from the positioner
		
		Parameters
		----------
		errCode: int
			The return code ID returned by the positioner
		
		Returns
		-------
		string: the return parameter name

		"""

		if errCode == self.COMMAND_ACCEPTED:
			return 'COMMAND_ACCEPTED'
		elif errCode == self.VALUE_OUT_OF_RANGE:
			return 'VALUE_OUT_OF_RANGE'
		elif errCode == self.INVALID_TRAJECTORY:
			return 'INVALID_TRAJECTORY'
		elif errCode == self.ALREADY_IN_MOTION:
			return 'ALREADY_IN_MOTION'
		elif errCode == self.NOT_INITIALIZED:
			return 'NOT_INITIALIZED'
		elif errCode == self.INCORRECT_AMOUNT_OF_DATA:
			return 'INCORRECT_AMOUNT_OF_DATA'
		elif errCode == self.CALIBRATION_MODE_ACTIVE:
			return 'CALIBRATION_MODE_ACTIVE'
		elif errCode == self.MOTOR_NOT_CALIBRATED:
			return 'MOTOR_NOT_CALIBRATED'
		elif errCode == self.COLLISION_DETECTED:
			return 'COLLISION_DETECTED'
		elif errCode == self.HALL_SENSOR_DISABLED:
			return 'HALL_SENSOR_DISABLED'
		elif errCode == self.INVALID_BROADCAST_COMMAND:
			return 'INVALID_BROADCAST_COMMAND'
		elif errCode == self.INVALID_BOOTLOADER_COMMAND:
			return 'INVALID_BOOTLOADER_COMMAND'
		elif errCode == self.INVALID_COMMAND:
			return 'INVALID_COMMAND'
		elif errCode == self.UNKNOWN_COMMAND:
			return 'UNKNOWN_COMMAND'
		elif errCode == self.DATUM_NOT_CALIBRATED:
			return 'DATUM_NOT_CALIBRATED'
		elif errCode == self.FATAL_ERROR_COLLISION:
			return 'FATAL_COLLISION_INTERRUPT'
		else:
			return 'UNKNOWN_ERROR'

class COM_Options:
	"""
	The grouping of all the communication configuration parameters

	Attributes
	----------
	COM: classCanCom.CAN_Options
		The CAN options
	RX: classCanCom.RX_Options
		The input-output parameters
	STREG: classCanCom.StatusRegistry
		The status registry parameters
	BSTREG:	classCanCom.BootloaderStatusRegistry
		The bootloader status registry parameters

	"""

	COM	= CAN_Options()
	RX	= RX_Options()
	STREG	= StatusRegistery()
	BSTREG 	= BootloaderStatusRegistery()
	BPARAM  = BootloaderParameters()

class COM_handle:
	"""
	The communicaiton handle class.

	It holds all the parameters and the configuration for a correct communication. This class also contains all the communication functions.

	Attributes
	----------
	_OPT: classCanCom.COM_Options
		The communication configuration parameters
	serHandle: serial.Serial
		The serial handle for the communication
	serialNo: string
		The serial number of the CAN-USB transciever
	initialized: bool
		The CAN channel is operationnal
	invalidIDs: list of int
		The list of positioner IDs that got a communicaiton error

	Methods
	-------
	__init__:
		Initializes the class instances
	get_all_serial_no:
		Returns all the available connected CAN-USB transievers serial numbers
	init:
		Initializes the serial handle
	close:
		Closes the active CAN channel
	add_invalid_ID:
		Adds a positioner to the invalid IDs list
	reset_invalidIDs:
		Resets the list of invalid IDs
	CAN_write:
		Performs a communication with the positioners.
	send_full_status:
		Sends a full 64bit status register to the positioner.
	send_half_status:
		Sends a 32 bit register part to the positioner
	send_CAN:
		Sends a CAN communication to the positioner(s)
	receive_CAN:
		Recieves a CAN communication from the positioner(s)
	get_errcode:
		Returns the response codes' names for each message in "messages".

	"""

	__slots__	= (	'_OPT',\
					'serHandle',\
					'serialNo',\
					'initialized',\
					'invalidIDs')

	def __init__(self):
		"""Initializes the class instances"""

		self._OPT	= COM_Options()
		self.serHandle	= None
		self.serialNo	= []
		self.invalidIDs = []

	def get_all_serial_no(self):
		"""
		Returns all the available connected CAN-USB transievers serial numbers

		Returns
		-------
		serialNumbers: list of string
			A list of the available CAN-USB serial numbers

		"""

		#Get available COM ports
		serialNumbers	= []
		serial_list	= list(list_ports.comports())
		if not serial_list:
			return serialNumbers

		serialHandle = None

		#Get COM port which description corresponds to 'USB' that are not already opened
		for port_no, description, device in serial_list:
			if 'USB' in description:
				try:
					serialHandle = serial.Serial(port_no)
				except serial.SerialException:
					pass
				
				if serialHandle is not None:
					try:
						#Retrieve the serial number
						serialHandle.reset_input_buffer()
						serialHandle.write('N\r'.encode())

						time.sleep(DEFINES.CAN_DELAY_BETWEEN_CONFIG_COMMANDS)

						input_buffer	= serialHandle.readline(serialHandle.inWaiting())
						#store the serial number
						if len(input_buffer.decode())	== 6:
							result	= str(input_buffer[1:5].decode())
							serialNumbers.append(result)

						serialHandle.close()
					except serial.SerialException:
						pass

		return serialNumbers

	def init(self, desiredSerial = None):
		"""
		Initializes the serial handle

		This connects to the desired CAN-USB and configures it.

		Parameters
		----------
		desiredSerial: string
			The serial number of the desired CAN-USB device. If None or left blank, the first device found will be selected.

		Raises
		------
		errors.CANError:
			If no COM port is available
			If an error occured during the device configuration

		"""

		#Reset values
		if self.serHandle is None or not (self.serialNo	== desiredSerial):
			#If a CAN-USB is already connected, close the connexion
			if self.serHandle is not None:
				self.close()			

			#Get available COM ports
			serial_list	= list(list_ports.comports())
			if not serial_list:
				raise errors.CANError("No COM port available") from None

			#Get COM port which description corresponds to 'USB' and with the desired serial number
			for port_no, description, device in serial_list:
				if 'USB' in description:
					try:
						self.serHandle	= serial.Serial(port_no)
					except serial.SerialException:
						self.serHandle	= None

					if self.serHandle is not None: #If the connexion was successful
						try:
							serialNo	= self.CAN_write(0,'get_serial_number',[])
						except errors.CANError as e:
							self.close()
							# raise e from None
						else:
							if serialNo[0]	== desiredSerial or desiredSerial	== None:
								self.serialNo	= serialNo[0]
								self._OPT.COM.CAN_VCP_PORT	= port_no
								break
							self.close()		

			#If no device matches the description, exit
			if self.serHandle is None:
				raise errors.CANError("CAN initialization could not connect to the requested device") from None

			#Initialize the serial port parameters
			try:
				self.serHandle.baudrate	= self._OPT.COM.CAN_BAUDRATE
				self.serHandle.bytesize	= serial.EIGHTBITS
				self.serHandle.timeout	= self._OPT.COM.CAN_TIMEOUT

				self.reset_invalidIDs()

				#flush all the buffers
				self.CAN_write(0,'clearbuffer',[])

				#Initialize the CAN bus
				self.CAN_write(0,'init',[])
			except errors.CANError as e:
				self.close()
				raise e from None

	#Closes the CAN communication
	def close(self):
		"""Closes the active CAN channel"""

		if self.serHandle is not None:
			try:
				self.serHandle.close()
			except serial.SerialException:
				pass
		self.serHandle	= None
		self.serialNo	= ''

	def add_invalid_ID(self, ID, errorMessage = 'UNDEFINED_ERROR'):
		"""
		Adds a positioner to the invalid IDs list

		It will first try to stop the positioner send it back to the origin, and then it will stop all the communications with this positioner.

		Parameters
		----------
		ID: int
			The ID of the positioner to add to the invalid list
		errorMessage: string
			The reason the positioner is flagged as invalid.

		"""

		if ID>0 and ID not in self.invalidIDs:
			#Try to go to 0,0
			try:
				data = {'speedAlpha': 500, 'speedBeta': 500,\
						'currentAlpha': 40, 'currentBeta': 40,\
						'R1Steps': 0, 'R2Steps': 0}

				self.CAN_write(ID, 'stop_trajectory', allowIDInvalidation = False)
				self.CAN_write(ID, 'reset_collision_flags', allowIDInvalidation = False)
				self.CAN_write(ID, 'set_openloop_current', data, allowIDInvalidation = False)
				self.CAN_write(ID, 'set_speed', data, allowIDInvalidation = False)
				self.CAN_write(ID, 'goto_position_absolute', data, allowIDInvalidation = False)
			except:
				pass

			#Try to reboot
			try:
				self.CAN_write(ID, 'reboot', [], allowIDInvalidation = False)
			except:
				pass

			#Add the positioner to the invalid IDs list
			self.invalidIDs.append(ID)
			
	def reset_invalidIDs(self):
		"""Resets the list of invalid IDs"""
		self.invalidIDs = []

	#Sends a command via the CAN bus
	#Returns the received data
	def CAN_write(self, ID, command, data, allowIDInvalidation = True):
		"""
		Performs a communication with the positioners.

		The list of available commands are in the 'Other parameters' section.

		Parameters
		----------
		ID: uint
			The ID of the positioner to communicate with. If the command is broadcastable, use ID=0 to broadcast it to every positioner.
		command: string
			The command that should be sent. See the 'Other parameters' section for a list of commands
		data: dict
			Any additionnal data the command requires shall be added in a dictionnary. See the 'Other parameters' section for more details
		allowIDInvalidation: bool, optional
			If True, any communication error will automatically add the positioner to the invalid IDs list
		
		Returns
		-------
		Oultput: list
			A list of responses. Each positioner's response is put in a list and then appended to the 'Output' list.

		Other parameters
		----------------
		'init'
			Initializes the CAN-USB transeiver. \n
			No data required. \n
			No output.
		'get_serial_number'
			Returns the serial number of the current CAN-USB transciever. \n
			No data required. \n
			Returns a string representing the serial number.
		'get_firmware_version'
			Returns the current version of the firmware.\n
			No data required.\n
			Returns a string containing the current firmware version.
		'ask_id'
			Returns the ID number of the positioner. Broadcastable. \n
			No data required. \n
			Response is an int representing the ID.
		'is_any_moving'
			Returns True if any positioner is moving, False otherwise. ID is not used. \n
			No data required. 
		'init_datum'
			Asks the positioner to start a datum initialization. \n
			No data required. \n
			No output.
		'init_datum_alpha'
			Asks the positioner to start a datum initialization on the alpha motor only. \n
			No data required. \n
			No output.
		'init_datum_beta'
			Asks the positioner to start a datum initialization on the beta motor only. \n
			No data required. \n
			No output.
		'start_trajectory'
			Asks the positioner to start its trajectory. \n
			No data required.\n
			No output.
		'stop_trajectory'
			Asks the positioner to stop its trajectory. \n
			No data required. \n
			No output.
		'status_request'
			Returns the status of the positioner. Broadcastable. \n
			No data required. \n
			Response is a list containing one int64 representing the status.
		'clearbuffer'
			Clears the CAN-USB buffer. No data required. No output.
		'readbuffer'
			Returns the current content of the CAN-USB buffer. \n
			No data required.
		'readdata'
			Same as 'readbuffer'
		'set_speed'
			Sets the motor speeds of the positioner. \n
			Data must contain the alpha speed ('speedAlpha': float) and the beta speed ('speedBeta': float), in motor side RPM. \n
			No output.
		'set_position'
			Sets the current position of the positioner. \n
			Data must contain the alpha position ('currentAlphaPos': int) and the beta position ('currentBetaPos': int), in motor steps. \n
			No output.
		'set_actual_position'
			Same as 'set_position'
		'goto_position_absolute'
			Starts an absolute move on the positioner. \n
			Data must contain the alpha target position ('R1Steps': int) and the beta target position ('R2Steps': int), in motor steps. \n
			Response is a list of the time each motor will take ([alphaMotorTime (float), betaMotorTime (float)]) in seconds.
		'goto_position_relative'
			Starts a relative move on the positioner. \n
			Data must contain the alpha steps ('R1Steps': int) and the beta steps ('R2Steps': int), in motor steps. \n
			Response is a list of the time each motor will take ([alphaMotorTime (float), betaMotorTime (float)]) in seconds.
		'get_position'
			Returns the current position of the positioner.\n
			No data required.\n
			Response is a list of motor position ([alphaMotor (int), betaMotor (int)]) in motor steps.
		'get_actual_position'
			Same as 'get_position'
		'get_pos'
			Same as 'get_position'
		'get_pos_hall'
			Returns the current position of the positioner as estimated by the hall sensors.\n
			No data required.\n
			Response is a list of motor position ([alphaMotor (int), betaMotor (int)]) in motor steps.
		'set_openloop_current'
			Sets the motor open loop current of the positioner. \n
			Data must contain the alpha current ('currentAlpha': int) and the beta current ('currentBeta': int), in percent. \n
			No output.
		'start_motor_calibration'
			Asks the positioner to start a new motor calibration.\n 
			No data required.\n
			No output.
		'get_motor_calibration_error'
			Returns the motor calibration error of each motor.\n
			No data required.\n
			Response is a list of motor calibration errors ([alphaMotor (int), betaMotor (int)]) in degrees.
		'start_datum_calibration'
			Asks the positioner to start a new datum calibration. \n
			No data required.\n
			No output.
		'start_cogging_calibration'
			Asks the positioner to start a new cogging torque calibration. \n
			No data required.\n
			No output.
		'get_offset'
			Returns the offset (datum to 0) of each motor.\n
			No data required.\n
			Response is a list of offsets ([alphaOffset (int), betaOffset (int)]) in motor steps.
		'set_offset'
			Sets the offset (datum to 0) of each motor.\n
			Data must contain the alpha offset ('alphaOffset': int) and the beta offset ('betaOffset': int), in motor steps. \n
			No output.
		'set_approach'
			Sets the approach distance of each motor.\n
			Data must contain the alpha approach distance ('approachAlpha': int) and the beta approach distance ('approachBeta': int), in motor steps. \n
			No output.
		'request_nb_cogging_pts'
			Returns the number of points done in the cogging calibration\n
			No data required.\n
			Response is a list containing a single int32 reprensenting the number of points
		'request_cogging_curve_pos'
			Returns the positive cogging curve point that was requested.\n
			Data must contain the desired alpha index ('alphaIndex': int) and the desired beta index ('betaIndex': int). \n
			Response is a list containing the cogging value in the form [alphaCurrent (int), betaCurrent (int)], in current percentage.
		'request_cogging_curve_neg'
			Returns the negative cogging curve point that was requested.\n
			Data must contain the desired alpha index ('alphaIndex': int) and the desired beta index ('betaIndex': int). \n
			Response is a list containing the cogging value in the form [alphaCurrent (int), betaCurrent (int)], in current percentage.
		'request_cogging_curve_hold'
			Returns the holding cogging curve point that was requested.\n
			Data must contain the desired alpha index ('alphaIndex': int) and the desired beta index ('betaIndex': int).\n 
			Response is a list containing the cogging value in the form [alphaCurrent (int), betaCurrent (int)], in current percentage.
		'request_cogging_position'
			Returns the motor position of the cogging point that was requested.\n
			Data must contain the desired alpha index ('alphaIndex': int) and the desired beta index ('betaIndex': int). \n
			Response is a list containing the motor angles in the form [alphaAngle (int), betaAngle (int)], in degrees.
		'get_current_consumption'
			Returns the alpha motor position and the current it draws\n
			No data required.\n
			Response is a list containing the motor angle in steps and the current in percent, in the form [motorAngle (int), currentValue (int)].
		'get_current_and_pos_alpha'
			Returns the alpha and beta motor current consumption\n
			No data required.\n
			Response is a list containing the motor current consumption in the form [alphaConsumption (int), betaConsumption (int)].
		'get_current_and_pos_beta'
			Returns the beta motor position and the current it draws\n
			No data required.\n
			Response is a list containing the motor angle in steps and the current in mA, in the form [motorAngle (int), currentValue (int)].
		'get_bootloader_parameter'
			Returns the requested bootloader parameter (Bootloader mode only)\n
			Data must contain the required parameter ID (see BootloaderParameters) ('bootloaderParameter': int)\n
			Response is the parameter value (int)
		'set_bootloader_parameter'
			Changes the requested bootloader parameter (Bootloader mode only)\n
			Data must contain the required parameter ID (see BootloaderParameters) ('bootloaderParameter': int) and the new value ('bootloaderParameterValue': int)\n
			No output.
		'get_root_access'
			Requests bootloader root access (Bootloader mode only)\n
			No data required.\n
			No output.
		'reboot'
			Requests a positioner reboot\n
			No data required.\n
			No output.
		'boot'
			Requests a positioner to exit the bootloader (Bootloader mode only)\n
			No data required.\n
			No output.
		'start_firmware_upgrade'
			Starts a new firmware upgrade (Bootloader mode only)\n
			Data must contain the new firmware length in Bytes ('firmwareLength': int) and the checksum ('firmwareChecksum': int). Checksum is comupted using zlib.crc32.\n
			No output.
		'send_firmware_upgrade_frame'
			Sends a firmware frame (Bootloader mode only)\n
			Data must contain the new firmware frame ('firmwareData': hex), with a length of 8 Bytes and in hexadecimal representation. The last frame shall be any required length smaller or equal to 8 Bytes. \n
			No output.
		'abort_firmware_upgrade'
			Aborts the firmware upgrade (Bootloader mode only)\n
			No data required.\n
			No output.
		'get_bootloader_status'
			Returns the bootloader status of the positioner (Bootloader mode only). Broadcastable. \n
			No data required. \n
			Response is a list containing one int32 representing the status.
		'enable_collision_detection'
			Enables the collision detection.\n
			No data required.\n
			No output.
		'disable_collision_detection'
			Disables the collision detection.\n
			No data required.\n
			No output.
		'enable_closed_loop'
			Enables the closed loop control mode.\n
			No data required.\n
			No output.
		'disable_closed_loop'
			Disables the closed loop control mode.\n
			No data required.\n
			No output.
		'enable_approach_alpha'
			Enables the approach move on the alpha motor.\n
			No data required.\n
			No output.
		'disable_approach_alpha'
			Disables the approach move on the alpha motor.\n
			No data required.\n
			No output.
		'enable_approach_beta'
			Enables the approach move on the beta motor.\n
			No data required.\n
			No output.
		'disable_approach_beta'
			Disables the approach move on the beta motor.\n
			No data required.\n
			No output.
		'enable_power_after_move'
			Keeps the motor power after the move.\n
			No data required.\n
			No output.
		'disable_power_after_move'
			Shuts down the motor power after the move.\n
			No data required.\n
			No output.
		'enable_low_power_after_move'
			Enters low power mode for the motors after the move.\n
			No data required.\n
			No output.
		'disable_low_power_after_move'
			Exits low power mode for the motors after the move.\n
			No data required.\n
			No output.

		Raises
		------
		errors.CANError: Only if RAISE_ERROR_ON_COMMUNICATION_FAILURE is True
			If the CAN communication failed
		errors.OutOfRangeError
			If a parameter is out of range

		"""

		Output	= []

		if ID in self.invalidIDs:
			return

		try:
			if self.serHandle is not None:		
				#command is not case sensitive
				command	= command.lower()
				#Convert ID to usable adress
				positionerID	= ID
				ID	= ID<<self._OPT.COM.CAN_ID_BIT_SHIFT

				if command == 'init':#-------------------------------------------------------
					self.serHandle.reset_input_buffer()

					#Close the CAN channel
					self.serHandle.write('C\r'.encode())#C\r
					time.sleep(DEFINES.CAN_DELAY_BETWEEN_CONFIG_COMMANDS)
					self.serHandle.reset_input_buffer()
					#Set the Baud rate to 1Mb/s
					self.serHandle.write('S8\r'.encode())#S8\r

					time.sleep(DEFINES.CAN_DELAY_BETWEEN_CONFIG_COMMANDS)

					input_buffer	= self.serHandle.readline(self.serHandle.inWaiting())
					if input_buffer.decode() != '\r':
						raise errors.CANError('CAN could not configure the baud rate') from None
					else:
						#Reopen CAN channel
						self.serHandle.reset_input_buffer()
						self.serHandle.write('O\r'.encode())#O\r
						time.sleep(DEFINES.CAN_DELAY_BETWEEN_CONFIG_COMMANDS)
						#Check for correct communication
						input_buffer	= self.serHandle.readline(self.serHandle.inWaiting())
						if input_buffer.decode() != '\r':
							raise errors.CANError('CAN channel could not be reopened') from None
				
				elif command == 'get_serial_number':#----------------------------------------
					self.serHandle.reset_input_buffer()
					#Retrieve the serial number
					self.serHandle.write('N\r'.encode())#C\r

					watchdog	= time.perf_counter()
					while self.serHandle.inWaiting()<6 and time.perf_counter()-DEFINES.CAN_DELAY_BETWEEN_CONFIG_COMMANDS < watchdog:
						_=1

					input_buffer = self.serHandle.readline(self.serHandle.inWaiting())
					
					if not len(input_buffer.decode())	== 6:
						raise errors.CANError("CAN could not retrieve the transceiver's serial number") from None
					else:
						Output.append(str(input_buffer[1:5].decode()))

				elif command == 'get_firmware_version':	#---------------------------------------------------
					self.send_CAN(positionerID, command = self._OPT.RX.GET_FIRMWARE_VERSION)
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, dataLength = 4, nbData = 1, nbResponses = 1, allowIDInvalidation = False)

					for response in Output:
						if response[0] is not None:
							response[0] = f'{(response[0]>>16)&0x000000FF}.{(response[0]>>8)&0x000000FF}.{(response[0])&0x000000FF}'

				elif command == 'ask_id':
					self.send_CAN(positionerID, command = self._OPT.RX.GET_ID)
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, dataLength = 4, nbData = 1, nbResponses = DEFINES.CAN_COM_WAIT_FOR_TIMEOUT, timeoutDelay = DEFINES.CAN_DELAY_FOR_ASKID, allowIDInvalidation = False)

				elif command == 'is_any_moving':#----------
					allStatus = []

					self.send_CAN(0, command = self._OPT.RX.GET_STATUS)
					self.receive_CAN(0, commandName = command, dataContainer = allStatus, dataLength = 8, nbData = 1, nbResponses = int(data['nbPositioners']), allowIDInvalidation = allowIDInvalidation)

					isMoving = False
					for status in allStatus:
						if status[0] is not None:
							isMoving = isMoving or (not bool(status[0]&(self._OPT.STREG.DISPLACEMENT_COMPLETED)))

					Output.append(isMoving)

				elif command == 'init_datum':
					self.send_CAN(positionerID, command = self._OPT.RX.INIT_DATUM)
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'init_datum_alpha':
					self.send_CAN(positionerID, command = self._OPT.RX.INIT_DATUM_ALPHA)
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'init_datum_beta':
					self.send_CAN(positionerID, command = self._OPT.RX.INIT_DATUM_BETA)
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)
				
				elif command == 'start_trajectory':#-----------------------------------------
					self.send_CAN(positionerID, command = self._OPT.RX.START_TRAJECTORY)
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'stop_trajectory':#------------------------------------------
					self.send_CAN(positionerID, command = self._OPT.RX.STOP_TRAJECTORY)
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)
				
				elif command == 'status_request':#----------
					self.send_CAN(positionerID, command = self._OPT.RX.GET_STATUS)
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, dataLength = 8, nbData = 1, allowIDInvalidation = allowIDInvalidation)

				elif command == 'clearbuffer':#---------------------------------------------
					self.serHandle.reset_input_buffer()
					self.serHandle.reset_output_buffer()
				
				elif command == 'readbuffer' or command == 'readdata':#---------------------
					input_buffer=self.serHandle.read(self.serHandle.inWaiting())
					Output.append(input_buffer)
				
				elif command == 'set_speed':#--------------------------------------
					self.send_CAN(positionerID, command = self._OPT.RX.SET_SPEED, data1 = data['speedAlpha'], data2 = data['speedBeta'])
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'set_position' or command == 'set_actual_position':#--------------------------------------
					self.send_CAN(positionerID, command = self._OPT.RX.SET_ACTUAL_POSITION, data1 = data['currentAlphaPos'], data2 = data['currentBetaPos'])
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'goto_position_absolute':#--------------------------------------
					self.send_CAN(positionerID, command = self._OPT.RX.GOTO_POSITION_ABSOLUTE, data1 = data['R1Steps'], data2 = data['R2Steps'])
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, allowIDInvalidation = allowIDInvalidation)

					for response in Output:
						if response[0] is not None:
							response[0] = response[0]/DEFINES.CANCOM_FIRMWARE_CONTROL_LOOP_FREQUENCY
							response[1] = response[1]/DEFINES.CANCOM_FIRMWARE_CONTROL_LOOP_FREQUENCY

				elif command == 'goto_position_relative':#--------------------------------------
					self.send_CAN(positionerID, command = self._OPT.RX.GOTO_POSITION_RELATIVE, data1 = data['R1Steps'], data2 = data['R2Steps'])
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, allowIDInvalidation = allowIDInvalidation)

					for response in Output:
						if response[0] is not None:
							response[0] = response[0]/DEFINES.CANCOM_FIRMWARE_CONTROL_LOOP_FREQUENCY
							response[1] = response[1]/DEFINES.CANCOM_FIRMWARE_CONTROL_LOOP_FREQUENCY

				elif command == 'get_position' or command == 'get_actual_position' or command == 'get_pos':#--------------------------------------
					self.send_CAN(positionerID, command = self._OPT.RX.GET_ACTUAL_POSITION)
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, allowIDInvalidation = allowIDInvalidation)

					for response in Output:
						if response[0] is not None:
							if response[0] > 2**31:
								response[0] -= 2**32
							if response[1] > 2**31:
								response[1] -= 2**32

				elif command == 'get_pos_hall':#--------------------------------------
					self.send_CAN(positionerID, command = self._OPT.RX.GET_MOTOR_HALL_POS)
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, allowIDInvalidation = allowIDInvalidation)

											
					for response in Output:
						if response[0] is not None:
							if response[0] > 2**31:
								response[0] -= 2**32
							if response[1] > 2**31:
								response[1] -= 2**32

				elif command == 'set_openloop_current':#--------------------------------------
					self.send_CAN(positionerID, command = self._OPT.RX.SET_CURRENT, data1 = data['currentAlpha'], data2 = data['currentBeta'])
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)
					
				elif command == 'start_motor_calibration':
					self.send_CAN(positionerID, command = self._OPT.RX.START_MOTOR_CALIBRATION)
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'get_motor_calibration_error':
					self.send_CAN(positionerID, command = self._OPT.RX.GET_MOTOR_CALIBRATION_ERROR)
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, allowIDInvalidation = allowIDInvalidation)

					for response in Output:
						if response[0] is not None:
							if response[0] > 2**31:
								response[0] -= 2**32
							if response[1] > 2**31:
								response[1] -= 2**32

				elif command == 'start_datum_calibration':
					self.send_CAN(positionerID, command = self._OPT.RX.START_DATUM_CALIBRATION)
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command 	== 'get_datum_calibration_offset':
					self.send_CAN(positionerID, command = self._OPT.RX.GET_DATUM_CALIB_OFFSET)
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, allowIDInvalidation = allowIDInvalidation)

					for response in Output:
						if response[0] is not None:
							if response[0] > 2**31:
								response[0] -= 2**32
							if response[1] > 2**31:
								response[1] -= 2**32

				elif command == 'start_cogging_calibration':
					self.send_CAN(positionerID, command = self._OPT.RX.START_COGGING_CALIBRATION)
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)
	
				elif command == 'get_offset':
					self.send_CAN(positionerID, command = self._OPT.RX.GET_OFFSET)
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, allowIDInvalidation = allowIDInvalidation)

					for response in Output:
						if response[0] is not None:
							if response[0] > 2**31:
								response[0] -= 2**32
							if response[1] > 2**31:
								response[1] -= 2**32

				elif command == 'set_offset':
					self.send_CAN(positionerID, command = self._OPT.RX.SET_OFFSET, data1 = data['alphaOffset'], data2 = data['betaOffset'])
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)
					
				elif command == 'set_approach':#--------------------------------------
					self.send_CAN(positionerID, command = self._OPT.RX.SET_APPROACH_DISTANCE, data1 = data['approachAlpha'], data2 = data['approachBeta'])
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command 	== 'save_internal_calib':
					self.send_CAN(positionerID, command = self._OPT.RX.SAVE_INTERNAL_CALIBRATION)
					self.receive_CAN(positionerID, commandName = command, timeoutDelay = DEFINES.CAN_COM_SAVE_INTERNAL_CALIB_WATCHDOG_TIMER, allowIDInvalidation = allowIDInvalidation)

				elif command 	== 'offset_max_closed_loop_current':
					self.send_CAN(positionerID, command = self._OPT.RX.CHANGE_COLLISION_MARGIN, data1 = data['currentIncrementAlpha'], data2 = data['currentIncrementBeta'])
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command 	== 'set_holding_current':
					self.send_CAN(positionerID, command = self._OPT.RX.CHANGE_HOLDING_CURRENT, data1 = data['holdingCurrentAlpha'], data2 = data['holdingCurrentBeta'])
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)
				
				elif 	command == 'request_nb_cogging_pts':
					self.send_CAN(positionerID, command = self._OPT.RX.REQUEST_NB_COGGING_PTS)
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, dataLength = 4, nbData = 1, allowIDInvalidation = allowIDInvalidation)

				elif 	command == 'request_cogging_curve_pos':
					self.send_CAN(positionerID, command = self._OPT.RX.REQUEST_COGGING_CURVE_POS, data1 = data['alphaIndex'], data2 = data['betaIndex'])
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, allowIDInvalidation = allowIDInvalidation)

					for response in Output:
						if response[0] is not None:
							if response[0] > 2**31:
								response[0] -= 2**32
							if response[1] > 2**31:
								response[1] -= 2**32

				elif 	command == 'request_cogging_curve_neg':
					self.send_CAN(positionerID, command = self._OPT.RX.REQUEST_COGGING_CURVE_NEG, data1 = data['alphaIndex'], data2 = data['betaIndex'])
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, allowIDInvalidation = allowIDInvalidation)

					for response in Output:
						if response[0] is not None:
							if response[0] > 2**31:
								response[0] -= 2**32
							if response[1] > 2**31:
								response[1] -= 2**32

				elif 	command == 'request_cogging_curve_hold':
					self.send_CAN(positionerID, command = self._OPT.RX.REQUEST_COGGING_CURVE_HOLD, data1 = data['alphaIndex'], data2 = data['betaIndex'])
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, allowIDInvalidation = allowIDInvalidation)

					for response in Output:
						if response[0] is not None:
							if response[0] > 2**31:
								response[0] -= 2**32
							if response[1] > 2**31:
								response[1] -= 2**32

				elif 	command == 'request_cogging_position':
					self.send_CAN(positionerID, command = self._OPT.RX.REQUEST_COGGING_POSITION, data1 = data['alphaIndex'], data2 = data['betaIndex'])
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, allowIDInvalidation = allowIDInvalidation)

					for response in Output:
						if response[0] is not None:
							if response[0] > 2**31:
								response[0] -= 2**32
							if response[1] > 2**31:
								response[1] -= 2**32

				elif	command == 'get_current_consumption':
					self.send_CAN(positionerID, command = self._OPT.RX.GET_CURRENT)
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, allowIDInvalidation = allowIDInvalidation)

					for response in Output:
						if response[0] is not None:
							if response[0] > 2**31:
								response[0] -= 2**32
							if response[1] > 2**31:
								response[1] -= 2**32
					
				elif	command == 'get_current_and_pos_alpha':
					self.send_CAN(positionerID, command = self._OPT.RX.GET_CURRENT_AND_POS_ALPHA)
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, allowIDInvalidation = allowIDInvalidation)

					for response in Output:
						if response[0] is not None:
							if response[0] > 2**31:
								response[0] -= 2**32
							if response[1] > 2**31:
								response[1] -= 2**32

				elif	command == 'get_current_and_pos_beta':
					self.send_CAN(positionerID, command = self._OPT.RX.GET_CURRENT_AND_POS_BETA)
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, allowIDInvalidation = allowIDInvalidation)

					for response in Output:
						if response[0] is not None:
							if response[0] > 2**31:
								response[0] -= 2**32
							if response[1] > 2**31:
								response[1] -= 2**32

				elif command 	== 'get_bootloader_parameter':
					self.send_CAN(positionerID, command = self._OPT.RX.GET_FACTORY_SETTING, data1 = data['bootloaderParameter'])
					self.receive_CAN(positionerID, commandName = command, dataContainer = Output, nbResponses = 1, dataLength = 4, nbData = 1, allowIDInvalidation = allowIDInvalidation)

					for response in Output:
						if response[0] is not None:
							if response[0] > 2**31:
								response[0] -= 2**32

				elif command 	== 'set_bootloader_parameter':
					self.send_CAN(positionerID, command = self._OPT.RX.SET_FACTORY_SETTING, data1 = data['bootloaderParameter'], data2 = data['bootloaderParameterValue'])
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command 	== 'get_root_access':
					self.send_CAN(positionerID, command = self._OPT.RX.GET_ROOT_ACCESS)
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command 	== 'reboot':
					self.send_CAN(positionerID, command = self._OPT.RX.REQUEST_REBOOT)
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command 	== 'boot':
					self.send_CAN(positionerID, command = self._OPT.RX.REQUEST_BOOT)
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'start_firmware_upgrade':
					self.send_CAN(positionerID, command = self._OPT.RX.SEND_NEW_FIRMWARE, data1 = data['firmwareLength'], data2 = data['firmwareChecksum'])
					self.receive_CAN(positionerID, commandName = command, timeoutDelay = DEFINES.CAN_COM_FIRMWARE_UPGRADE_TIMEOUT, allowIDInvalidation = allowIDInvalidation)

				elif command == 'send_firmware_upgrade_frame':
					self.send_CAN(positionerID, command = self._OPT.RX.FIRMWARE_DATA, manualHexFrame = data['firmwareData'])
					self.receive_CAN(positionerID, commandName = command, timeoutDelay = DEFINES.CAN_COM_FIRMWARE_UPGRADE_TIMEOUT, allowIDInvalidation = allowIDInvalidation)

				elif command == 'abort_firmware_upgrade':
					self.send_CAN(positionerID, command = self._OPT.RX.FIRMWARE_ABORT)
					self.receive_CAN(positionerID, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'get_bootloader_status':
					self.send_CAN(positionerID, command = self._OPT.RX.GET_STATUS)
					self.receive_CAN(positionerID, commandName = command, nbData = 1, dataLength = 4, dataContainer = Output, allowIDInvalidation = allowIDInvalidation)

				elif command 	== 'reset_collision_flags':  
					self.send_full_status(positionerID, regClear = (self._OPT.STREG.COLLISION_ALPHA|self._OPT.STREG.COLLISION_BETA), commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'enable_collision_detection':
					self.send_full_status(positionerID, regClear = (self._OPT.STREG.COLLISION_DETECT_ALPHA_DISABLE|self._OPT.STREG.COLLISION_DETECT_BETA_DISABLE), commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'disable_collision_detection':
					self.send_full_status(positionerID, regSet = (self._OPT.STREG.COLLISION_DETECT_ALPHA_DISABLE|self._OPT.STREG.COLLISION_DETECT_BETA_DISABLE), commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'enable_closed_loop':
					self.send_full_status(positionerID, regSet = (self._OPT.STREG.CLOSED_LOOP_ALPHA|self._OPT.STREG.CLOSED_LOOP_BETA), commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'disable_closed_loop':
					self.send_full_status(positionerID, regClear = (self._OPT.STREG.CLOSED_LOOP_ALPHA|self._OPT.STREG.CLOSED_LOOP_BETA), commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'enable_approach_alpha':
					self.send_full_status(positionerID, regSet = self._OPT.STREG.PRECISE_POSITIONING_ALPHA, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'disable_approach_alpha':
					self.send_full_status(positionerID, regClear = self._OPT.STREG.PRECISE_POSITIONING_ALPHA, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'enable_approach_beta':
					self.send_full_status(positionerID, regSet = self._OPT.STREG.PRECISE_POSITIONING_BETA, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'disable_approach_beta':
					self.send_full_status(positionerID, regClear = self._OPT.STREG.PRECISE_POSITIONING_BETA, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'enable_power_after_move':
					self.send_full_status(positionerID, regClear = self._OPT.STREG.SWITCH_OFF_AFTER_MOVE, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'disable_power_after_move':
					self.send_full_status(positionerID, regSet = self._OPT.STREG.SWITCH_OFF_AFTER_MOVE, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'enable_low_power_after_move':
					self.send_full_status(positionerID, regSet = self._OPT.STREG.LOW_POWER_AFTER_MOVE, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command == 'disable_low_power_after_move':
					self.send_full_status(positionerID, regClear = self._OPT.STREG.LOW_POWER_AFTER_MOVE, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command 	== 'enable_closed_loop_for_approach':
					self.send_full_status(positionerID, regClear = (self._OPT.STREG.PRECISE_MOVE_IN_OPEN_LOOP_ALPHA|self._OPT.STREG.PRECISE_MOVE_IN_OPEN_LOOP_BETA), commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command 	== 'disable_closed_loop_for_approach':
					self.send_full_status(positionerID, regSet = (self._OPT.STREG.PRECISE_MOVE_IN_OPEN_LOOP_ALPHA|self._OPT.STREG.PRECISE_MOVE_IN_OPEN_LOOP_BETA), commandName = command, allowIDInvalidation = allowIDInvalidation)
				
				elif command 	== 'enable_hall':
					self.send_full_status(positionerID, regClear = (self._OPT.STREG.HALL_ALPHA_DISABLE|self._OPT.STREG.HALL_BETA_DISABLE), commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command 	== 'disable_hall':
					self.send_full_status(positionerID, regSet = (self._OPT.STREG.HALL_ALPHA_DISABLE|self._OPT.STREG.HALL_BETA_DISABLE), commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command 	== 'enable_hall_power_after_move':
					self.send_full_status(positionerID, regClear = self._OPT.STREG.SWITCH_OFF_HALL_AFTER_MOVE, commandName = command, allowIDInvalidation = allowIDInvalidation)

				elif command 	== 'disable_hall_power_after_move':
					self.send_full_status(positionerID, regSet = self._OPT.STREG.SWITCH_OFF_HALL_AFTER_MOVE, commandName = command, allowIDInvalidation = allowIDInvalidation)

				else:
					raise errors.CANError('CAN unknown command') from None
			else:
				raise errors.CANError('CAN transciever is disconnected') from None

		except serial.SerialException:
			self.close()
			raise errors.CANError('CAN transciever is disconnected') from None
		except (errors.CANError, errors.OutOfRangeError) as e:
			raise e from None

		return Output

	def send_full_status(self, positionerID, regSet = 0x0000000000000000, regClear = 0x0000000000000000, commandName = '', allowIDInvalidation = True):
		"""
		Sends a full 64bit status register to the positioner.

		It will cut the register in 2 32bits parts and send the register in 2 parts, the low part and the high part, using classCanCom.send_half_status

		Parameters
		----------
		positionerID: uint
			The positioner to send the command to
		regSet: uint64
			The bits of the register that shall be set
		regClear: uint64
			The bits of the register that shall be cleared
		commandName: string
			The name of the command that wants to change the register
		allowIDInvalidation: bool
			If true, any communication error will automatically add the positioner to the invalid IDs list

		Raises
		------
		errors.CANError
			If the register parameter is larger than 64bits

		"""

		regSetLow 		= regSet&0x00000000FFFFFFFF
		regSetHigh 		= regSet>>32
		regClearLow 	= regClear&0x00000000FFFFFFFF
		regClearHigh 	= regClear>>32

		if regSet > 0xFFFFFFFFFFFFFFFF or regClear > 0xFFFFFFFFFFFFFFFF:
			raise errors.CANError('CAN StatusRegister command out of range')

		if regSetLow or regClearLow:
			self.send_half_status(positionerID, self._OPT.RX.SET_STATUS_LOW, regSetLow, regClearLow, commandName, allowIDInvalidation = allowIDInvalidation)

		if regSetHigh or regClearHigh:
			self.send_half_status(positionerID, self._OPT.RX.SET_STATUS_HIGH, regSetHigh, regClearHigh, commandName, allowIDInvalidation = allowIDInvalidation)

	def send_half_status(self, positionerID, command = None, regSet = 0x00000000, regClear = 0x00000000, commandName = '', allowIDInvalidation = True):
		"""
		Sends a 32 bit register part to the positioner

		Parameters
		----------
		positionerID: uint
			The positioner to send the command to
		command: uint
			The communication command ID (classCanCom.RX_Options.SET_STATUS_LOW or classCanCom.RX_Options.SET_STATUS_HIGH)
		regSet: uint32, optional
			The bits of the register that shall be set
		regClear: uint32, optional
			The bits of the register that shall be cleared
		commandName: string, optional
			The name of the command that wants to change the register
		allowIDInvalidation: bool, optional
			If True, any communication error will automatically add the positioner to the invalid IDs list

		"""

		if (regSet or regClear) and command is not None:
			self.send_CAN(positionerID, command = command, data1 = regSet, data2 = regClear)
			self.receive_CAN(positionerID, commandName = commandName, allowIDInvalidation = allowIDInvalidation)#, dataContainer = [], nbData = 1)
		else:
			return

	def send_CAN(self, positionerID, command = None, data1 = None, data2 = None, manualHexFrame = None):
		"""
		Sends a CAN communication to the positioner(s)

		Parameters
		----------
		positionerID: uint
			The positioner to send the command to
		command: uint
			The communication command ID (among classCanCom.RX_Options)
		data1: int32, optional
			If data is sent, the first variable value. Leave blank or None is no data is needed.
		data2: int32, optional
			If data is sent, the second variable value. Leave blank or None is no data is needed.
		manualHexFrame: int8, int16, int24, int32, int40, int48, int56, int64, optional
			Manual data that shall be sent to the positioner. Leave blank or None if no manual data is needed.
		
		Raises
		------
		errors.CANError
			If the manualHexFrame is too long

		"""

		if command is None :
			return

		self.serHandle.reset_input_buffer()

		ID	= positionerID<<self._OPT.COM.CAN_ID_BIT_SHIFT
		txCmd = (command<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
			
		txCmd	= '%0.8X' % txCmd

		if manualHexFrame is not None:
			dataLength = len(manualHexFrame)/2
			if dataLength > 8 or int(dataLength) != dataLength:
				raise errors.CANError('Invalid frame length')
			
			if dataLength == 0:
				manualHexFrame = ''
			elif dataLength == 1:
				manualHexFrame = '%0.2X' % (int(manualHexFrame,16))
			elif dataLength == 2:
				manualHexFrame = '%0.4X' % (int(manualHexFrame,16))
			elif dataLength == 3:
				manualHexFrame = '%0.6X' % (int(manualHexFrame,16))
			elif dataLength == 4:
				manualHexFrame = '%0.8X' % (int(manualHexFrame,16))
			elif dataLength == 5:
				manualHexFrame = '%0.10X' % (int(manualHexFrame,16))
			elif dataLength == 6:
				manualHexFrame = '%0.12X' % (int(manualHexFrame,16))
			elif dataLength == 7:
				manualHexFrame = '%0.14X' % (int(manualHexFrame,16))
			elif dataLength == 8:
				manualHexFrame = '%0.16X' % (int(manualHexFrame,16))

			dataLength = str(int(dataLength))

			self.serHandle.write(('T'+txCmd+dataLength+manualHexFrame+'\r').encode())

		elif data1 is None and data2 is None:
			self.serHandle.write(('T'+txCmd+'0'+'\r').encode())

		elif data2 is None:
			dataCmd	= '%0.8X' % (swapInt32(data1%(2**32)))

			#send command
			self.serHandle.write(('T'+txCmd+'4'+dataCmd+'\r').encode())#t(ID)4(data)\r

		elif data1 is None:
			dataCmd	= '%0.8X' % (swapInt32(data2%(2**32)))

			#send command
			self.serHandle.write(('T'+txCmd+'4'+dataCmd+'\r').encode())#t(ID)4(data)\r

		else:
			data1Cmd	= '%0.8X' % (swapInt32(data1%(2**32)))
			data2Cmd	= '%0.8X' % (swapInt32(data2%(2**32)))

			#send command
			self.serHandle.write(('T'+txCmd+'8'+data1Cmd+data2Cmd+'\r').encode())#t(ID)4(data)\r

	def receive_CAN(self, positionerID, commandName = '', dataContainer = None, nbResponses = 1, dataLength = 4, nbData = 2, timeoutDelay = DEFINES.CAN_COM_WATCHDOG_TIMER, allowIDInvalidation = True):
		"""
		Recieves a CAN communication from the positioner(s)

		Parameters
		----------
		positionerID: uint
			The positioner that the command was sent to
		commandName: string
			The name of the command that wants to receive data
		dataContainer: list, optional
			The response data will be added to the dataContainer list. Leave blanck if no data is expected.
		nbResponses: uint
			The number of expected messages
		dataLength: uint
			The expected length of one data chunk, in Bytes
		nbData: uint
			The number of expected data chunks 
		timeoutDelay: ufloat, optional
			The communication timeout delay
		allowIDInvalidation: bool, optional
			If True, any communication error will automatically add the positioner to the invalid IDs list
		
		Raises
		------
		errors.CANError: 
			If an invalid data length was asked
		errors.CANError: Only if RAISE_ERROR_ON_COMMUNICATION_FAILURE is True
			If no response was received
			If the response code corresponds to an error

		"""

		responseOffset = 2
		responseLength = 11

		if dataLength == 1:
			swap = lambda n : swapInt8(n)
		elif dataLength == 2:
			swap = lambda n : swapInt16(n)
		elif dataLength == 3:
			swap = lambda n : swapInt24(n)
		elif dataLength == 4:
			swap = lambda n : swapInt32(n)
		elif dataLength == 5:
			swap = lambda n : swapInt40(n)
		elif dataLength == 6:
			swap = lambda n : swapInt48(n)
		elif dataLength == 7:
			swap = lambda n : swapInt56(n)
		elif dataLength == 8:
			swap = lambda n : swapInt64(n)
		else:
			errors.CANError("Invalid data length provided to receive_CAN")

		if nbResponses == DEFINES.CAN_COM_WAIT_FOR_TIMEOUT:
			watchdog	= time.perf_counter()
			while time.perf_counter()- timeoutDelay< watchdog:
				_=1
		else:
			if type(dataContainer) == list:
				responseCharacters = nbResponses*(responseLength+2*dataLength*nbData)+responseOffset
			else:
				responseCharacters = responseLength + responseOffset

			watchdog = time.perf_counter()
			stayInLoop = True
			nbChar = 0
			previousNbChar = 0

			while (nbChar<responseCharacters or stayInLoop) and time.perf_counter()- timeoutDelay< watchdog:
				nbChar = self.serHandle.inWaiting()
				if nbChar >= responseCharacters and previousNbChar == nbChar:
					stayInLoop = False
				previousNbChar = nbChar

		input_buffer=self.serHandle.read(self.serHandle.inWaiting()) #get whole input buffer
		inputMessages = input_buffer.decode().split('\r')[1:-1] #get all the messages received

		responseCodes = self.get_errcode(inputMessages)	#Check errors

		if len(responseCodes) <= 0:
			if allowIDInvalidation:
				self.add_invalid_ID(positionerID, 'NO_RESPONSE')
			if DEFINES.RAISE_ERROR_ON_COMMUNICATION_FAILURE:
				raise errors.CANError(f'CAN {commandName} received a wrong response (NO_RESPONSE) from positioner {positionerID:04.0f}') from None		
		
		for responseCode in responseCodes:
			if 	responseCode[0] == self._OPT.RX.get_err_description(self._OPT.RX.COMMAND_ACCEPTED) and \
				nbResponses != DEFINES.CAN_COM_WAIT_FOR_TIMEOUT and \
				responseCode[1] == positionerID:
				# if len(inputMessages) != nbResponses:
				# 	responseCode[0] = f"BAD_MESSAGE_COUNT ({len(inputMessages)} received, expected {nbResponses})"
				if len(input_buffer.decode()) < responseCharacters:
					responseCode[0] = "BAD_MESSAGE_LENGTH (WRONG_DATA)"

			if responseCode[0] != self._OPT.RX.get_err_description(self._OPT.RX.COMMAND_ACCEPTED): #If the response was wrong
				if allowIDInvalidation:
					self.add_invalid_ID(responseCode[1], responseCode[0])
				if DEFINES.RAISE_ERROR_ON_COLLISION and responseCode[0] == self._OPT.RX.get_err_description(self._OPT.RX.FATAL_ERROR_COLLISION):
					raise errors.CANError(f'CAN {commandName} received a wrong response ({responseCode[0]}) from positioner {responseCode[1]:04.0f}') from None
				elif DEFINES.RAISE_ERROR_ON_COMMUNICATION_FAILURE:
					raise errors.CANError(f'CAN {commandName} received a wrong response ({responseCode[0]}) from positioner {responseCode[1]:04.0f}') from None
				else:
					continue

			if type(dataContainer) == list: #Return data if needed
				tempOutput = []
				message = responseCode[2]
				for i in range(nbData):
					startIdx = responseLength+2*i*dataLength-1
					tempOutput.append(swap(int(message[startIdx:startIdx+2*dataLength],16)))
				dataContainer.append(tempOutput)

		if type(dataContainer) == list and dataContainer == []:
			tempOutput = []
			for i in range(nbData):
				tempOutput.append(None)
			dataContainer.append(tempOutput)

	def get_errcode(self, messages): #Check if the message doesn't report any error
		"""
		Returns the response codes' names for each message in "messages".

		Parameters
		----------
		messages: list of string
			The list of messages to compute.

		Returns
		-------
		responseCodes: list of list
			For each message, a list is appended to the output list. This list contains the following elements:\n
			(1) response code name (string): the name of the response code\n
			(2) idCode (int): the ID of the positioner that sent the message\n
			(3) message (string): a copy of the message

		"""

		idCode = -1
		responseCodes = []
		for message in messages:
			if len(message) >= 5:
				idCode = ((int(message[1:5],16))>>2)&0b011111111111 #extract the ID
			else:
				responseCodes.append(["BAD_MESSAGE_LENGTH (NO_ID)", idCode, message])
				continue
			if len(message) >= 7:
				commandCode = ((int(message[5:7],16))>>2)&0b11111111 #extract the command code
				if commandCode == self._OPT.RX.FATAL_ERROR_COLLISION:
					responseCodes.append([self._OPT.RX.get_err_description(commandCode), idCode, message])
					continue
			else:
				responseCodes.append(["BAD_MESSAGE_LENGTH (NO_COMMAND)", idCode, message])
				continue
			if len(message) >= 9:
				responseCode = int(message[8],16) # extract the response code
				if responseCode != self._OPT.RX.COMMAND_ACCEPTED:
					responseCodes.append([self._OPT.RX.get_err_description(responseCode), idCode, message])
					continue
			else:
				responseCodes.append(["BAD_MESSAGE_LENGTH (NO_RESPONSE)", idCode, message])
				continue

			responseCodes.append([self._OPT.RX.get_err_description(self._OPT.RX.COMMAND_ACCEPTED), idCode, message])
			
		return responseCodes

def swapInt8(number):
	"""
	Swaps a 8bit integer bytewise

	Parameters
	----------
	number: int8
		The number to swap

	Returns
	-------
	int: the swapped number
	
	"""

	return number

def swapInt16(number):
	"""
	Swaps a 16bit integer bytewise

	Parameters
	----------
	number: int16
		The number to swap

	Returns
	-------
	int: the swapped number
	
	"""

	return (((number << 8) & 0xFF00) | \
			((number >> 8) & 0x00FF))

def swapInt24(number):
	"""
	Swaps a 24bit integer bytewise

	Parameters
	----------
	number: int24
		The number to swap

	Returns
	-------
	int: the swapped number
	
	"""

	return (((number << 16) & 0xFF0000) | \
			((number) 		& 0x00FF00) | \
			((number >> 16) & 0x0000FF))

def swapInt32(number):
	"""
	Swaps a 32bit integer bytewise

	Parameters
	----------
	number: int32
		The number to swap

	Returns
	-------
	int: the swapped number
	
	"""

	return (((number << 24) & 0xFF000000) | \
			((number << 8) 	& 0x00FF0000) | \
			((number >> 8) 	& 0x0000FF00) | \
			((number >> 24) & 0x000000FF))

def swapInt40(number):
	"""
	Swaps a 40bit integer bytewise

	Parameters
	----------
	number: int40
		The number to swap

	Returns
	-------
	int: the swapped number
	
	"""

	return (((number << 32) & 0xFF00000000) | \
			((number << 16) & 0x00FF000000) | \
			((number) 		& 0x0000FF0000) | \
			((number >> 16) & 0x000000FF00) | \
			((number >> 32) & 0x00000000FF))

def swapInt48(number):
	"""
	Swaps a 48bit integer bytewise

	Parameters
	----------
	number: int48
		The number to swap

	Returns
	-------
	int: the swapped number
	
	"""

	return (((number << 40) & 0xFF0000000000) | \
			((number << 24) & 0x00FF00000000) | \
			((number << 8) 	& 0x0000FF000000) | \
			((number >> 8) 	& 0x000000FF0000) | \
			((number >> 24) & 0x00000000FF00) | \
			((number >> 40) & 0x0000000000FF))

def swapInt56(number):
	"""
	Swaps a 56bit integer bytewise

	Parameters
	----------
	number: int56
		The number to swap

	Returns
	-------
	int: the swapped number
	
	"""

	return (((number << 48) & 0xFF000000000000) | \
			((number << 32) & 0x00FF0000000000) | \
			((number << 16) & 0x0000FF00000000) | \
			((number) 		& 0x000000FF000000) | \
			((number >> 16) & 0x00000000FF0000) | \
			((number >> 32) & 0x0000000000FF00) | \
			((number >> 48) & 0x000000000000FF))

def swapInt64(number):
	"""
	Swaps a 64bit integer bytewise

	Parameters
	----------
	number: int64
		The number to swap

	Returns
	-------
	int: the swapped number
	
	"""

	return (((number << 56) & 0xFF00000000000000) | \
			((number << 40) & 0x00FF000000000000) | \
			((number << 24) & 0x0000FF0000000000) | \
			((number << 8) 	& 0x000000FF00000000) | \
			((number >> 8) 	& 0x00000000FF000000) | \
			((number >> 24) & 0x0000000000FF0000) | \
			((number >> 40) & 0x000000000000FF00) | \
			((number >> 56) & 0x00000000000000FF))

if __name__	== '__main__':
	pass

