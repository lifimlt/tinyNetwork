# -*- coding: utf-8 -*-
#
#  * \brief   This project about Tiny Network Serial.
#  *
#  * \License  THIS FILE IS PART OF MULTIBEANS PROJECT;
#  *           all of the files  - The core part of the project;
#  *           THIS PROGRAM IS NOT FREE SOFTWARE, NEED MULTIBEANS ORG LIC;
#  *
#  *                ________________     ___           _________________
#  *               |    __    __    |   |   |         |______     ______|
#  *               |   |  |  |  |   |   |   |                |   |
#  *               |   |  |__|  |   |   |   |________        |   |
#  *               |___|        |___|   |____________|       |___|
#  *
#  *                               MULTIBEANS ORG.
#  *                     Homepage: http://www.mltbns.com/
#  *
#  *           * You can download the license on our Github. ->
#  *           * -> https://github.com/lifimlt  <-
#  *           * Copyright (c) 2020 Carlos Wei: # carlos.wei.hk@gmail.com.
#  *           * Copyright (c) 2013-2020 MULTIBEANS ORG. http://www.mltbns.com/
#  *
#  *  \note    void.
#  ****************************************************************************

import sys
import subprocess
import MainUi
import platform
import socket
import threading
import psutil
import numpy
from HexConvert import HexConvert as hexConv
from Agent import TcpAgent as tcpAgent
from Agent import UdpAgent as udpAgent
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QMessageBox, QLabel, QHeaderView
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import pyqtSignal, QByteArray, QModelIndex
from PyQt5 import QtCore

''' BACKUP SLOT FUNCTIONS ON MainUi.py to avoid MainUi.py is re-write when converted to MainUi.py automatilly.

        self.comboBoxProtocal.currentIndexChanged['int'].connect(MainWindow.on_comboBoxProtocal_currentIndexChanged)
        self.comboBoxMode.currentIndexChanged['int'].connect(MainWindow.on_comboBoxMode_currentIndexChanged)
        self.comboBoxEthList.currentIndexChanged['int'].connect(MainWindow.on_comboBoxEthList_currentIndexChanged)
        self.checkBoxWordWrap.clicked['bool'].connect(MainWindow.on_checkBoxWordWrap_clicked)
        self.checkBoxDisplayTime.clicked['bool'].connect(MainWindow.on_checkBoxDisplayTime_clicked)
        self.checkBoxDisplayRecTime.clicked['bool'].connect(MainWindow.on_checkBoxDisplayRecTime_clicked)
        self.checkBoxRepeatSend.clicked['bool'].connect(MainWindow.on_checkBoxRepeatSend_clicked)
        self.radioButtonSendASCII.clicked.connect(MainWindow.on_radioButtonSendASCII_clicked)
        self.radioButtonSendHex.clicked.connect(MainWindow.on_radioButtonSendHex_clicked)
        self.radioButtonRecASCII.clicked.connect(MainWindow.on_radioButtonRecASCII_clicked)
        self.radioButtonRecHex.clicked.connect(MainWindow.on_radioButtonRecHex_clicked)
        self.spinBox.valueChanged['int'].connect(MainWindow.on_spinBoxTime_valueChanged)
        self.pushButtonConnect.clicked.connect(MainWindow.on_pushButtonConnect_click)
        self.pushButtonPing.clicked.connect(MainWindow.on_pushButtonPing_click)
        self.pushButtonDisconnect.clicked.connect(MainWindow.on_pushButtonDisconnect_click)
        self.pushButtonSend.clicked.connect(MainWindow.on_pushButtonSend_clicked)
        self.pushButtonClear.clicked.connect(MainWindow.on_pushButtonClear_clicked)
        self.pushButtonWriteIp.clicked.connect(MainWindow.on_pushButtonWriteIp_clicked)
        self.pushButtonAppIp.clicked.connect(MainWindow.on_pushButtonAppIp_clicked)
        self.tableWidgetClientList.clicked["QModelIndex"].connect(MainWindow.on_tableWidgetClientList_clicked)
        
'''

class MainWindow(QMainWindow):

    ui = MainUi.Ui_MainWindow()
    # UI MACROS
    MODE_SERVER = 0
    MODE_CLIENT = 1
    tcp_mode = MODE_CLIENT
    PROTOCAL_TCP = 0
    PROTOCAL_UDP = 1
    protocal_mode = PROTOCAL_TCP
    tcpAgent = tcpAgent()
    udpAgent = udpAgent()
    eth_device_list = []

    ASCII_FLAG = 0
    HEX_FLAG = 1
    recv_disp_mode = ASCII_FLAG
    send_disp_mode = ASCII_FLAG

    is_disp_send_time = False
    is_disp_recv_time = False
    is_word_wrap = False
    is_repeat_send_mode = False

    repeat_send_time_ms = 0

    client_list_count = 0
    client_list = []

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui.setupUi(self)
        self.setWindowTitle("Tiny Network Tool v1.0")
        self.init_ui_logic()

    def on_btn_click_signal(self):
        k = 1
        #self.ui.label.setText("hello")

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip

    def init_ui_logic(self):
        self.ui.lineEditAimIp.setText("192.168.31.1")
        self.ui.lineEditLocalPort.setText( "8388" )
        self.ui.lineEditLocalIp.setText( self.get_local_ip() )
        self.ui.comboBoxMode.setCurrentIndex( self.tcp_mode )
        self.ui.comboBoxProtocal.setCurrentIndex( self.protocal_mode )
        self.ui.pushButtonDisconnect.setEnabled(False)
        self.ui.radioButtonRecASCII.setChecked(True)
        self.ui.radioButtonSendASCII.setChecked(True)
        self.refresh_devices_list()
        if self.ui.comboBoxMode.currentIndex() == self.MODE_CLIENT:
            self.ui.groupBoxClientList.setHidden(True)
            self.setMaximumSize(0,0)
        else:
            self.ui.groupBoxClientList.setHidden(False)
            self.setMaximumSize(0,0)
        # init table widget of client list
        self.ui.tableWidgetClientList.setRowCount(0);
        self.ui.tableWidgetClientList.setColumnCount(2);
        self.ui.tableWidgetClientList.setHorizontalHeaderLabels(["IP", "Port"])
        self.ui.tableWidgetClientList.horizontalHeader().setSectionResizeMode( QHeaderView.Stretch )
        self.ui.tableWidgetClientList.verticalHeader().hide()
        self.client_list_count = 0
        self.ui.tableWidgetClientList.horizontalHeader().setStyleSheet(
            "QHeaderView::section{background-color:rgb(40,143,218);font:10pt;}");

    def insert_client_info(self, ip_str, port_str):
        back_up_str = ip_str + "," + port_str
        self.client_list.append( back_up_str )
        row_item = QTableWidgetItem()
        col_item = QTableWidgetItem()
        row_item.setText(ip_str)
        col_item.setText(port_str)
        self.ui.tableWidgetClientList.insertRow( self.client_list_count )
        self.ui.tableWidgetClientList.setItem( self.client_list_count, 0, row_item )
        self.ui.tableWidgetClientList.setItem( self.client_list_count, 1, col_item )
        self.client_list_count = self.client_list_count + 1

    def delete_client_info_by_ip(self, ip_str):
        item = self.ui.tableWidgetClientList.findItems("ip_str",QtCore.Qt.MatchContains)
        for i in range(self.client_list_count):
            current_ip_str = self.ui.tableWidgetClientList.item(0, i).text()
            if ip_str in current_ip_str or ip_str == current_ip_str:
                self.ui.tableWidgetClientList.removeRow( i )
                self.client_list.remove(i)
                self.client_list_count = self.client_list_count - 1
                break
            else:
                pass

    def remove_all_client_info(self):
        for i in range(self.client_list_count):
            self.ui.tableWidgetClientList.removeRow(i)
        self.client_list_count = 0
        self.client_list.clear()

    def refresh_devices_list(self):
        for i in range( self.ui.comboBoxEthList.count() ):
            self.ui.comboBoxEthList.removeItem(i)
        net_devices_list = self.scan_net_devices()
        for item in net_devices_list:
            self.ui.comboBoxEthList.addItem( item )

    def scan_net_devices(self):
        net_devices_info = []
        temp_info = psutil.net_if_addrs()
        for k, v in temp_info.items():
             net_devices_info.append( (k, v) )
        device_name = []
        device_address = []
        item_str_list = []
        k = 0
        for device in net_devices_info:
            print( device )
            device_name.append( device[0] )
            dev = device[1]
            i = 0
            for item in dev[0]:
                if i == 1:
                    if item.find(".") >= 0:
                        device_address.append(item)
                    else:
                        device_address.append("-")
                else:
                    pass
                i = i + 1
            item_str_list.append( str(device_name[k]) + "," + str(device_address[k])  )
            k = k + 1
        return item_str_list

    def pop_error_window(self, content):
        error_win = QMessageBox()
        error_win.setModal( True )
        error_win.setWindowTitle( "Error" )
        error_win.setIcon(QMessageBox.Critical)
        error_win.setText( content )
        error_win.exec()

    def pop_info_window(self, content):
        info_win = QMessageBox()
        info_win.setModal( True )
        info_win.setWindowTitle( "Info" )
        info_win.setIcon(QMessageBox.Information)
        info_win.setText( content )
        info_win.exec()

    def repeat_send(self):
        self.on_pushButtonSend_clicked()

    def set_ip_from_net_device(self):
        device_str = self.ui.comboBoxEthList.currentText()
        temp_str = device_str.split(",")
        ip_str = temp_str[1]
        self.ui.lineEditLocalIp.setText( ip_str )

    timer = threading.Timer(5, repeat_send)

    @QtCore.pyqtSlot("int", name="on_comboboxprotocal_currentindexchanged")
    def on_comboBoxProtocal_currentIndexChanged(self, int_index):
        print("ui: protocal index change to " + str( int_index ) )
        self.protocal_mode = int_index
        if int_index == self.PROTOCAL_UDP:
            self.ui.comboBoxMode.setEnabled( False )
            self.ui.lineEditLocalPort.setEnabled( False )
            self.ui.lineEditLocalIp.setEnabled( False )
        else:
            self.ui.comboBoxMode.setEnabled( True )
            self.ui.pushButtonConnect.setEnabled( True )
            self.ui.pushButtonDisconnect.setEnabled( True )

    @QtCore.pyqtSlot("int", name="on_comboboxmode_currentindexchanged")
    def on_comboBoxMode_currentIndexChanged(self, int_index):
        self.tcp_mode = int_index
        if self.tcp_mode == self.MODE_SERVER:
            self.ui.pushButtonConnect.setText("Listen")
            self.ui.lineEditLocalPort.setEnabled( True )
            self.ui.lineEditLocalIp.setEnabled( True )
        elif self.tcp_mode == self.MODE_CLIENT:

            self.ui.lineEditLocalPort.setEnabled( False )
            self.ui.lineEditLocalIp.setEnabled( False )
            self.ui.pushButtonConnect.setText("Connect")
        if self.ui.comboBoxMode.currentIndex() == self.MODE_CLIENT:
            self.ui.groupBoxClientList.setHidden(True)
            self.setMaximumSize(0,0)
        else:
            self.ui.groupBoxClientList.setHidden(False)
            self.setMaximumSize(0,0)

    @QtCore.pyqtSlot(int, name="on_comboboxethlist_currentindexchanged")
    def on_comboBoxEthList_currentIndexChanged(self):
        self.set_ip_from_net_device()

    @QtCore.pyqtSlot(name="on_pushbuttonping_click")
    def on_pushButtonPing_click(self):

        aim_ip = self.ui.lineEditAimIp.text()
        if len( aim_ip ) == 0:
            self.pop_error_window("Aim ip is Empty.")
            return
        self.ui.statusbar.showMessage("ping " + aim_ip + "| waitting...")
        ret = subprocess.call(["ping", aim_ip ,"-c", "2"])
        if ret == 0:
            self.ui.statusbar.showMessage("system: ping " + aim_ip + " network normal.", 3000)
            self.pop_info_window("system: ping " + aim_ip + " network normal." )
        else:
            self.ui.statusbar.showMessage("system: ping " + aim_ip + " network failed.", 3000)
            self.pop_error_window("system: ping " + aim_ip + " network failed.")

    @QtCore.pyqtSlot("QModelIndex", name="on_tablewidgetclientlist_clicked")
    def on_tableWidgetClientList_clicked(self, model):
        if (self.client_list_count == 0):
            return
        print( "current_row" + str(model.row()) )
        print( "current_column" + str(model.column()) )
        index = model.row()
        self.ui.lineEditAimIp.setText( self.client_list[index].split(',')[0] )
        self.ui.lineEditAimPort.setText( self.client_list[index].split(',')[1] )

    @QtCore.pyqtSlot(name="on_pushbuttonconnect_click")
    def on_pushButtonConnect_click(self):
        ui_deal_flag = False
        if self.ui.comboBoxProtocal.currentIndex() == self.PROTOCAL_TCP:
            mode = self.ui.comboBoxMode.currentIndex()
            self.tcpAgent.set_mode( mode )
            if self.ui.comboBoxMode.currentIndex() == self.MODE_CLIENT:
                if len(self.ui.lineEditAimIp.text()) == 0:
                    self.pop_error_window("Target IP is Empty!")
                    self.ui.lineEditAimIp.setFocus()
                    self.ui.lineEditAimIp.setStyleSheet("background-color: rgb(204, 0, 0);")
                    return
                if len(self.ui.lineEditAimPort.text()) == 0:
                    self.pop_error_window("Target Port is Empty!")
                    self.ui.lineEditAimPort.setFocus()
                    self.ui.lineEditAimPort.setStyleSheet("background-color: rgb(204, 0, 0);")
                    return
                self.ui.lineEditAimPort.setStyleSheet("")
                self.ui.lineEditAimIp.setStyleSheet("")
                ip_str = self.ui.lineEditAimIp.text()
                port_int = int(self.ui.lineEditAimPort.text())
                if self.tcpAgent.connect(ip_str, port_int):
                    self.pop_info_window( ip_str + "  " + str(port_int)  + " has been set up.")
                    self.ui.statusbar.showMessage( "Linked-> ip : [" + ip_str + "]" + ", port : [" + str(port_int) + "]" )
                    self.ui.statusbar.setStyleSheet("color: rgb(78, 154, 6);")
                    ui_deal_flag = True
                else:
                    pass
            elif self.ui.comboBoxMode.currentIndex() == self.MODE_SERVER:
                if len(self.ui.lineEditLocalIp.text()) == 0:
                    self.pop_error_window("Local IP is Empty!")
                    self.ui.lineEditLocalIp.setFocus()
                    self.ui.lineEditLocalIp.setStyleSheet("background-color: rgb(204, 0, 0);")
                    return
                if len(self.ui.lineEditAimPort.text()) == 0:
                    self.pop_error_window("Listen Port is Empty!")
                    self.ui.lineEditLocalPort.setFocus()
                    self.ui.lineEditLocalPort.setStyleSheet("background-color: rgb(204, 0, 0);")
                    return
                if self.ui.lineEditLocalIp.text() == "-":
                    self.pop_error_window("Network device no ip was detected!")
                    return
                self.ui.lineEditLocalPort.setStyleSheet("")
                self.ui.lineEditLocalIp.setStyleSheet("")
                local_ip = self.ui.lineEditLocalIp.text()
                local_port = self.ui.lineEditLocalPort.text()

                if self.tcpAgent.connect(local_ip, int(local_port)):
                    self.pop_info_window( "listen :" + local_ip + " , Port :" + local_port )
                    self.ui.statusbar.showMessage( "listen :" + local_ip + " , Port :" + local_port )
                    self.ui.statusbar.setStyleSheet("color: rgb(78, 154, 6);")
                    ui_deal_flag = True
            else:
                # tcpAgent error information via the msg sginal-slot mechanism
                pass
        elif self.ui.comboBoxProtocal.currentIndex() == self.PROTOCAL_UDP:
            local_ip = self.ui.lineEditLocalIp.text()
            local_port = int( self.ui.lineEditLocalPort.text() )
            print( "local_port " + self.ui.lineEditLocalPort.text())
            if self.udpAgent.bind_udp(local_ip, local_port):
                ui_deal_flag = True
                pass
            else:
                # Having msg signal pop when run into the error.
                pass
        else:
            pass
        # Deal with the ui logic when set up connection.
        if ui_deal_flag == True:
            self.ui.pushButtonConnect.setEnabled(False)
            self.ui.pushButtonDisconnect.setEnabled(True)
            self.ui.pushButtonAppIp.setEnabled(False)
            self.ui.pushButtonWriteIp.setEnabled(False)
            self.ui.comboBoxEthList.setEnabled(False)
            self.ui.comboBoxMode.setEnabled(False)
            self.ui.comboBoxProtocal.setEnabled(False)


    @QtCore.pyqtSlot(name="on_pushbuttondisconnect_click")
    def on_pushButtonDisconnect_click(self):
        ui_deal_flag = False
        if self.ui.comboBoxProtocal.currentIndex() == self.PROTOCAL_TCP:
            self.tcpAgent.tcp_disconnect()
            self.remove_all_client_info()
            self.ui.statusbar.showMessage("TCP Disconnected!")
            self.ui.statusbar.setStyleSheet("color: rgb(204, 0, 0);")
            self.tcpAgent.tcp_socket.close()
            ui_deal_flag = True
        elif self.ui.comboBoxProtocal.currentIndex() == self.PROTOCAL_UDP:
            self.udpAgent.unbind_udp()
            ui_deal_flag = True
        else:
            ui_deal_flag = False
            pass
        if ui_deal_flag == True:
            self.ui.pushButtonConnect.setEnabled(True)
            self.ui.pushButtonDisconnect.setEnabled(False)
            self.ui.pushButtonAppIp.setEnabled(True)
            self.ui.pushButtonWriteIp.setEnabled(True)
            self.ui.comboBoxEthList.setEnabled(True)
            self.ui.comboBoxMode.setEnabled(True)
            self.ui.comboBoxProtocal.setEnabled(True)

    @QtCore.pyqtSlot(name="on_radiobuttonrecascii_clicked")
    def on_radioButtonRecASCII_clicked(self):
        print("radioButtonRecASCII")
        self.recv_disp_mode = self.ASCII_FLAG

    @QtCore.pyqtSlot(name="on_radiobuttonrechex_clicked")
    def on_radioButtonRecHex_clicked(self):
        print("radioButtonRecHex")
        self.recv_disp_mode = self.HEX_FLAG

    @QtCore.pyqtSlot(name="on_radiobuttonsendascii_clicked")
    def on_radioButtonSendASCII_clicked(self):
        print("radioButtonSendASCII ")
        self.send_disp_mode = self.ASCII_FLAG

    @QtCore.pyqtSlot(name="on_radiobuttonsendhex_clicked")
    def on_radioButtonSendHex_clicked(self):
        print("radioButtonSendHex ")
        self.send_disp_mode = self.HEX_FLAG

    @QtCore.pyqtSlot("bool", name="on_checkboxwordwrap_clicked")
    def on_checkBoxWordWrap_clicked(self, checked):
        print("checkBoxWordWrap: " + str(checked))
        self.is_word_wrap = checked

    @QtCore.pyqtSlot("bool", name="on_checkboxwordwrap_clicked")
    def on_checkBoxDisplayTime_clicked(self, checked):
        print("checkBoxDisplayTime: " + str(checked))
        self.is_disp_send_time = checked

    @QtCore.pyqtSlot("bool", name="on_checkboxdisplayrectime_clicked")
    def on_checkBoxDisplayRecTime_clicked(self, checked):
        print("checkBoxDisplayRecTime : " + str(checked))
        self.is_disp_recv_time = checked

    @QtCore.pyqtSlot("bool", name="on_checkboxrepeatsend_clicked")
    def on_checkBoxRepeatSend_clicked(self, checked):
        print( "checkBoxRepeatSend : " + str(checked) )
        self.is_repeat_send_mode = checked

    @QtCore.pyqtSlot("int", name="on_spinboxtime_valuechanged")
    def on_spinBoxTime_valueChanged(self, time):
        print( "ms value change:" + str(time) )
        self.repeat_send_time_ms = time

    @QtCore.pyqtSlot(name="on_pushbuttonsend_clicked")
    def on_pushButtonSend_clicked(self):
        if len(self.ui.textEditSend.toPlainText()) == 0:
            if self.timer.isAlive():
                self.timer.cancel()
            self.pop_error_window("Send Editor is Empty!")
            self.ui.textEditSend.setFocus()
            return
        browser_text = self.ui.textEditSend.toPlainText()
        if self.protocal_mode == self.PROTOCAL_TCP:
            if self.send_disp_mode == self.ASCII_FLAG:
                send_bytes = hexConv.stringToUtf8( browser_text )
                self.tcpAgent.send_bytes( send_bytes )
            elif self.send_disp_mode == self.HEX_FLAG:
                send_bytes = hexConv.hexStringTobytes( browser_text )
                self.tcpAgent.send_bytes( send_bytes )
        elif self.protocal_mode == self.PROTOCAL_UDP:
            ip_port = [ip, port] = [self.ui.lineEditAimIp.text(), int(self.ui.lineEditAimPort.text())]
            if self.send_disp_mode == self.ASCII_FLAG:
                send_bytes = hexConv.stringToUtf8( browser_text )
                self.udpAgent.send_bytes( send_bytes, ip_port)
            elif self.send_disp_mode == self.HEX_FLAG:
                send_bytes = hexConv.hexStringTobytes( browser_text )
                self.udpAgent.send_bytes( send_bytes, ip_port )
        else:
            pass

    @QtCore.pyqtSlot(name="on_pushbuttonclear_clicked")
    def on_pushButtonClear_clicked(self):
        self.ui.textBrowserRec.clear()

    @QtCore.pyqtSlot(name="on_pushbuttonwriteip_clicked")
    def on_pushButtonWriteIp_clicked(self):
        # need root authorization.
        net_word = self.ui.comboBoxEthList.currentText()
        net_dev_name = net_word.split(",")
        if net_dev_name[0] == "lo":
            self.pop_error_window("'lo' may not modify the ip.")
            return
        print( "current select deivce :" + net_dev_name[0] )
        net_addr = self.ui.lineEditLocalIp.text()
        if platform.system() == "Linux" :
            msg = ""
            try:
                ret = subprocess.call(["pkexec","ifconfig", net_dev_name[0], net_addr])
            except Exception as ret_e:
                msg = ret_e
            else:
                pass
            if ret == 0:
                self.pop_info_window( msg + net_dev_name[0] + ": " + net_addr + " set succussful")
            else:
                self.pop_error_window( msg +  net_dev_name[0] + ": " + net_addr + " set failed" )
        elif platform.system() == "Windows":
            pass

    @QtCore.pyqtSlot(name="on_pushbuttonappip_clicked")
    def on_pushButtonAppIp_clicked(self):
        self.ui.statusbar.showMessage("system try to put in for a new ip from router dhcp server...")
        net_word = self.ui.comboBoxEthList.currentText()
        net_dev_name = net_word.split(",")
        if net_dev_name[0] == "lo":
            self.pop_error_window("'lo' may not modify the ip.")
            return
        print( "current select deivce :" + net_dev_name[0] )
        if platform.system() == "Linux" :
            msg = ""
            try:
                ret = subprocess.call(["pkexec","dhclient", net_dev_name[0]] ,timeout=3)
            except Exception as ret_e:
                msg = ret_e
            else:
                pass
            if ret == 0:
                self.ui.statusbar.showMessage("system get a new ip.", 3000)
                self.pop_info_window( msg + net_dev_name[0] + ": " + " set succuss.")
            else:
                self.ui.statusbar.showMessage("Application of ip was denied.", 3000)
                self.pop_error_window( msg + net_dev_name[0] + ": " + " set failed" )
        elif platform.system() == "Windows":
            pass

    @QtCore.pyqtSlot(str, name="sig_tcp_agent_send_msg")
    def on_tcpAgent_send_msg(self, msg):
        print("recv : sig_tcp_agent_send_msg :" + msg)
        self.pop_info_window( msg )

    @QtCore.pyqtSlot(str, name="sig_tcp_agent_send_error")
    def on_tcpAgent_send_error(self, msg):
        print("recv : sig_tcp_agent_send_error :" + msg)
        self.pop_error_window( msg )

    @QtCore.pyqtSlot("QByteArray", name="sig_tcp_agent_recv_network_msg")
    def on_tcpAgent_recv_network_msg(self, array):
        print(array)
        if self.recv_disp_mode == self.ASCII_FLAG:
            self.ui.textBrowserRec.append( str(array, encoding='utf-8') )
        else:
            int_list = numpy.array( array )
            print(int_list)
            self.ui.textBrowserRec.append( hexConv.intlistToHexString( int_list ) )

    @QtCore.pyqtSlot(str, name="sig_udp_agent_send_error")
    def on_udpAgent_send_error(self, msg):
        print("recv : sig_tcp_agent_send_error :" + msg)
        self.pop_error_window( msg )

    @QtCore.pyqtSlot(str, name="sig_udp_agent_send_error")
    def on_udpAgent_send_msg(self, msg):
        print("recv : sig_udp_agent_send_error :" + msg)
        self.pop_info_window( msg )

    @QtCore.pyqtSlot("QByteArray", name="sig_udp_agent_recv_network_msg")
    def on_udpAgent_recv_network_msg(self, array):
        print(array)
        if self.recv_disp_mode == self.ASCII_FLAG:
            self.ui.textBrowserRec.append( str(array, encoding='utf-8') )
        else:
            int_list = numpy.array( array )
            print(int_list)
            self.ui.textBrowserRec.append( hexConv.intlistToHexString( int_list ) )

    @QtCore.pyqtSlot("QByteArray", name="sig_udp_agent_recv_network_msg")
    def on_udpAgent_recv_network_msg(self, array):
        print(array)
        if self.recv_disp_mode == self.ASCII_FLAG:
            self.ui.textBrowserRec.append( str(array, encoding='utf-8') )
        else:
            int_list = numpy.array( array )
            print(int_list)
            self.ui.textBrowserRec.append( hexConv.intlistToHexString( int_list ) )

    @QtCore.pyqtSlot(int, str, name="sig_tcp_agent_client_name")
    def on_tcpAgent_client_name(self, i_o_o, name_str):

        if "," in name_str and "." in name_str:
            temp_str = name_str.split(",")
            ip_str = temp_str[0].split("'")[1]
            port_str = temp_str[1].split(")")[0]

        if i_o_o == 0:
            print( "a client info  remove :" + name_str )
            self.delete_client_info_by_ip(ip_str)
            pass
        elif i_o_o == 1:
            print("a client info join" + name_str)
            self.insert_client_info(ip_str, port_str)
            pass
        else:
            pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    # Deal with the signal and slot
    # Move the signal-slot connected functions to self.__init__() that is samely.
    # tcp slot.
    win.tcpAgent.sig_tcp_agent_send_msg.connect( win.on_tcpAgent_send_msg )
    win.tcpAgent.sig_tcp_agent_recv_network_msg.connect( win.on_tcpAgent_recv_network_msg )
    win.tcpAgent.sig_tcp_agent_client_name.connect( win.on_tcpAgent_client_name )
    win.tcpAgent.sig_tcp_agent_send_error.connect( win.on_tcpAgent_send_error )
    # udp slot.
    win.udpAgent.sig_udp_agent_recv_network_msg.connect(win.on_udpAgent_recv_network_msg)
    win.udpAgent.sig_udp_agent_send_error.connect( win.on_udpAgent_send_error )
    win.udpAgent.sig_udp_agent_send_msg.connect( win.on_udpAgent_send_msg )



    win.show()
    sys.exit(app.exec_())