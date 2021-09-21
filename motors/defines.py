# can related
CAN_ID_BIT_SHIFT = 18
CAN_CMD_BIT_SHIFT = 10  # Bits to shift to input the command
CAN_UID_BIT_SHIFT = 4
# can timing
CAN_COM_WATCHDOG_TIMER = 0.5  # [s]
CAN_DELAY_IF_NO_MESSAGE_FOUND = 0.2

# positioner steps
POS_MOTOR_STEPS = 2 ** 30
POS_TIME_STEP = 5e-4

# positioner response code
POS_RESP_COMMAND_ACCEPTED = 0  # 0    all OK
POS_RESP_VALUE_OUT_OF_RANGE = 1  # 1    received parameter is out of range
POS_RESP_INVALID_TRAJECTORY = 2  # 2    trajectory not accepted
POS_RESP_ALREADY_IN_MOTION = 3  # 3    already in motion, cannot accept command
POS_RESP_DATUM_NOT_INITIALIZED = 4  # 4    datum not initialized
POS_RESP_INCORRECT_AMOUNT_OF_DATA = 5  # 5    incorrect amount of data in packet
POS_RESP_CALIBRATION_MODE_ACTIVE = 6  # 6    one of the calibration modes is active: MOTOR_CALIBRATION,
# COGGING_CALIBRATION, DATUM_CALIBRATION, DATUM _INITIALIZATION
POS_RESP_MOTOR_NOT_CALIBRATED = 7  # 7    the motors are not calibrated and therefore the hall sensors
# can't be used
POS_RESP_COLLISION_DETECTED_ALPHA = 8  # 8    a collision is detected on alpha, the flag has to be first
# cleared with stop trajectory
POS_RESP_COLLISION_DETECTED_BETA = 9  # 9    a collision is detected on beta, the flag has to be first
# cleared with stop trajectory
POS_RESP_INVALID_BROADCAST_COMMAND = 10  # 10   broadcast command not valid
POS_RESP_INVALID_BOOTLOADER_COMMAND = 11  # 11   command not supported by bootloader
POS_RESP_INVALID_COMMAND = 12  # 12   invalid command
POS_RESP_UNKNOWN_COMMAND = 13  # 13   unknown command
POS_RESP_DATUM_NOT_CALIBRATED = 14  # 14   datum not calibrated
POS_RESP_HALL_SENSOR_DISABLED = 15  # 15   hall sensors are disabled and can therefore not be used
pos_response_code = {
    -2: 'command could not be sent',
    -1: 'no message received',
    0: 'command accepted',
    1: 'value out of range',
    2: 'invalid trajectory',
    3: 'already in motion',
    4: 'datum not initialized',
    5: 'incorrect amount of data',
    6: 'calibration mode active',
    7: 'motor not calibrated',
    8: 'collision detected alpha',
    9: 'collision detected beta',
    10: 'invalid broadcast command',
    11: 'invalid bootloader command',
    12: 'invalid command',
    13: 'unknown command',
    14: 'datum not calibrated',
    15: 'hall sensor disabled',
}

# positioner commands
POS_CMD_GET_ID = 1  # 1    ask the ID of the positioner
POS_CMD_GET_FIRMWARE = 2  # 2    request actual firmware version of positioner
POS_CMD_GET_STATUS = 3  # 3    request for status register
POS_CMD_SEND_TRAJECTORY_NEW = 10  # 10   starts a new trajectory transmission (uint32_t alpha points,
# uint32_t beta points)
POS_CMD_SEND_TRAJECTORY_DATA = 11  # 11   sends trajectory points (int32_t position, uint32_t time)
POS_CMD_SEND_TRAJECTORY_DATA_END = 12  # 12   sends end trajectory transmission to validate sent trajectories
POS_CMD_SEND_TRAJECTORY_ABORT = 13  # 13   stop the positioner, sets trajectory to 0 move, same as 16 but
# without clearing the collision flags
POS_CMD_START_TRAJECTORY = 14  # 14   starts the stored trajectory
POS_CMD_STOP_TRAJECTORY = 15  # 15   stop the positioner, sets trajectory to 0 move, clears the
# collision flag
POS_CMD_FATAL_ERROR_COLLISION = 18  # 18   only send by robot when collision occurs
POS_CMD_GET_DATUM_CALIB_OFFSET = 19  # 19
POS_CMD_GOTO_DATUMS = 20  # 20   move slowly until datums are reached and sets positions to zero
# once we reach datum
POS_CMD_GOTO_DATUM_ALPHA = 21  # 21   move alpha arm slowly in negative direction until datum and set
# alpha position to zero
POS_CMD_GOTO_DATUM_BETA = 22  # 22   move beta arm slowly in negative direction until datum and set
# beta position to zero
POS_CMD_CALIB_DATUMS = 23  # 23
POS_CMD_CALIB_DATUM_ALPHA = 24  # 24
POS_CMD_CALIB_DATUM_BETA = 25  # 25
POS_CMD_CALIB_MOTORS = 26  # 26
POS_CMD_CALIB_MOTOR_ALPHA = 27  # 27
POS_CMD_CALIB_MOTOR_BETA = 28  # 28
POS_CMD_GET_DATUM_CALIB_ERROR = 29  # 29   gets hall calibration error (maximum difference between
# magnetic field and hall value) (int32_t alpha, int32_t beta)
POS_CMD_GOTO_POSITION_ABSOLUTE = 30  # 30   starts movement to absolute position (int32_t alpha position,
# int32_t beta position)
POS_CMD_GOTO_POSITION_RELATIVE = 31  # 31   starts movement to relative position (int32_t alpha position,
# int32_t beta position)
POS_CMD_GET_ACTUAL_POSITION = 32  # 32   requests actual positions
POS_CMD_SET_ACTUAL_POSITION = 33  # 33   sets the actual configuration to the desired one IN IDEAL CASES
# THIS COMMAND IS NEVER USED
POS_CMD_GET_OFFSETS = 34  # 34
POS_CMD_SET_OFFSETS = 35  # 35
POS_CMD_SET_APPROACH_DISTANCE = 39  # 39   set approach distance
POS_CMD_SET_SPEED = 40  # 40   sets RPM speed for both motors (uint32_t alpha speed, uint32_t
# beta speed)
POS_CMD_SET_CURRENT = 41  # 41   set open loop current in percentage (uint32_t alpha current,
# uint32_t beta current)
POS_CMD_GET_HALL_OUTPUT_POS = 44  # 44   gets hall absolute positioning from output (int32_t alpha,
# int32_t beta)
POS_CMD_GET_MOTOR_CALIB_ERROR = 45  # 45   gets hall calibration error (maximum difference between
# magnetic field and hall value) (int32_t alpha, int32_t beta)
POS_CMD_CALIB_COGGING = 47
POS_CMD_CALIB_COGGING_ALPHA = 48
POS_CMD_CALIB_COGGING_BETA = 49
POS_CMD_SAVE_CALIBRATION_DATA = 53  # 53   save calibration parameters to flash
POS_CMD_GET_ACTUAL_POSITION_CURRENT_ALPHA = 54  # 54   get commanded position of alpha and measured current of alpha
POS_CMD_GET_ACTUAL_POSITION_CURRENT_BETA = 55  # 55   get commanded position of alpha and measured current of beta
POS_CMD_GET_CURRENT = 56  # 56   get measured current of alpha and beta
POS_CMD_GET_ACTUAL_POSITION_CMD_TORQUE_ALPHA = 57  # 57
POS_CMD_GET_ACTUAL_POSITION_CMD_TORQUE_BETA = 58  # 58
POS_CMD_GET_CMD_TORQUE = 59  # 59   get measured current of alpha and beta
POS_CMD_GET_ALPHA_HALL_CALIB = 104  # 104  request alpha hall sensors calibration values (4 x uint16_t
# maxA, maxB, minA, minB)
POS_CMD_GET_BETA_HALL_CALIB = 105  # 105  request beta hall sensors calibration values (4 x uint16_t
# maxA, maxB, minA, minB)
POS_CMD_GET_COGGING_LENGTH = 106  # 106  request length of cogging vectors
POS_CMD_GET_COGGING_POS = 107  # 107  request positive cogging parameter
POS_CMD_GET_COGGING_NEG = 108  # 108  request positive cogging parameter
POS_CMD_GET_COGGING_ANGLE = 110  # 110  request cogging position
POS_CMD_SET_INCREASE_COLLISION_MARGIN = 111  # 111
POS_CMD_SET_LOW_POWER_CURRENT = 112  # 112 set low power holding current: usually 0 for alpha, 30 for beta
POS_CMD_GET_LOW_POWER_CURRENT = 113  # 113 get low power holding current
POS_CMD_SET_APPROACHSPEED = 114
POS_CMD_SWITCH_ON_HALL_AFTER_MOVE_CMD = 116  # 116 after a move the hall sensors stay powered
POS_CMD_SWITCH_OFF_HALL_AFTER_MOVE_CMD = 117  # 117 after every move the hall sensors can be switched of with this
# command, a longer time is needed when a move is started to let the sensor start up
POS_CMD_SET_ALPHA_CLOSED_LOOP = 118  # 118 set alpha axis in closed loop with collision detection activated
POS_CMD_SET_ALPHA_CLOSED_LOOP_NO_COLL_DETECT = 119  # 119 set alpha axis in closed loop with collision detection
# deactivated
POS_CMD_SET_ALPHA_OPEN_LOOP = 120  # 120 set alpha axis in open loop with collision detection activated
POS_CMD_SET_ALPHA_OPEN_LOOP_NO_COLL_DETECT = 121  # 121 set alpha axis in open loop with collision detection deactivated
POS_CMD_SET_BETA_CLOSED_LOOP = 122  # 122 set beta axis in closed loop with collision detection activated
POS_CMD_SET_BETA_CLOSED_LOOP_NO_COLL_DETECT = 123  # 123 set beta axis in closed loop with collision detect. deactivated
POS_CMD_SET_BETA_OPEN_LOOP = 124  # 124 set beta axis in open loop with collision detection activated
POS_CMD_SET_BETA_OPEN_LOOP_NO_COLL_DETECT = 125  # 125 set alpha axis in open loop with collision detection deactivated
POS_CMD_SWITCH_ON_LED = 126  # 126 switch on led
POS_CMD_SWITCH_OFF_LED = 127  # 127 switch off led
POS_CMD_SWITCH_ON_PRECISE_ALPHA = 128  # 128 switch on precise mode for alpha
POS_CMD_SWITCH_OFF_PRECISE_ALPHA = 129  # 129 switch off precise mode for alpha
POS_CMD_SWITCH_ON_PRECISE_BETA = 130  # 130 switch on precise mode for alpha
POS_CMD_SWITCH_OFF_PRECISE_BETA = 131  # 131 switch off precise mode for alpha
POS_CMD_GET_TEMPERATURE = 132  # 132 get tempearture measurement
POS_CMD_REQUEST_REBOOT = 213  # 213  requests reboot to go into bootloader

# bootloader
POS_BOOTLOADER_SET_FACTORY_SETTING = 60
POS_BOOTLOADER_GET_FACTORY_SETTING = 61
POS_BOOTLOADER_SEND_NEW_FIRMWARE = 200
POS_BOOTLOADER_FIRMWARE_DATA = 201
POS_BOOTLOADER_GET_BOOTLOADER_VERSION = 210
POS_BOOTLOADER_GET_MAIN_VERSION = 211
POS_BOOTLOADER_GET_BACKUP_VERSION = 212
POS_BOOTLOADER_REQUEST_REBOOT = 213
POS_BOOTLOADER_GET_ROOT_ACCESS = 222

POS_BOOTLOADER_PARAM_POSITIONER_ID = 0  # 0 Positioner CAN ID
POS_BOOTLOADER_PARAM_POWER_LED_CONTROL = 1  # 1 Power LED control
POS_BOOTLOADER_PARAM_FIBRE_TYPE = 2  # 2 Fibre type installed
POS_BOOTLOADER_PARAM_ALPHA_REDUCTION = 3  # 3 alpha reduction ratio
POS_BOOTLOADER_PARAM_BETA_REDUCTION = 4  # 4 beta reduction ratio
POS_BOOTLOADER_PARAM_ALPHA_MODEL = 5  # 5 alpha model type
POS_BOOTLOADER_PARAM_BETA_MODEL = 6  # 6 beta model type
POS_BOOTLOADER_PARAM_ALPHA_CONTROL = 7  # 7 alpha control type
POS_BOOTLOADER_PARAM_BETA_CONTROL = 8  # 8 beta control type
POS_BOOTLOADER_PARAM_ALPHA_POLARITY = 9  # 9 alpha polarity
POS_BOOTLOADER_PARAM_BETA_POLARITY = 10  # 10 beta polarity
POS_BOOTLOADER_PARAM_ALPHA_MAX_SPEED = 11  # 11 alpha maximum speed
POS_BOOTLOADER_PARAM_BETA_MAX_SPEED = 12  # 12 beta maximum speed
POS_BOOTLOADER_PARAM_ALPHA_MAX_CURRENT = 13  # 13 alpha maximum current
POS_BOOTLOADER_PARAM_BETA_MAX_CURRENT = 14  # 14 beta maximum current
POS_BOOTLOADER_PARAM_ALPHA_ENCODER_RESOLUTION = 15  # 15 alpha encoder resolution
POS_BOOTLOADER_PARAM_BETA_ENCODER_RESOLUTION = 16  # 16 beta encoder resolution
POS_BOOTLOADER_PARAM_ALPHA_ENCODER_TYPE = 17  # 17 alpha encoder type
POS_BOOTLOADER_PARAM_BETA_ENCODER_TYPE = 18  # 18 beta encoder type
POS_BOOTLOADER_PARAM_ALPHA_COLLISION_DETECTION = 19  # 19 alpha collision detection
POS_BOOTLOADER_PARAM_BETA_COLLISION_DETECTION = 20  # 20 beta collision detection
POS_BOOTLOADER_PARAM_ALPHA_LOW_POS_LIMIT = 21  # 21 alpha lower position limit
POS_BOOTLOADER_PARAM_ALPHA_HIGH_POS_LIMIT = 22  # 22 alpha higher position limit
POS_BOOTLOADER_PARAM_BETA_LOW_POS_LIMIT = 23  # 23 beta lower position limit
POS_BOOTLOADER_PARAM_BETA_HIGH_POS_LIMIT = 24  # 24 beta higher position limit
POS_BOOTLOADER_PARAM_ALPHA_INTERPOLATION = 25  # 25 alpha interpolation type
POS_BOOTLOADER_PARAM_BETA_INTERPOLATION = 26  # 26 beta interpolation type
POS_BOOTLOADER_PARAM_ALPHA_MAX_ACCELERATION = 27  # 27 alpha maximum acceleration
POS_BOOTLOADER_PARAM_BETA_MAX_ACCELERATION = 28  # 28 beta maximum acceleration
POS_BOOTLOADER_PARAM_ALPHA_TORQUE_LIMIT = 29  # 29 alpha maximum torque limit
POS_BOOTLOADER_PARAM_BETA_TORQUE_LIMIT = 30  # 30 beta maximum torque limit
POS_BOOTLOADER_PARAM_POSITIONER_ROW = 31  # 31 positioner row position in FPS
POS_BOOTLOADER_PARAM_POSITIONER_COL = 32  # 32 positioner column position in FPS
POS_BOOTLOADER_PARAM_RESERVE_01 = 33  # 33 reserve configuration value 01
POS_BOOTLOADER_PARAM_RESERVE_02 = 34  # 34 reserve configuration value 02
POS_BOOTLOADER_PARAM_RESERVE_03 = 35  # 35 reserve configuration value 03
POS_BOOTLOADER_PARAM_RESERVE_04 = 36  # 36 reserve configuration value 04
POS_BOOTLOADER_PARAM_RESERVE_05 = 37  # 37 reserve configuration value 05
POS_BOOTLOADER_PARAM_RESERVE_06 = 38  # 38 reserve configuration value 06
POS_BOOTLOADER_PARAM_RESERVE_07 = 39  # 39 reserve configuration value 07
POS_BOOTLOADER_PARAM_RESERVE_08 = 40  # 40 reserve configuration value 08


# positioner status bits
class StatusRegistery:
    """
    The status registry of the positioner.

    Each parameter of the positioner's status registry in normal operation mode is listed here. These are read-only
    values and must not be modified.

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
        The alpha motor is configured to perform an approach move and precise positionning each time it reaches the end
        of the trajectory
    PRECISE_POSITIONING_BETA: uint64
        The alpha motor is configured to perform an approach move and precise positionning each time it reaches the end
        of the trajectory
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

    __slots__ = ('SYSTEM_INITIALIZED',
                 'CONFIG_CHANGED',
                 'BSETTINGS_CHANGED',
                 'DATA_STREAMING',
                 'RECEIVING_TRAJECTORY',
                 'TRAJECTORY_ALPHA_RECEIVED',
                 'TRAJECTORY_BETA_RECEIVED',
                 'LOW_POWER_AFTER_MOVE',
                 'DISPLACEMENT_COMPLETED',
                 'DISPLACEMENT_COMPLETED_ALPHA',
                 'DISPLACEMENT_COMPLETED_BETA',
                 'COLLISION_ALPHA',
                 'COLLISION_BETA',
                 'CLOSED_LOOP_ALPHA',
                 'CLOSED_LOOP_BETA',
                 'PRECISE_POSITIONING_ALPHA',
                 'PRECISE_POSITIONING_BETA',
                 'COLLISION_DETECT_ALPHA_DISABLE',
                 'COLLISION_DETECT_BETA_DISABLE',
                 'MOTOR_CALIBRATION',
                 'MOTOR_ALPHA_CALIBRATED',
                 'MOTOR_BETA_CALIBRATED',
                 'DATUM_CALIBRATION',
                 'DATUM_ALPHA_CALIBRATED',
                 'DATUM_BETA_CALIBRATED',
                 'DATUM_INITIALIZATION',
                 'DATUM_ALPHA_INITIALIZED',
                 'DATUM_BETA_INITIALIZED',
                 'HALL_ALPHA_DISABLE',
                 'HALL_BETA_DISABLE',
                 'COGGING_CALIBRATION',
                 'COGGING_ALPHA_CALIBRATED',
                 'COGGING_BETA_CALIBRATED',
                 'ESTIMATED_POSITION',
                 'POSITION_RESTORED',
                 'SWITCH_OFF_AFTER_MOVE',
                 'CALIBRATION_SAVED',
                 'PRECISE_MOVE_IN_OPEN_LOOP_ALPHA',
                 'PRECISE_MOVE_IN_OPEN_LOOP_BETA',
                 'SWITCH_OFF_HALL_AFTER_MOVE')

    def __init__(self):
        """Initializes the class instances"""

        # Status register bits for system
        self.SYSTEM_INITIALIZED = 0x0000000000000001
        self.CONFIG_CHANGED = 0x0000000000000002
        self.BSETTINGS_CHANGED = 0x0000000000000004
        self.DATA_STREAMING = 0x0000000000000008

        # Status register bits for communication
        self.RECEIVING_TRAJECTORY = 0x0000000000000010
        self.TRAJECTORY_ALPHA_RECEIVED = 0x0000000000000020
        self.TRAJECTORY_BETA_RECEIVED = 0x0000000000000040
        self.LOW_POWER_AFTER_MOVE = 0x0000000000000080

        # Status register bits for positioning
        self.DISPLACEMENT_COMPLETED = 0x0000000000000100
        self.DISPLACEMENT_COMPLETED_ALPHA = 0x0000000000000200
        self.DISPLACEMENT_COMPLETED_BETA = 0x0000000000000400
        self.COLLISION_ALPHA = 0x0000000000000800
        self.COLLISION_BETA = 0x0000000000001000
        self.CLOSED_LOOP_ALPHA = 0x0000000000002000
        self.CLOSED_LOOP_BETA = 0x0000000000004000
        self.PRECISE_POSITIONING_ALPHA = 0x0000000000008000
        self.PRECISE_POSITIONING_BETA = 0x0000000000010000
        self.COLLISION_DETECT_ALPHA_DISABLE = 0x0000000000020000
        self.COLLISION_DETECT_BETA_DISABLE = 0x0000000000040000

        self.MOTOR_CALIBRATION = 0x0000000000080000
        self.MOTOR_ALPHA_CALIBRATED = 0x0000000000100000
        self.MOTOR_BETA_CALIBRATED = 0x0000000000200000
        self.DATUM_CALIBRATION = 0x0000000000400000
        self.DATUM_ALPHA_CALIBRATED = 0x0000000000800000
        self.DATUM_BETA_CALIBRATED = 0x0000000001000000
        self.DATUM_INITIALIZATION = 0x0000000002000000
        self.DATUM_ALPHA_INITIALIZED = 0x0000000004000000
        self.DATUM_BETA_INITIALIZED = 0x0000000008000000
        self.HALL_ALPHA_DISABLE = 0x0000000010000000
        self.HALL_BETA_DISABLE = 0x0000000020000000

        self.COGGING_CALIBRATION = 0x0000000040000000
        self.COGGING_ALPHA_CALIBRATED = 0x0000000080000000
        self.COGGING_BETA_CALIBRATED = 0x0000000100000000

        self.ESTIMATED_POSITION = 0x0000000200000000
        self.POSITION_RESTORED = 0x0000000400000000

        self.SWITCH_OFF_AFTER_MOVE = 0x0000000800000000
        self.CALIBRATION_SAVED = 0x0000001000000000

        self.PRECISE_MOVE_IN_OPEN_LOOP_ALPHA = 0x0000002000000000
        self.PRECISE_MOVE_IN_OPEN_LOOP_BETA = 0x0000004000000000

        self.SWITCH_OFF_HALL_AFTER_MOVE = 0x0000008000000000

    def get_register_attributes(self, status):
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
            string += f'{slot:{maxLen + 2}s} : {bool(status & getattr(self, slot))}\n'

        return string

    def get_indexes_from_register(self, status):
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
            if bool(status & getattr(self, slot)):
                output.append(i)
            i += 1

        return output

    def get_register_from_indexes(self, indexes):
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
            i += 1

        return status


# positioner status bits
class StatusRegisteryBootloader:
    """
    The status registry of the positioner.

    Each parameter of the positioner's status registry in normal operation mode is listed here. These are read-only
    values and must not be modified.

    Attributes
    ----------

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

    __slots__ = ('BOOTLOADER_INIT',
                 'BOOTLOADER_TIMEOUT',
                 'CONFIG_CHANGED',
                 'BSETTINGS_CHANGED',
                 'RECEIVING_NEW_FIRMWARE',
                 'NEW_FIRMWARE_RECEIVED',
                 'NEW_FIRMWARE_CHECK_OK',
                 'NEW_FIRMWARE_CHECK_BAD',
                 'LAST_FIRMWARE_OK')

    def __init__(self):
        """Initializes the class instances"""

        # Status register bits for system
        self.BOOTLOADER_INIT = 0x00000001
        self.BOOTLOADER_TIMEOUT = 0x00000002
        self.CONFIG_CHANGED = 0x00000100
        self.BSETTINGS_CHANGED = 0x00000200
        self.RECEIVING_NEW_FIRMWARE = 0x00010000
        self.NEW_FIRMWARE_RECEIVED = 0x01000000
        self.NEW_FIRMWARE_CHECK_OK = 0x02000000
        self.NEW_FIRMWARE_CHECK_BAD = 0x04000000
        self.LAST_FIRMWARE_OK = 0x08000000

    def get_register_attributes(self, status):
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
            string += f'{slot:{maxLen + 2}s} : {bool(status & getattr(self, slot))}\n'

        return string

    def get_indexes_from_register(self, status):
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
            if bool(status & getattr(self, slot)):
                output.append(i)
            i += 1

        return output

    def get_register_from_indexes(self, indexes):
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
            i += 1

        return status
