import time
import socket
import shutil
import os
import logging

"""
Using TCP/I.P. protocol, python socket connection
Change PC_SEM_IP as needed

"""
class AbstractExternalCommunication:

    PC_SEM_IP = '192.168.0.1'
    LAPTOP_IP = socket.gethostbyname(socket.gethostname())
    SEM_PORT = 3000
    BUFF_SIZE = 1024

    def __init__(self):
        self.connection = None
        self.socket = None
        self.pc_sem_dir_temp = ''

    def set_sem_dir_temp(self, sem_dir_temp):
        self.pc_sem_dir_temp = sem_dir_temp

    def get_connection(self):
        return self.connection

    def set_connection(self, connection):
        self.connection = connection

    def get_socket(self):
        return self.socket

    def set_socket(self, socket):
        self.socket = socket

    def clear_savedir_pc_sem(self):
        if os.path.exists(self.pc_sem_dir_temp):
            shutil.rmtree(self.pc_sem_dir_temp)
            os.makedirs(self.pc_sem_dir_temp)
        else:
            os.makedirs(self.pc_sem_dir_temp)

    def initiate_connection(self):
        logging.info("Connecting to PC-SEM ...")
        su8230_socket = socket.socket(socket.AF_INET)
        su8230_socket.bind((self.LAPTOP_IP, self.SEM_PORT))
        su8230_socket.listen()
        su8230_socket.settimeout(20)  # Timeout to close the connection after a while if it didnt work
        try:
            connection, address = su8230_socket.accept()
            logging.info("Connected")
            connection.settimeout(20)
            self.set_connection(connection)
            self.set_socket(su8230_socket)

        except socket.timeout:
            print(f'Connection to PC SEM failed. Verify that Ethernet on SEM PC is set to  {self.LAPTOP_IP} and firewall '
                  f'is authorised for all Python processes. Go to :  '
                  f'Control Panel\Windows Defender Firewall\Allowed Apps')

    def validate_connection(self, command_string):
        logging.info("Start")
        su8230_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        su8230_socket.bind((self.LAPTOP_IP, self.SEM_PORT))

        su8230_socket.listen()
        su8230_socket.settimeout(20)
        try:
            connection, address = su8230_socket.accept()
            with connection:
                logging.info('Connected by' + str(address))
                connection.settimeout(20)

                # Try to send a get command
                logging.info(f"Sent command : {command_string}")
                instrument_name_byte = command_string.encode('UTF-8')
                send_data = connection.send(instrument_name_byte)
                # logging.info(str(send_data))  #
                message = connection.recv(self.BUFF_SIZE)
                logging.info(f"Received command : {message}")
                connection.close()
                logging.info("Close")
        except socket.timeout:
            print(f'Connection to PC SEM failed. Verify that Ethernet on SEM PC is set to  {self.LAPTOP_IP} and firewall'
                  f'is authorised for all Python processes. Go to :  '
                  f'Panneau de configuration\Système et sécurité\Pare-feu Windows Defender\Applications autorisées')

    def close_connection(self):
        connection = self.get_connection()
        su8230_socket = self.get_socket()
        if connection is not None:
            connection.close()
            su8230_socket.close()
            logging.info("Connection closed")

    def send_command(self, send_command_string, log=True):
        time.sleep(2)
        connection = self.get_connection()
        while connection is None:
            self.initiate_connection()
            connection = self.get_connection()

        # TODO find out if connection is open before sending a command
        try:
            self.send_text_command(connection, send_command_string, log)
        except:
            print(socket.error)
            self.close_connection()

    def send_text_command(self, connection, send_command_string, log):
        pass

    def receive_command(self, log=True):
        time.sleep(2)
        connection = self.get_connection()
        return self.receive_text_command(connection, log)

    def receive_text_command(self, connection, log):
        pass

    def wait_command_complete(self):
        pass

    def process_get_command(self, command_string):
        self.initiate_connection()
        self.send_command(command_string)
        dictDecodedMessage = self.receive_command()

        # Wait for SEM to be idle
        isComplete = self.wait_command_complete()
        if isComplete:
            self.close_connection()
            return dictDecodedMessage

        return None

    def process_set_command(self, command_string):
        self.initiate_connection()
        self.send_command(command_string)
        dictDecodedMessage = self.receive_command()
        # Wait for SEM to be idle
        isComplete = self.wait_command_complete()
        if isComplete:
            self.close_connection()

        self.validate_return_status(dictDecodedMessage)

    def validate_return_status(self, dictDecodedMessage):
        pass