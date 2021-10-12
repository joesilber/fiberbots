from defines import *
import time
from lawicel import Lawicel

message_stack = []


class Positioners():
    def __init__(self):
        self.connections = []
        self.dict = {}

    def __getitem__(self, key):
        return self.dict[key]

    def __iter__(self):
        return iter(self.dict)

    def connect(self, connection_device='lawicel', desiredserial=None):
        self.connect_to_can(connection_device, desiredserial)
        self.connect_to_positioners()

    def connect_to_can(self, connection_device='lawicel', desiredserial=None):
        # establish connection with CAN device
        if connection_device == 'lawicel':
            self.connections.append(Lawicel(desiredserial))  # establish connection to lawicel device
        else:
            print('unknown connection device: ' + connection_device)

    def connect_to_positioners(self):
        # check for number of available positioners and add them to the positioner list
        for connection in self.connections:
            available_pos = []
            if not connection.success:
                print(f'connection {connection.type} with serial number {connection.serial_no} is not valid')
            else:
                responses = send_receive_CAN(connection, 0, POS_CMD_GET_FIRMWARE)
                if not responses:
                    print(
                        f'no positioners found for connection {connection.type} with serial number {connection.serial_no}')
                    return
                else:
                    for response in responses:
                        available_pos.append(response[0])
            if available_pos:
                # self.dict = dict([(posID, PositionerUnit(posID, connection)) for posID in available_pos])
                for posID in available_pos:
                    if posID in self.dict:
                        print(f'positioner: {posID} already in list, info updated')
                        self.dict[posID].update_connection([connection])
                        # self.dict[posID].firmware=firmware
                    else:
                        self.dict[posID] = PositionerUnit(posID, [connection])
        pos_list = self.list_positioners()
        if pos_list:
            if 0 not in self.dict:
                self.all = PositionerUnit(0, self.connections)

    def list_positioners(self, pr=True):
        if pr:
            print('positioners in list:')
            print(', '.join(str(key) for key, value in self.dict.items()))
        return list(self.dict.keys())

    def remove_positioner(self, positioners):
        if isinstance(positioners, int):
            positioners = [positioners]
        for pos in positioners:
            if pos in self.dict:
                del self.dict[pos]
                print(f'positioner {pos} removed from list')
            else:
                print(f'positioner {pos} not in list')

    def available_positioners(self):
        available_pos = []
        for connection in self.connections:
            if not connection.success:
                print(f'connection {connection.type} with serial number {connection.serial_no} is not valid')
            else:
                responses = send_receive_CAN(connection, 0, POS_CMD_GET_FIRMWARE)
                if responses == []:
                    print(
                        f'no positioners found for connection {connection.type} with serial number {connection.serial_no}')
                    return
                else:
                    for response in responses:
                        available_pos.append(response[0])
        return available_pos

    def remove_not_available_positioners(self):
        available_pos = self.available_positioners()
        listed_pos = self.list_positioners(pr=False)
        not_available = list(set(listed_pos) - set(available_pos))
        self.remove_positioner(not_available)

    def available_positioners_not_in_list(self):
        available_pos = self.available_positioners()
        pos_not_in_list = []
        if available_pos:
            # self.dict = dict([(posID, PositionerUnit(posID, [connection])) for posID in available_pos])
            for posID in available_pos:
                if posID not in self.dict:
                    pos_not_in_list.append(posID)
            print(f'available positioners not in list: {pos_not_in_list}')
            return pos_not_in_list

    def show_connections(self):
        k = 0
        print('open connections:')
        for connection in self.connections:
            print(f'{k}: connection {connection.type} with nb {connection.serial_no}')
            k = k + 1

    def close_connection(self, numbers):
        if isinstance(numbers, int):
            numbers = [numbers]
        for number in numbers:
            try:
                self.connections[number].close()
                print(
                    f'{number}: connection {self.connections[number].type} with nb {self.connections[number].serial_no} closed')
                self.connections.pop(number)
            except Exception as e:
                print(
                    f'{number}: connection {self.connections[number].type} with nb {self.connections[number].serial_no} could not be closed')
                print(e)


def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func

    return decorate


@static_vars(UID_COUNT=0)
def send_receive_CAN(connection, id_pos, command, receive_data_type=1, data1=None, data2=None,
                     can_receive_delay=CAN_DELAY_IF_NO_MESSAGE_FOUND, manualHexFrame=None):
    response = []
    send_receive_CAN.UID_COUNT = send_receive_CAN.UID_COUNT + 1
    if send_receive_CAN.UID_COUNT >= 16:
        send_receive_CAN.UID_COUNT = 0

    if command is None:
        return []

    if not connection:
        print('no connection is established')
        return []

    ID = id_pos << CAN_ID_BIT_SHIFT
    IDcmd = (command << CAN_CMD_BIT_SHIFT) + ID
    txCmd = (send_receive_CAN.UID_COUNT << CAN_UID_BIT_SHIFT) + IDcmd
    txCmd = '%0.8X' % txCmd

    if manualHexFrame is not None:
        dataLength = len(manualHexFrame) / 2
        if dataLength > 8 or int(dataLength) != dataLength:
            print(f'pos{id_pos}-> error message: Invalid CAN frame length')
            response_code = -2  # command could not be sent
            data1 = []
            data2 = []
            response.append([id_pos, response_code, data1, data2])
            return response

        if dataLength == 0:
            manualHexFrame = ''
        elif dataLength == 1:
            manualHexFrame = '%0.2X' % (int(manualHexFrame, 16))
        elif dataLength == 2:
            manualHexFrame = '%0.4X' % (int(manualHexFrame, 16))
        elif dataLength == 3:
            manualHexFrame = '%0.6X' % (int(manualHexFrame, 16))
        elif dataLength == 4:
            manualHexFrame = '%0.8X' % (int(manualHexFrame, 16))
        elif dataLength == 5:
            manualHexFrame = '%0.10X' % (int(manualHexFrame, 16))
        elif dataLength == 6:
            manualHexFrame = '%0.12X' % (int(manualHexFrame, 16))
        elif dataLength == 7:
            manualHexFrame = '%0.14X' % (int(manualHexFrame, 16))
        elif dataLength == 8:
            manualHexFrame = '%0.16X' % (int(manualHexFrame, 16))

        dataLength = str(int(dataLength))

        send_str = txCmd + dataLength + manualHexFrame

    elif data1 is None and data2 is None:
        send_str = txCmd + '0'

    elif data2 is None:
        dataCmd = '%0.8X' % (swapInt32(data1 % (2 ** 32)))
        send_str = txCmd + '4' + dataCmd

    elif data1 is None:
        dataCmd = '%0.8X' % (swapInt32(data2 % (2 ** 32)))
        send_str = txCmd + '4' + dataCmd

    else:
        data1Cmd = '%0.8X' % (swapInt32(data1 % (2 ** 32)))
        data2Cmd = '%0.8X' % (swapInt32(data2 % (2 ** 32)))
        send_str = txCmd + '8' + data1Cmd + data2Cmd

    try:
        connection.send(send_str)
    except Exception as e:
        # print('command could not be sent:')
        print(f'pos{id_pos}-> error message: {e}')
        response_code = -2  # command could not be sent
        data1 = []
        data2 = []
        response.append([id_pos, response_code, data1, data2])
        return response

    matched_messages = receive_add_to_stack_check_for_message(connection, id_pos, send_receive_CAN.UID_COUNT)
    start_time = time.perf_counter()
    while ((not matched_messages) or (id_pos == 0)) and (
            time.perf_counter() - can_receive_delay <= start_time):  # check again received messages if message not found
        time.sleep(CAN_DELAY_IF_NO_MESSAGE_FOUND)
        matched_messages = receive_add_to_stack_check_for_message(connection, id_pos, send_receive_CAN.UID_COUNT)

    if not matched_messages:
        # print('error no message received')
        response_code = -1  # no response message received
        data1 = []
        data2 = []
        response.append([id_pos, response_code, data1, data2])
    else:
        for message in matched_messages:
            message_stack.remove(message)  # remove treated message from active message stack
            id_message = message[0]
            response_code = message[3]
            data1, data2 = decode_data(message, receive_data_type)
            response.append([id_message, response_code, data1, data2])
    # return response code and data
    return response


def receive_add_to_stack_check_for_message(connection, id_pos, uid):
    new_messages = connection.receive()
    # print(new_messages)
    for message in new_messages:
        message_stack.append(message)
    return check_for_message(id_pos, uid)


def check_for_message(pos_id, uid_count):
    matched_messages = []
    # print(f'UID send {uid_count}')
    for message in message_stack:
        # print(f'UID in stack {message[1]}')
        if pos_id == 0 and uid_count == message[1]:
            matched_messages.append(message)
        elif [pos_id, uid_count] == message[0:2]:
            matched_messages.append(message)
            return matched_messages
    return matched_messages


def decode_data(message, receive_data_type):
    """
    receive data type contains how the data send by the CAN should be decoded
    case=0 %no data is send back
    case=1 %uint32
    case=2 %int32
    case=3 %uint32, uint32
    case=4 %int32, int32
    case=5 %uint64
    case=6 %int64
    """
    data1 = []
    data2 = []
    if len(message[5]) >= 8:
        if receive_data_type == 1:
            data1 = swapInt32(int(message[5][0:8], 16))
        elif receive_data_type == 2:
            data1 = to_signed(swapInt32(int(message[5][0:8], 16)), 4)
    if len(message[5]) >= 16:
        if receive_data_type == 3:
            data1 = swapInt32(int(message[5][0:8], 16))
            data2 = swapInt32(int(message[5][8:17], 16))
        elif receive_data_type == 4:
            data1 = to_signed(swapInt32(int(message[5][0:8], 16)), 4)
            data2 = to_signed(swapInt32(int(message[5][8:17], 16)), 4)
        elif receive_data_type == 5:
            data1 = swapInt64(int(message[5][0:16], 16))
    return data1, data2


def to_signed(n, byte_count):
    return int.from_bytes(n.to_bytes(byte_count, 'little'), 'little', signed=True)


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

    return (((number << 8) & 0xFF00) |
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

    return (((number << 16) & 0xFF0000) |
            (number & 0x00FF00) |
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

    return (((number << 24) & 0xFF000000) |
            ((number << 8) & 0x00FF0000) |
            ((number >> 8) & 0x0000FF00) |
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

    return (((number << 32) & 0xFF00000000) |
            ((number << 16) & 0x00FF000000) |
            ((number) & 0x0000FF0000) |
            ((number >> 16) & 0x000000FF00) |
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

    return (((number << 40) & 0xFF0000000000) |
            ((number << 24) & 0x00FF00000000) |
            ((number << 8) & 0x0000FF000000) |
            ((number >> 8) & 0x000000FF0000) |
            ((number >> 24) & 0x00000000FF00) |
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

    return (((number << 48) & 0xFF000000000000) |
            ((number << 32) & 0x00FF0000000000) |
            ((number << 16) & 0x0000FF00000000) |
            ((number) & 0x000000FF000000) |
            ((number >> 16) & 0x00000000FF0000) |
            ((number >> 32) & 0x0000000000FF00) |
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

    return ((number << 56) & 0xFF00000000000000) | ((number << 40) & 0x00FF000000000000) | (
            (number << 24) & 0x0000FF0000000000) | ((number << 8) & 0x000000FF00000000) | (
                   (number >> 8) & 0x00000000FF000000) | ((number >> 24) & 0x0000000000FF0000) | (
                   (number >> 40) & 0x000000000000FF00) | ((number >> 56) & 0x00000000000000FF)


class Response:
    def __init__(self, pos_id, response):
        self.pos_id = pos_id
        self.response = pos_response_code[response]
        self.response_raw = response
        self.firmware = None
        self.status = None
        self.status_int = None
        self.move_time_alpha = None  # [sec]
        self.move_time_beta = None  # [sec]
        self.alpha = None  #
        self.beta = None  #


class PositionerUnit:
    def __init__(self, pos_id, connection):
        self.pos_id = pos_id
        self.firmware = ''
        self.connection = connection
        self.print = True

    def update_connection(self, connection):
        self.connection = connection

    def get_firmware(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_GET_FIRMWARE)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer_inst.firmware = reply[2]
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> firmware number: {answer_inst.firmware}")
                    else:
                        print(f"pos{answer_inst.pos_id}-> get firmware error: {answer_inst.response}")
        return answer

    def get_status(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_GET_STATUS, receive_data_type=5)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer_inst.status_int = reply[2]
                if answer_inst.response_raw == 0:
                    status = StatusRegistery()
                    answer_inst.status = status.get_register_attributes(reply[2])
                else:
                    answer_inst.status = ''
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> status:")
                        print(answer_inst.status)
                    else:
                        print(f"pos{answer_inst.pos_id}-> get status error: {answer_inst.response}")
        return answer

    def get_status_bootloader(self):
        self.request_reboot()
        answer = []
        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_CMD_GET_STATUS, receive_data_type=1,
                                   can_receive_delay=2)
        reply = replies[0]
        answer_inst = Response(reply[0], reply[1])  # create response instance
        answer_inst.status_int = reply[2]
        if answer_inst.response_raw == 0:
            status = StatusRegisteryBootloader()
            answer_inst.status = status.get_register_attributes(reply[2])
        #    print(bool(answer_inst.status_int & status.BOOTLOADER_INIT))
        #    print(bool(answer_inst.status_int & status.NEW_FIRMWARE_RECEIVED))
        else:
            answer_inst.status = ''
        answer.append(answer_inst)
        if self.print:
            if answer_inst.response_raw == 0:
                print(f"pos{answer_inst.pos_id}-> bootloader status:")
                print(answer_inst.status)
            else:
                print(f"pos{answer_inst.pos_id}-> get bootloader status error: {answer_inst.response}")
        return answer

    def init_datum(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_GOTO_DATUMS)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> init datum: {answer_inst.response}")
                    else:
                        print(f"pos{answer_inst.pos_id}-> init datum error: {answer_inst.response}")
        return answer

    def init_datum_alpha(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_GOTO_DATUM_ALPHA)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> init datum alpha: {answer_inst.response}")
                    else:
                        print(f"pos{answer_inst.pos_id}-> init datum alpha error: {answer_inst.response}")
        return answer

    def init_datum_beta(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_GOTO_DATUM_BETA)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> init datum beta: {answer_inst.response}")
                    else:
                        print(f"pos{answer_inst.pos_id}-> init datum beta error: {answer_inst.response}")
        return answer

    def calib_datum(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_CALIB_DATUMS)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> calib datum: {answer_inst.response}")
                    else:
                        print(f"pos{answer_inst.pos_id}-> calib datum error: {answer_inst.response}")
        return answer

    def calib_datum_alpha(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_CALIB_DATUM_ALPHA)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> calib datum alpha: {answer_inst.response}")
                    else:
                        print(f"pos{answer_inst.pos_id}-> calib datum alpha error: {answer_inst.response}")
        return answer

    def calib_datum_beta(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_CALIB_DATUM_BETA)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> calib datum beta: {answer_inst.response}")
                    else:
                        print(f"pos{answer_inst.pos_id}-> calib datum beta error: {answer_inst.response}")
        return answer

    def calib_motor(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_CALIB_MOTORS)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> calib motor: {answer_inst.response}")
                    else:
                        print(f"pos{answer_inst.pos_id}-> calib motor error: {answer_inst.response}")
        return answer

    def calib_motor_alpha(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_CALIB_MOTOR_ALPHA)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> calib motor alpha: {answer_inst.response}")
                    else:
                        print(f"pos{answer_inst.pos_id}-> calib motor alpha error: {answer_inst.response}")
        return answer

    def calib_motor_beta(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_CALIB_MOTOR_BETA)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> calib motor beta: {answer_inst.response}")
                    else:
                        print(f"pos{answer_inst.pos_id}-> calib motor beta error: {answer_inst.response}")
        return answer

    def get_datum_calib_error(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_GET_DATUM_CALIB_ERROR, receive_data_type=4)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                if answer_inst.response_raw == 0:
                    answer_inst.alpha = reply[2]
                    answer_inst.beta = reply[3]
                else:
                    answer_inst.alpha = []
                    answer_inst.beta = []
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(
                            f"pos{answer_inst.pos_id}-> datum calibration error: alpha={answer_inst.alpha}, beta={answer_inst.beta} [deg]")
                    else:
                        print(f"pos{answer_inst.pos_id}-> datum calibration error: {answer_inst.response}")
        return answer

    def goto(self, alpha, beta):
        answer = []
        alpha_pos = int(round(alpha / 360 * POS_MOTOR_STEPS))
        beta_pos = int(round(beta / 360 * POS_MOTOR_STEPS))
        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_CMD_GOTO_POSITION_ABSOLUTE, receive_data_type=3,
                                   data1=alpha_pos, data2=beta_pos)
        for reply in replies:  # one reply per positioner per command
            answer_inst = Response(reply[0], reply[1])  # create response instance
            if answer_inst.response_raw == 0:
                answer_inst.move_time_alpha = reply[2] * POS_TIME_STEP
                answer_inst.move_time_beta = reply[3] * POS_TIME_STEP
            else:
                answer_inst.move_time_alpha = 0
                answer_inst.move_time_beta = 0
            answer.append(answer_inst)
            if self.print:
                if answer_inst.response_raw == 0:
                    print(f"pos{answer_inst.pos_id}-> go to: alpha={alpha}, beta={beta} [deg]")
                    print(
                        f"pos{answer_inst.pos_id}-> go to: alpha={answer_inst.move_time_alpha}, beta={answer_inst.move_time_beta} [sec]")
                else:
                    print(f"pos{answer_inst.pos_id}-> go to error: {answer_inst.response}")
        return answer

    def goto_relative(self, alpha, beta):
        answer = []
        alpha_pos = int(round(alpha / 360 * POS_MOTOR_STEPS))
        beta_pos = int(round(beta / 360 * POS_MOTOR_STEPS))
        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_CMD_GOTO_POSITION_RELATIVE, receive_data_type=3,
                                   data1=alpha_pos, data2=beta_pos)
        for reply in replies:  # one reply per positioner per command
            answer_inst = Response(reply[0], reply[1])  # create response instance
            if answer_inst.response_raw == 0:
                answer_inst.move_time_alpha = reply[2] * POS_TIME_STEP
                answer_inst.move_time_beta = reply[3] * POS_TIME_STEP
            else:
                answer_inst.move_time_alpha = 0
                answer_inst.move_time_beta = 0
            answer.append(answer_inst)
            if self.print:
                if answer_inst.response_raw == 0:
                    print(f"pos{answer_inst.pos_id}-> go to relative: alpha={alpha}, beta={beta} [deg]")
                    print(
                        f"pos{answer_inst.pos_id}-> go to relative: alpha={answer_inst.move_time_alpha}, beta={answer_inst.move_time_beta} [sec]")
                else:
                    print(f"pos{answer_inst.pos_id}-> go to relative error: {answer_inst.response}")
        return answer

    def get_pos(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_GET_ACTUAL_POSITION, receive_data_type=4)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                if answer_inst.response_raw == 0:
                    answer_inst.alpha = reply[2] / POS_MOTOR_STEPS * 360
                    answer_inst.beta = reply[3] / POS_MOTOR_STEPS * 360
                else:
                    answer_inst.alpha = []
                    answer_inst.beta = []
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(
                            f"pos{answer_inst.pos_id}-> position: alpha={answer_inst.alpha}, beta={answer_inst.beta} [deg]")
                    else:
                        print(f"pos{answer_inst.pos_id}-> get position error: {answer_inst.response}")
        return answer

    def set_pos(self, alpha, beta):
        answer = []
        alpha_pos = int(round(alpha / 360 * POS_MOTOR_STEPS))
        beta_pos = int(round(beta / 360 * POS_MOTOR_STEPS))
        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_CMD_SET_ACTUAL_POSITION,
                                   data1=alpha_pos, data2=beta_pos,
                                   can_receive_delay=1.2)  # it takes time for the pos to set the position
        for reply in replies:  # one reply per positioner per command
            answer_inst = Response(reply[0], reply[1])  # create response instance
            answer.append(answer_inst)
            if self.print:
                if answer_inst.response_raw == 0:
                    print(f"pos{answer_inst.pos_id}-> position set: alpha={alpha}, beta={beta} [deg]")
                else:
                    print(f"pos{answer_inst.pos_id}-> position set error: {answer_inst.response}")
        return answer

    def get_offsets(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_GET_OFFSETS, receive_data_type=4)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                if answer_inst.response_raw == 0:
                    answer_inst.alpha = reply[2] / POS_MOTOR_STEPS * 360
                    answer_inst.beta = reply[3] / POS_MOTOR_STEPS * 360
                else:
                    answer_inst.alpha = []
                    answer_inst.beta = []
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(
                            f"pos{answer_inst.pos_id}-> offset: alpha={answer_inst.alpha}, beta={answer_inst.beta} [deg]")
                    else:
                        print(f"pos{answer_inst.pos_id}-> get offset error: {answer_inst.response}")
        return answer

    def set_offsets(self, alpha, beta):
        answer = []
        alpha_pos = int(round(alpha / 360 * POS_MOTOR_STEPS))
        beta_pos = int(round(beta / 360 * POS_MOTOR_STEPS))
        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_CMD_SET_OFFSETS,
                                   data1=alpha_pos, data2=beta_pos)
        for reply in replies:  # one reply per positioner per command
            answer_inst = Response(reply[0], reply[1])  # create response instance
            answer.append(answer_inst)
            if self.print:
                if answer_inst.response_raw == 0:
                    print(f"pos{answer_inst.pos_id}-> offset set: alpha={alpha}, beta={beta} [deg]")
                else:
                    print(f"pos{answer_inst.pos_id}-> offset set error: {answer_inst.response}")
        return answer

    def set_approach_distance(self, alpha, beta):
        answer = []
        alpha_pos = int(round(alpha / 360 * POS_MOTOR_STEPS))
        beta_pos = int(round(beta / 360 * POS_MOTOR_STEPS))
        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_CMD_SET_APPROACH_DISTANCE,
                                   data1=alpha_pos, data2=beta_pos)
        for reply in replies:  # one reply per positioner per command
            answer_inst = Response(reply[0], reply[1])  # create response instance
            answer.append(answer_inst)
            if self.print:
                if answer_inst.response_raw == 0:
                    print(f"pos{answer_inst.pos_id}-> apprach distance set: alpha={alpha}, beta={beta} [deg]")
                else:
                    print(f"pos{answer_inst.pos_id}-> apprach distance set error: {answer_inst.response}")
        return answer

    def set_speed(self, alpha_speed, beta_speed):
        answer = []
        alpha_speed = abs(int(round(alpha_speed)))
        beta_speed = abs(int(round(beta_speed)))
        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_CMD_SET_SPEED,
                                   data1=alpha_speed, data2=beta_speed)
        for reply in replies:  # one reply per positioner per command
            answer_inst = Response(reply[0], reply[1])  # create response instance
            answer.append(answer_inst)
            if self.print:
                if answer_inst.response_raw == 0:
                    print(f"pos{answer_inst.pos_id}-> speed set: alpha={alpha_speed}, beta={beta_speed} [rpm]")
                else:
                    print(f"pos{answer_inst.pos_id}-> speed set error: {answer_inst.response}")
        return answer

    def set_current(self, alpha_current, beta_current):
        answer = []
        alpha_current = abs(int(round(alpha_current)))
        if alpha_current > 100:
            alpha_current = 100
        beta_current = abs(int(round(beta_current)))
        if beta_current > 100:
            beta_current = 100
        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_CMD_SET_CURRENT,
                                   data1=alpha_current, data2=beta_current)
        for reply in replies:  # one reply per positioner per command
            answer_inst = Response(reply[0], reply[1])  # create response instance
            answer.append(answer_inst)
            if self.print:
                if answer_inst.response_raw == 0:
                    print(f"pos{answer_inst.pos_id}-> current set: alpha={alpha_current}, beta={beta_current} [rpm]")
                else:
                    print(f"pos{answer_inst.pos_id}-> current set error: {answer_inst.response}")
        return answer

    def get_hall_pos(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_GET_HALL_OUTPUT_POS, receive_data_type=4)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                if answer_inst.response_raw == 0:
                    answer_inst.alpha = reply[2] / POS_MOTOR_STEPS * 360
                    answer_inst.beta = reply[3] / POS_MOTOR_STEPS * 360
                else:
                    answer_inst.alpha = []
                    answer_inst.beta = []
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(
                            f"pos{answer_inst.pos_id}-> hall positions: alpha={answer_inst.alpha}, beta={answer_inst.beta} [deg]")
                    else:
                        print(f"pos{answer_inst.pos_id}-> get hall positions error: {answer_inst.response}")
        return answer

    def get_motor_calib_error(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_GET_MOTOR_CALIB_ERROR, receive_data_type=4)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                if answer_inst.response_raw == 0:
                    answer_inst.alpha = reply[2]
                    answer_inst.beta = reply[3]
                else:
                    answer_inst.alpha = []
                    answer_inst.beta = []
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(
                            f"pos{answer_inst.pos_id}-> motor calibration error: alpha={answer_inst.alpha}, beta={answer_inst.beta} [%]")
                    else:
                        print(f"pos{answer_inst.pos_id}-> get motor calibration error: {answer_inst.response}")
        return answer

    def save(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SAVE_CALIBRATION_DATA, can_receive_delay=1)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> positioner calibration data saved")
                    else:
                        print(f"pos{answer_inst.pos_id}-> save error: {answer_inst.response}")
        return answer

    def set_low_power_current(self, alpha_current, beta_current):
        answer = []
        alpha_current = abs(int(round(alpha_current)))
        if alpha_current > 100:
            alpha_current = 100
        beta_current = abs(int(round(beta_current)))
        if beta_current > 100:
            beta_current = 100
        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_CMD_SET_LOW_POWER_CURRENT,
                                   data1=alpha_current, data2=beta_current)
        for reply in replies:  # one reply per positioner per command
            answer_inst = Response(reply[0], reply[1])  # create response instance
            answer.append(answer_inst)
            if self.print:
                if answer_inst.response_raw == 0:
                    print(f"pos{answer_inst.pos_id}-> low power current set: alpha={alpha_current}, beta={beta_current} [%]")
                else:
                    print(f"pos{answer_inst.pos_id}-> get low power current error: {answer_inst.response}")
        return answer

    def get_low_power_current(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_GET_LOW_POWER_CURRENT, receive_data_type=4)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                if answer_inst.response_raw == 0:
                    answer_inst.alpha = reply[2]
                    answer_inst.beta = reply[3]
                else:
                    answer_inst.alpha = []
                    answer_inst.beta = []
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(
                            f"pos{answer_inst.pos_id}-> low power current: alpha={answer_inst.alpha}, beta={answer_inst.beta} [deg]")
                    else:
                        print(f"pos{answer_inst.pos_id}-> get low power current error: {answer_inst.response}")
        return answer

    def switch_on_hall(self):  # broadcast command
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SWITCH_ON_HALL_AFTER_MOVE_CMD)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> hall sensors switched on")
                    else:
                        print(f"pos{answer_inst.pos_id}-> hall sensors switched on error: {answer_inst.response}")
        return answer

    def switch_off_hall(self):  # broadcast command
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SWITCH_OFF_HALL_AFTER_MOVE_CMD)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> hall sensors switched off")
                    else:
                        print(f"pos{answer_inst.pos_id}-> hall sensors switched off error: {answer_inst.response}")
        return answer

    def set_alpha_closed_loop(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SET_ALPHA_CLOSED_LOOP)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> Alpha: closed loop, collision detection on")
                    else:
                        print(f"pos{answer_inst.pos_id}-> set alpha closed loop error: {answer_inst.response}")
        return answer

    def set_alpha_closed_loop_no_coll_detect(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SET_ALPHA_CLOSED_LOOP_NO_COLL_DETECT)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> ALpha: closed loop, collision detection off")
                    else:
                        print(
                            f"pos{answer_inst.pos_id}-> set alpha closed loop, coll detect off error: {answer_inst.response}")
        return answer

    def set_alpha_open_loop(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SET_ALPHA_OPEN_LOOP)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> Alpha: open loop, collision detection on")
                    else:
                        print(f"pos{answer_inst.pos_id}-> set alpha open loop error: {answer_inst.response}")
        return answer

    def set_alpha_open_loop_no_coll_detect(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SET_ALPHA_OPEN_LOOP_NO_COLL_DETECT)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> Alpha: open loop, collision detection off")
                    else:
                        print(
                            f"pos{answer_inst.pos_id}-> set alpha open loop, coll detect off error: {answer_inst.response}")
        return answer

    def set_beta_closed_loop(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SET_BETA_CLOSED_LOOP)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> Beta: closed loop, collision detection on")
                    else:
                        print(f"pos{answer_inst.pos_id}-> set beta closed loop error: {answer_inst.response}")
        return answer

    def set_beta_closed_loop_no_coll_detect(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SET_BETA_CLOSED_LOOP_NO_COLL_DETECT)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> Beta: closed loop, collision detection off")
                    else:
                        print(
                            f"pos{answer_inst.pos_id}-> set beta closed loop, coll detect off error: {answer_inst.response}")
        return answer

    def set_beta_open_loop(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SET_BETA_OPEN_LOOP)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> Beta: open loop, collision detection on")
                    else:
                        print(f"pos{answer_inst.pos_id}-> set beta open loop error: {answer_inst.response}")
        return answer

    def set_beta_open_loop_no_coll_detect(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SET_BETA_OPEN_LOOP_NO_COLL_DETECT)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> Beta: open loop, collision detection off")
                    else:
                        print(
                            f"pos{answer_inst.pos_id}-> set beta open loop, coll detect off error: {answer_inst.response}")
        return answer

    def switch_on_led(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SWITCH_ON_LED)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> LED switched on")
                    else:
                        print(f"pos{answer_inst.pos_id}-> LED switch on error: {answer_inst.response}")
        return answer

    def switch_off_led(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SWITCH_OFF_LED)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> LED switched off")
                    else:
                        print(f"pos{answer_inst.pos_id}-> LED switch off error: {answer_inst.response}")
        return answer

    def switch_on_precise_alpha(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SWITCH_ON_PRECISE_ALPHA)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> precise move alpha switched on")
                    else:
                        print(f"pos{answer_inst.pos_id}-> switch on precise alpha error: {answer_inst.response}")
        return answer

    def switch_on_precise_beta(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SWITCH_ON_PRECISE_BETA)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> precise move beta switched on")
                    else:
                        print(f"pos{answer_inst.pos_id}-> switch on precise beta error: {answer_inst.response}")
        return answer

    def switch_off_precise_alpha(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SWITCH_OFF_PRECISE_ALPHA)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> precise move alpha switched off")
                    else:
                        print(f"pos{answer_inst.pos_id}-> switch off precise alpha error: {answer_inst.response}")
        return answer

    def switch_off_precise_beta(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SWITCH_OFF_PRECISE_BETA)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> precise move beta switched off")
                    else:
                        print(f"pos{answer_inst.pos_id}-> switch off precise beta error: {answer_inst.response}")
        return answer

    def request_reboot(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_REQUEST_REBOOT)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> rebooting")
                    else:
                        print(f"pos{answer_inst.pos_id}-> request reboot error: {answer_inst.response}")
        return answer

    def send_trajectory(self, alpha_traj, beta_traj):
        answer = []

        alpha_traj = [[data_point[0] / 360 * POS_MOTOR_STEPS, data_point[1] / POS_TIME_STEP] for data_point in
                      alpha_traj]
        beta_traj = [[data_point[0] / 360 * POS_MOTOR_STEPS, data_point[1] / POS_TIME_STEP] for data_point in
                     beta_traj]

        # start sending trajectory
        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_CMD_SEND_TRAJECTORY_NEW,
                                   data1=len(alpha_traj), data2=len(beta_traj))
        reply = replies[0]
        # print(f'start: {pos_response_code[reply[1]]}')
        if reply[1] != 0:  # if command is not accepted return
            print(reply[1])
            answer_inst = Response(reply[0], reply[1])  # create response instance
            answer.append(answer_inst)
            if self.print:
                print(f"pos{answer_inst.pos_id}-> send trajectory new error: {answer_inst.response}")
            return answer

        # send trajectory alpha
        for data_point in alpha_traj:
            replies = send_receive_CAN(self.connection[0], self.pos_id, POS_CMD_SEND_TRAJECTORY_DATA,
                                       data1=abs(int(round(data_point[0]))), data2=abs(int(round(data_point[1]))))
            reply = replies[0]
            # print(f'alpha data point: {pos_response_code[reply[1]]}')
            if reply[1] != 0:  # if command is not accepted return
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    print(f"pos{answer_inst.pos_id}-> send trajectory alpha data error: {answer_inst.response}")
                return answer

        # send trajectory beta
        for data_point in beta_traj:
            replies = send_receive_CAN(self.connection[0], self.pos_id, POS_CMD_SEND_TRAJECTORY_DATA,
                                       data1=abs(int(round(data_point[0]))), data2=abs(int(round(data_point[1]))))
            reply = replies[0]
            # print(f'beta data point: {pos_response_code[reply[1]]}')
            if reply[1] != 0:  # if command is not accepted return
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    print(f"pos{answer_inst.pos_id}-> send trajectory beta data error: {answer_inst.response}")
                return answer

        # trajectory end
        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_CMD_SEND_TRAJECTORY_DATA_END)
        reply = replies[0]
        # print(f'end: {pos_response_code[reply[1]]}')

        answer_inst = Response(reply[0], reply[1])  # create response instance
        answer.append(answer_inst)

        if self.print:
            if answer_inst.response_raw == 0:
                print(f"pos{answer_inst.pos_id}-> send trajectory complete")
            else:
                print(f"pos{answer_inst.pos_id}-> send trajectory end error: {answer_inst.response}")
        return answer

    def start_trajectory(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_START_TRAJECTORY)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> start trajectory")
                    else:
                        print(f"pos{answer_inst.pos_id}-> start trajectory error: {answer_inst.response}")
        return answer

    def stop_and_clear_collision_flag(self):
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_STOP_TRAJECTORY)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> stop positioner and clear collision flags")
                    else:
                        print(f"pos{answer_inst.pos_id}-> error: {answer_inst.response}")
        return answer

    def stop(self):  # This command is used to stop the motion of the actuators. It will also reset the trajectories
        # and stop any movement or calibration mode.
        answer = []
        for connection in self.connection:  # only broadcast comm 0 has multiple connection handles
            replies = send_receive_CAN(connection, self.pos_id, POS_CMD_SEND_TRAJECTORY_ABORT)
            for reply in replies:  # one reply per positioner per command
                answer_inst = Response(reply[0], reply[1])  # create response instance
                answer.append(answer_inst)
                if self.print:
                    if answer_inst.response_raw == 0:
                        print(f"pos{answer_inst.pos_id}-> stop positioner")
                    else:
                        print(f"pos{answer_inst.pos_id}-> error: {answer_inst.response}")
        return answer

    def get_alpha_reduction_ratio(self):
        answer = []
        # request reboot
        self.request_reboot()
        time.sleep(0.1)
        # get factory settings
        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_BOOTLOADER_GET_FACTORY_SETTING,
                                   data1=POS_BOOTLOADER_PARAM_ALPHA_REDUCTION, receive_data_type=2)
        reply = replies[0]
        answer_inst = Response(reply[0], reply[1])  # create response instance

        answer_inst.alpha = reply[2]
        answer.append(answer_inst)
        if self.print:
            if answer_inst.response_raw == 0:
                print(f"pos{answer_inst.pos_id}-> alpha reduction ratio {answer_inst.alpha}")
            else:
                print(f"pos{answer_inst.pos_id}-> error: {answer_inst.response}")
        return answer

    def get_beta_reduction_ratio(self):
        answer = []
        # request reboot
        self.request_reboot()
        time.sleep(0.1)
        # get factory settings
        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_BOOTLOADER_GET_FACTORY_SETTING,
                                   data1=POS_BOOTLOADER_PARAM_BETA_REDUCTION, receive_data_type=2)
        reply = replies[0]
        answer_inst = Response(reply[0], reply[1])  # create response instance

        answer_inst.beta = reply[2]
        answer.append(answer_inst)
        if self.print:
            if answer_inst.response_raw == 0:
                print(f"pos{answer_inst.pos_id}-> beta reduction ratio {answer_inst.beta}")
            else:
                print(f"pos{answer_inst.pos_id}-> error: {answer_inst.response}")
        return answer

    def set_alpha_reduction_ratio(self, alpha_reduction_ratio):
        answer = []
        # request reboot
        self.request_reboot()

        # get root access
        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_BOOTLOADER_GET_ROOT_ACCESS)
        reply = replies[0]
        if reply[1] != 0:  # if command is not accepted return
            answer_inst = Response(reply[0], reply[1])  # create response instance
            answer.append(answer_inst)
            if self.print:
                print(f"pos{answer_inst.pos_id}-> root access not successful: {answer_inst.response}")
            return answer
        # set factory settings
        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_BOOTLOADER_SET_FACTORY_SETTING,
                                   data1=POS_BOOTLOADER_PARAM_ALPHA_REDUCTION, data2=int(round(alpha_reduction_ratio)))
        reply = replies[0]
        answer_inst = Response(reply[0], reply[1])  # create response instance
        answer.append(answer_inst)
        if self.print:
            if answer_inst.response_raw == 0:
                print(f"pos{answer_inst.pos_id}-> alpha reduction ratio set: {alpha_reduction_ratio}")
            else:
                print(f"pos{answer_inst.pos_id}-> alpha reduction ratio set error: {answer_inst.response}")
        return answer

    def set_beta_reduction_ratio(self, beta_reduction_ratio):
        answer = []
        # request reboot
        self.request_reboot()

        # get root access
        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_BOOTLOADER_GET_ROOT_ACCESS)
        reply = replies[0]
        if reply[1] != 0:  # if command is not accepted return
            answer_inst = Response(reply[0], reply[1])  # create response instance
            answer.append(answer_inst)
            if self.print:
                print(f"pos{answer_inst.pos_id}-> root access not successful: {answer_inst.response}")
            return answer
        # set factory settings
        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_BOOTLOADER_SET_FACTORY_SETTING,
                                   data1=POS_BOOTLOADER_PARAM_BETA_REDUCTION, data2=int(round(beta_reduction_ratio)))
        reply = replies[0]
        answer_inst = Response(reply[0], reply[1])  # create response instance
        answer.append(answer_inst)
        if self.print:
            if answer_inst.response_raw == 0:
                print(f"pos{answer_inst.pos_id}-> beta reduction ratio set: {beta_reduction_ratio}")
            else:
                print(f"pos{answer_inst.pos_id}-> beta reduction ratio set error: {answer_inst.response}")
        return answer

    def upgrade_firmware(self, firmwareFile):
        import time
        import zlib

        # read the new firmware and store the frames to send
        newFirmware = []
        firmwareFrames = []
        data = {'firmwareLength': 0,
                'firmwareChecksum': 0,
                'firmwareData': ''}

        with open(firmwareFile, 'rb') as file:
            newFirmware = file.read()
        # print(newFirmware)
        data['firmwareLength'] = len(newFirmware)
        data['firmwareChecksum'] = zlib.crc32(newFirmware)

        n = 8  # as we want max 8 Bytes per frame
        firmwareFrames = [(newFirmware[i:i + n]).hex() for i in range(0, len(newFirmware), n)]
        # print(firmwareFrames)
        print(
            f"pos{self.pos_id}-> Firmware length: {data['firmwareLength']} Bytes, checksum is {data['firmwareChecksum']}")
        tStart = time.perf_counter()
        print(f"pos{self.pos_id}-> Upgrading firmware")

        self.request_reboot()
        time.sleep(2)

        replies = send_receive_CAN(self.connection[0], self.pos_id, POS_BOOTLOADER_SEND_NEW_FIRMWARE,
                                   data1=data['firmwareLength'], data2=data['firmwareChecksum'], can_receive_delay=10)
        time.sleep(2)
        reply = replies[0]
        if reply[1] != 0:
            answer_inst = Response(reply[0], reply[1])  # create response instance
            print(f"pos{answer_inst.pos_id}-> bootloader start send error: {answer_inst.response}")
            return
        # print(f"start firmware {reply}")

        frameID = 1
        for frame in firmwareFrames:
            if (not frameID % 500) or frameID >= len(firmwareFrames):
                print(f'Sending firmware {100 * frameID / len(firmwareFrames):3.2f} %')
                # replies = send_receive_CAN(self.connection[0], self.pos_id, POS_CMD_GET_STATUS, receive_data_type=1,
                #                            can_receive_delay=10)
                # reply = replies[0]
                # print(reply)
                # if reply[1] == 0:
                #    status = StatusRegisteryBootloader()
                #    print(status.get_register_attributes(reply[2]))
            replies = send_receive_CAN(self.connection[0], self.pos_id, POS_BOOTLOADER_FIRMWARE_DATA,
                                       manualHexFrame=frame, can_receive_delay=45)
            reply = replies[0]
            if reply[1] != 0:
                answer_inst = Response(reply[0], reply[1])  # create response instance
                print(f"pos{self.pos_id}-> bootloader send error: {answer_inst.response}, frame: {frameID}")
                # aaaa
                replies = send_receive_CAN(self.connection[0], self.pos_id, POS_CMD_GET_STATUS, receive_data_type=1,
                                           can_receive_delay=10)
                reply = replies[0]
                print(reply)
                if reply[1] == 0:
                    status = StatusRegisteryBootloader()
                    print(status.get_register_attributes(reply[2]))
                else:
                    return
                # let's try again
                replies = send_receive_CAN(self.connection[0], self.pos_id, POS_BOOTLOADER_FIRMWARE_DATA,
                                           manualHexFrame=frame, can_receive_delay=45)
                reply = replies[0]
                print(reply)
                if reply[1] != 0:
                    return
                print(f"pos{self.pos_id}-> bootloader send error: frame sent with second try")

            # print(f"data firmware {reply}")
            frameID += 1

        firmware_received = False
        end_count = 1
        status = StatusRegisteryBootloader()
        while (not firmware_received) and (end_count < 10):
            end_count = end_count + 1
            replies = send_receive_CAN(self.connection[0], self.pos_id, POS_CMD_GET_STATUS, receive_data_type=1,
                                       can_receive_delay=10)
            reply = replies[0]
            # print(reply)
            if reply[1] == 0:
                # print(status.get_register_attributes(reply[2]))
                firmware_received = bool(reply[2] & status.NEW_FIRMWARE_RECEIVED)
                # print(firmware_received)
        if bool(reply[2] & status.NEW_FIRMWARE_CHECK_OK) and reply[1] == 0:  # check if new firmware check bit set
            print(f"pos{self.pos_id}-> Firmware upgrade successful")
        else:
            print(f"pos{self.pos_id}-> Firmware upgrade failed")

        print(f"pos{self.pos_id}-> Total time: {time.perf_counter() - tStart:.2f} [s]")
