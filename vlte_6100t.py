import tkinter as tk
from pywinusb import hid
import time
import numpy as np
import threading


class DataFrame(tk.LabelFrame):
    def __init__(self, root, **kw):
        self.id = "013B3AB7"
        self.addr = 2
        self.vid = 0x1111
        self.pid = 0x0004
        self.root = root
        self.state = 0
        tk.LabelFrame.__init__(self, self.root, kw)
        self.device = None
        # data
        self.data_field = [[], [], []]
        self.mass = 0
        self.mass_list = []
        self.time_list = []
        self.consumption_lpf = 10
        self.consumption = 0
        #
        self.set_gui()
        self.get_mass()

    def set_gui(self):
        # таблица с данными
        self.table = Table(self, columns=2, rows=2)
        self.table.place(x=10, y=30)
        self.set_gui_data()
        # отображение состояния
        self.state_label = tk.Label(self, text="ВЛТЭ-6100", font=("Helvetica", 10), justify="center")
        self.state_label.place(relx=0.0, x=5, y=5, height=20, width=100)
        # переподключиться
        self.reconnect_button = tk.Button(self, text='Масса', command=self.get_mass, bg="gray80")
        self.reconnect_button.place(relx=0.0, x=5, y=80, height=20, relwidth=0.5, width=-10)
        pass

    def get_mass(self):
        try:
            self.device = hid.HidDeviceFilter(vendor_id=0x1111, product_id=0x0004).get_devices()[0]
            self.state = 1
        except IndexError:
            self.device = None
            self.state = -1
        if self.device:
            self.device.open()
            self.device.set_raw_data_handler(self.parc_data)
            # out_reports = device.find_output_reports()
            # print(out_reports)
            # out_report = out_reports[0]
            usb_buffer = [0x00, 0x43, 0x4D, 0x44, 0x3E, 0x06, 0x00, 0x80,
                          0x01, 0x20, 0x00, 0x52, 0x44, 0xC0, 0x8D, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00,
                          ]
            try:
                self.device.send_output_report(usb_buffer)
            except hid.helpers.HIDError:
                self.state = -1
            self.after(100, self.disconnect)
            self.state_check()
        pass

    def disconnect(self):
        self.calc_consumption()
        self.set_gui_data()
        self.device.close()
        self.state_check()
        pass

    def parc_data(self, usb_data):
        if self.device.is_plugged():
            self.mass = ((usb_data[30] << 8) + (usb_data[29] << 0))  # почему то не в граммах, а в десятых грамма
            self.mass /= 10*1000
            self.state = 1
        else:
            self.state = -1
        pass

    def set_gui_data(self):
        self.create_data()
        for i in range(len(self.table.cells[0])):
            self.table.cells[0][i].value.set(self.data_field[0][i])
            self.table.cells[1][i].value.set(self.data_field[1][i])
        pass

    def calc_consumption(self):
        self.mass_list.append(self.mass)
        self.time_list.append(time.clock()/3600)
        if len(self.mass_list) > 1:
            while len(self.mass_list) > self.consumption_lpf:
                self.mass_list.pop(0)
            while len(self.time_list) > self.consumption_lpf:
                self.time_list.pop(0)
            consumption_list = []
            for i in range(len(self.mass_list)-1):
                consumption = - (self.mass_list[i+1] - self.mass_list[i])/(self.time_list[i+1] - self.time_list[i])
                consumption_list.append(consumption)
                pass
            self.consumption = np.mean(consumption_list)
        else:
            self.consumption = 0
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

    def create_data(self):
        self.data_field = [[], [], []]
        #
        try:
            self.data_field[0].append("Масса, кГ")  # 0
            self.data_field[0].append("Расход, кГ/ч")  # 1
            #
            self.data_field[1].append("{:.4f}".format(self.mass))  # 0
            self.data_field[1].append("{:.4f}".format(self.consumption))  # 1
            #
            self.data_field[2].append("Mass, ?")  # 0
            self.data_field[2].append("Consumption, kg/h")  # 1
        except (AttributeError, TypeError):
            self.data_field[1] = ["0" for i in range(len(self.data_field[0]))]
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


def parc_data(data):
    massa = ((data[30] << 8) + (data[29] << 0))  # почему то не в граммах, а в десятых грамма
    massa /= 10
    print(massa)
    return massa


if __name__ == "__main__":
    vid = 0x1111
    pid = 0x0004

    device = hid.HidDeviceFilter(vendor_id=0x1111, product_id=0x0004).get_devices()[0]

    device.open()
    device.set_raw_data_handler(parc_data)

    out_reports = device.find_output_reports()
    print(out_reports)
    out_report = out_reports[0]

    buffer = [0x00, 0x43, 0x4D, 0x44, 0x3E, 0x06, 0x00, 0x80,
              0x01, 0x20, 0x00, 0x52, 0x44, 0xC0, 0x8D, 0x00,
              0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
              0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
              0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
              0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
              0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
              0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
              0x00,
              ]
    device.send_output_report(buffer)
    while 1:
        device.send_output_report(buffer)
        time.sleep(0.01)
    device.close()




