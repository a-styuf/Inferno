import minimalmodbus
import serial
import serial.tools.list_ports
import tkinter as tk
import numpy as np
import struct
import time


class DataFrame(tk.LabelFrame):
    def __init__(self, root, **kw):
        self.id = "00A2C0E6"
        self.dev_br = 9600
        self.addr = 1
        self.dev_port = None
        self.instrument = None
        self.timeout = 0.2
        self.error = "No error"
        self.state = 0
        for key in sorted(kw):
            if key == "id":
                self.id = kw.pop(key)
            elif key == "addr":
                self.addr = kw.pop(key)
            else:
                pass
        self.root = root
        self.o2_prc, self.co_prc, self.h2_prc, self.co2_prc, self.no_ppm, self.so2_ppm = 0, 0, 0, 0, 0, 0
        self.data_field = [[], [], []]
        tk.LabelFrame.__init__(self, self.root, kw)
        self.set_gui()
        self.reconnect()
        self.state_check()

    def set_gui(self):
        # таблица с данными
        self.table = Table(self, columns=2, rows=6)
        self.table.place(x=10, y=30)
        self.set_gui_data()
        # запрос данных
        self.get_data_button = tk.Button(self, text='Получить', command=self.get_data, bg="gray80")
        self.get_data_button.place(relx=0, x=5, y=170, height=20, relwidth=0.5, width=-10)
        # переподключиться
        self.reconnect_button = tk.Button(self, text='Подключить', command=self.reconnect, bg="gray80")
        self.reconnect_button.place(relx=0.0, x=5, y=200, height=20, relwidth=0.5, width=-10)
        self.addr_var = tk.StringVar()
        self.addr_var.set(self.addr)
        self.addr_entry = tk.Entry(self, textvar=self.addr_var, bg="gray80", justify="center")
        self.addr_entry.place(relx=0.5, x=5, y=200, height=20, relwidth=0.5, width=-10)
        # отображение состояния
        self.state_label = tk.Label(self, text="ГАЗОНО-ЛИЗАТОР", font=("Helvetica", 9), justify="center")
        self.state_label.place(relx=0.0, x=5, y=5, height=20, width=115)
        # задание id AC04
        self.id_var = tk.StringVar()
        self.id_var.set(self.id)
        self.id_entry = tk.Entry(self, textvar=self.id_var, font=("Helvetica", 10), justify="center")
        self.id_entry.place(relx=1.0, x=-75, y=5, height=20, width=70)
        pass

    def init_mb(self, br=9600):
        self.dev_br = br
        self.state = self.connect_serial_by_ser_num()
        return self.state

    def connect_serial_by_ser_num(self):  # функция для установки связи с устройством по его ID
        com_list = serial.tools.list_ports.comports()
        for com in com_list:
            for serial_number in self.id:
                if com.serial_number is not None:
                    if com.serial_number in serial_number:
                        if self.instrument is None:
                            minimalmodbus.BAUDRATE = self.dev_br
                            minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = False
                            minimalmodbus.TIMEOUT = self.timeout
                            self.dev_port = com.device
                            try:
                                self.instrument = minimalmodbus.Instrument(self.dev_port, self.addr, mode="rtu")
                                self.instrument.debug = False
                                return 1
                            except serial.serialutil.SerialException:
                                return -1

    def set_gui_data(self):
        self.create_data()
        for i in range(len(self.table.cells[0])):
            self.table.cells[0][i].value.set(self.data_field[0][i])
            self.table.cells[1][i].value.set(self.data_field[1][i])
        pass

    def read_data(self):
        air_list = []
        try:
            air_list = self.instrument.read_registers(0, 24)
            print(air_list)
            if len(air_list) == 24:
                self.o2_prc = reg_to_float(air_list[2:4])
                self.co_prc = reg_to_float(air_list[6:8])
                self.h2_prc = reg_to_float(air_list[10:12])
                self.co2_prc = reg_to_float(air_list[14:16])
                self.no_ppm = reg_to_float(air_list[18:20])
                self.so2_ppm = reg_to_float(air_list[22:24])
            else:
                self.state = -1
        except (OSError, ValueError, AttributeError) as error:
            print(error)
            self.state = -1
        except ValueError as error:
            print(error)
            try:
                self.instrument = minimalmodbus.Instrument(self.dev_port, self.addr, mode="rtu")
            except:
                self.state = -1
        pass

    def create_data(self):
        self.data_field = [[], [], []]
        #
        try:
            self.data_field[0].append("O2, %")  # 0
            self.data_field[0].append("CO, %")  # 1
            self.data_field[0].append("H2, %")  # 27
            self.data_field[0].append("CO2, %")  # 3
            self.data_field[0].append("NO, ppm")  # 4
            self.data_field[0].append("SO2, ppm")  # 5
            #
            self.data_field[1].append("{:.3f}".format(self.o2_prc))  # 0
            self.data_field[1].append("{:.3f}".format(self.co_prc))  # 0
            self.data_field[1].append("{:.3f}".format(self.h2_prc))  # 0
            self.data_field[1].append("{:.3f}".format(self.co2_prc))  # 0
            self.data_field[1].append("{:.3f}".format(self.no_ppm))  # 0
            self.data_field[1].append("{:.3f}".format(self.so2_ppm))  # 0
            #
            self.data_field[2].append("O2, %")  # 0
            self.data_field[2].append("CO, %")  # 1
            self.data_field[2].append("H2, %")  # 2
            self.data_field[2].append("CO2, %")  # 3
            self.data_field[2].append("NO, ppm")  # 4
            self.data_field[2].append("SO2, ppm")  # 5
        except (AttributeError, TypeError):
            self.data_field[1] = ["0" for i in range(len(self.data_field[0]))]
        pass

    def get_data(self):
        self.read_data()
        self.set_gui_data()
        self.state_check()
        pass

    def state_check(self):
        if self.state == 1:
            self.state_label.configure(bg="PaleGreen3")
        elif self.state == -1:
            self.state_label.configure(bg="coral2")
        elif self.state == 0:
            self.state_label.configure(bg="gray")
        else:
            self.state_label.configure(bg="gray")
        pass

    def reconnect(self):
        self.id = [self.id_var.get()]
        self.addr = int(self.addr_var.get())
        self.init_mb()
        self.state_check()
        pass


# описание отдельной клетки будущей таблицы #
class Cell(tk.Widget):
    def __init__(self, parent, type="entry", **kw):
        self.value = tk.StringVar()
        if type == "entry":
            tk.Widget.__init__(self, parent, 'entry', kw)
            self.configure(textvariable=self.value)
        elif type == "label":
            tk.Widget.__init__(self, parent, 'label', kw)
            self.configure(textvariable=self.value)
        elif type == "checkbutton":
            tk.Widget.__init__(self, parent, 'checkbutton', kw)
            self.configure(variable=self.value,)
            self.value.set(0)
        else:
            tk.Widget.__init__(self, parent, 'entry', kw)
            self.configure(textvariable=self.value)


#  описание таблице, состоящей из клеток  и чекбоксов
class Table(tk.Frame): # не забываем, что таблица наследуется от Фрэйма
    def __init__(self, parent, columns = 2, rows = 7): # указываем родителя + указываем количество строк и столбцов
        tk.Frame.__init__(self, parent) # дял начала инициализируем родительский фрэйм
        self.cells = []  # теперь создаем лист под будущие ячейки таблицы. В будущем этот лист будет двумерным
        for j in range(columns):
            self.cells.append([])  # тут как раз и делаем лист для ячеек двумерным
            for i in range(rows):  # в данном цикле мы указываем тип ячейки который будет стоять по координате (j, i)
                if j == 0:
                    self.cells[j].append(Cell(self, width=18, justify="left", type="Label", bg="gray90"))
                else:
                    self.cells[j].append(Cell(self, width=10, justify="center", type="Label", bg="gray90"))
        [self.cells[j][i].grid(row=i, column=j) for i in range(rows) for j in range(columns)]


def reg_to_float(data_list):
    data_int = ((data_list[1] << 16) & 0xFFFF0000) + (data_list[0] & 0xFFFF)
    sign = (data_int >> 31) & 0x1
    exp = ((data_int >> 23) & 0xFF) - 127
    man = 1 + ((data_int & 0x7FFFFF) / 0x7FFFFF)
    # print("sign = {:d}, exp = {:d}, man = {:.3E}, val = {:.6E}".format(sign, exp, man, (1**(sign-1))*man*(2**exp)))
    data_float = (1**(sign-1))*man*(2**exp)
    return data_float
