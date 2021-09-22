import time
from serial.tools import list_ports
import serial

CAN_DELAY_BETWEEN_CONFIG_COMMANDS = 0.5  # [s]
CAN_TIMEOUT_DELAY = 0.2


def decode_messages(messages):
    while 'Z' in messages:  # remove can usb acknowledgment messages
        messages.remove('Z')

    received_messages = []
    for message in messages:
        if len(message) >= 10:
            idCode = ((int(message[1:5],
                           16)) >> 2) & 0b011111111111  # extract the ID, get first 14bits but disregard first 3bits
            command = ((int(message[4:7], 16)) >> 2) & 0b11111111  # extract the command code
            uid = ((int(message[7:9], 16)) >> 4) & 0b111111  # extract unique identifier
            response_code = (int(message[8], 16)) & 0b1111  # extract the response code
            nb_data_bytes = int(message[9], 16)
            data_string = ''
            if nb_data_bytes == 4:
                data_string = message[10:18]
            elif nb_data_bytes == 8:
                data_string = message[10:26]
            received_messages.append([idCode, uid, command, response_code, nb_data_bytes, data_string])
    # print(messages)
    return received_messages


class Lawicel:
    def __init__(self, desiredserial=None):
        self.type = 'lawicel'
        print('scan for serial ports and try to connect')
        serial_list = list(list_ports.comports())
        for port_no, description, device in serial_list:
            #print(f"a {port_no} b {description} c {device}")
            if 'USB' in description:
                try:
                    handle = serial.Serial(port_no)
                except serial.SerialException as e:
                    print(port_no + ': serial exception')
                    #print('serial port might be already in use')
                    #print(e)
                    handle = None

                if handle is not None:  # If the connexion was successful
                    #print(handle)
                    try:
                        handle.reset_input_buffer()
                        # Retrieve the serial number
                        handle.write('N\r'.encode())  # C\r

                        watchdog = time.perf_counter()
                        while handle.inWaiting() < 6 and time.perf_counter() - CAN_DELAY_BETWEEN_CONFIG_COMMANDS < watchdog:
                            _ = 1

                        input_buffer = handle.readline(handle.inWaiting())

                        if not len(input_buffer.decode()) == 6:
                            print(
                                'Wrong lawicel serial number length')  # raise errors.CANError("CAN could not retrieve the transceiver's serial number") from None
                            raise Exception
                        else:
                            serial_no = str(input_buffer[1:5].decode())
                            print(f'{port_no}: lawicel CAN USB found with serial: {serial_no}')
                    except Exception as e:
                        handle.close()
                        print(e)
                        # raise e from None
                    else:
                        if serial_no == desiredserial or desiredserial is None:
                            print(f'connecting to lawicel CAN USB: {serial_no}')
                            try:
                                handle.write('C\r'.encode())  # Close can channel
                                handle.write('S8\r'.encode())  # Set the Baud rate to 1Mb/s
                                handle.write('O\r'.encode())  # Open can channel
                                handle.reset_input_buffer()
                            except Exception as e:
                                print('lawicel CAN USB connection failed to set Baudrate or open channel')
                                print(e)
                            self.handle = handle
                            self.serial_no = serial_no
                            self.success = True
                            return
                        handle.close()
        print('No lawicel connection has been established')
        self.handle = []
        self.serial_no = []
        self.success = False

    def send(self, send_str):
        self.handle.reset_input_buffer()
        self.handle.write(('T' + send_str + '\r').encode())  # t(ID)4(data)\r

    def receive(self, timeoutdelay=CAN_TIMEOUT_DELAY, expect_data=False):
        if not self.handle:
            print('handle is empty')
            return
        responseOffset = 2
        responseLength = 11
        nbResponses = 1
        dataLength = 4
        nbData = 2

        # expect_data = True
        if expect_data:
            responseCharacters = nbResponses * (responseLength + 2 * dataLength * nbData) + responseOffset
        else:
            responseCharacters = responseLength + responseOffset

        watchdog = time.perf_counter()
        stayInLoop = True
        nbChar = 0
        previousNbChar = 0

        while (nbChar < responseCharacters or stayInLoop) and time.perf_counter() - timeoutdelay < watchdog:
            nbChar = self.handle.inWaiting()
            if nbChar >= responseCharacters and previousNbChar == nbChar:
                stayInLoop = False
            previousNbChar = nbChar

        input_buffer = self.handle.read(self.handle.inWaiting())  # get whole input buffer
        inputMessages = input_buffer.decode().split('\r')  # get all the messages received

        #print('bb')
        #print(input_buffer)
        #print('cc')
        #print(inputMessages)
        received_messages = decode_messages(inputMessages)
        # add messages to log
        return received_messages

    def close(self):
        self.handle.reset_input_buffer()
        self.handle.reset_output_buffer()
        self.handle.close()
        print('we CLOSED')
