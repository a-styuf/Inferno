
import serial
import serial.tools.list_ports
import tkinter as tk
import re
import minimalmodbus
import time


class DataFrame(tk.LabelFrame):
    def __init__(self, root, **kw):
        self.id = "00000000"  # todo
        self.addr = 1
        for key in sorted(kw):
            if key == "id":
                self.id = kw.pop(key)
            elif key == "addr":
                self.addr = kw.pop(key)
            else:
                pass
        self.root = root
        self.fr_machine = Device(addr=self.addr, id=self.id)
        self.freq_def = {"min": 0, "def": 0, "max": 50}
        tk.LabelFrame.__init__(self, self.root, kw)
        self.set_gui()
        self.state_check()

    def set_gui(self):
        # таблица с данными
        self.table = Table(self, columns=2, rows=1)
        self.table.place(x=10, y=40)
        self.set_gui_data()
        # запрос данных
        self.get_data_button = tk.Button(self, text='Прочитать частоту', command=self.get_data, bg="gray80")
        self.get_data_button.place(x=10, y=70, height=20, width=180)

        self.set_data_button = tk.Button(self, text='Установить частоту', command=self.set_data, bg="gray80")
        self.set_data_button.place(x=10, y=100, height=20, width=120)

        self.freq_var = tk.StringVar()
        self.freq_var.set(5)
        self.freq_entry = tk.Entry(self, textvar=self.freq_var, font=("Helvetica", 10), justify="center")
        self.freq_entry.place(x=140, y=100, height=20, width=45)
        # кнопка переподключения
        self.connect_button = tk.Button(self, text='Переподключение', command=self.connect, bg="gray80")
        self.connect_button.place(x=10, y=130, height=20, width=180)
        # отображение состояния
        self.state_label = tk.Label(self, text="Частотник", font=("Helvetica", 10))
        self.state_label.place(relx=0.0, x=5, y=5, height=20, width=100)
        # задание id AC04
        self.id_var = tk.StringVar()
        self.id_var.set(self.id)
        self.id_entry = tk.Entry(self, textvar=self.id_var, font=("Helvetica", 10), justify="center")
        self.id_entry.place(relx=1.0, x=-95, y=5, height=20, width=85)

    def set_gui_data(self):
        self.fr_machine.create_data()
        for i in range(len(self.table.cells[0])):
            self.table.cells[0][i].value.set(self.fr_machine.data_field[0][i])
            self.table.cells[1][i].value.set(self.fr_machine.data_field[1][i])
        pass

    def connect(self):
        self.fr_machine.init_mb()
        self.state_check()

    def state_check(self):
        if self.fr_machine.state == 1:
            self.state_label.configure(bg="PaleGreen3")
        elif self.fr_machine.state == -1:
            self.state_label.configure(bg="coral2")
        elif self.fr_machine.state == 0:
            self.state_label.configure(bg="gray")
        else:
            self.state_label.configure(bg="gray")
        pass

    def get_data(self):
        self.fr_machine.read_freq()
        self.set_gui_data()
        self.state_check()
        pass

    def set_data(self):
        #
        try:
            freq_Hz = float(self.freq_var.get())
        except ValueError:
            freq_Hz = self.freq_def["def"]
        freq_Hz = self.freq_def["min"] if freq_Hz < self.freq_def["min"] else freq_Hz
        freq_Hz = self.freq_def["max"] if freq_Hz > self.freq_def["max"] else freq_Hz
        self.freq_var.set(freq_Hz)
        #
        freq_10mHz = freq_Hz * 100
        self.fr_machine.write_freq(int(freq_10mHz))
        self.state_check()
        pass


class Device:
    def __init__(self, **kw):
        self.dev_id = ["00000000"]
        self.mb_addr = 8
        for key in sorted(kw):
            if key == "id":
                self.dev_id = [kw.pop(key)]
            elif key == "addr":
                self.mb_addr = kw.pop(key)
            else:
                pass
        self.port = None
        self.debug = False
        self.br = 19200
        self.instrument = None
        self.state = 0
        self.freq = 0
        self.data_field = [[], [], []]
        self.init_mb()

    def init_mb(self, br=19200):
        self.br = br
        self.state = self._connect_serial_by_ser_num()
        return self.state

    def _connect_serial_by_ser_num(self):  # функция для установки связи с устройством по его ID
        com_list = serial.tools.list_ports.comports()
        for com in com_list:
            for serial_number in self.dev_id:
                # print(com.serial_number)
                if com.serial_number is not None:
                    if serial_number in com.serial_number:
                        if self.instrument is None:
                            minimalmodbus.BAUDRATE = self.br
                            minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = False
                            minimalmodbus.TIMEOUT = 0.3
                            self.dev_port = com.device
                            try:
                                self.instrument = minimalmodbus.Instrument(com.device, self.mb_addr, mode="rtu")
                                # print(com)
                                self.instrument.debug = False
                            except serial.serialutil.SerialException as error:
                                # print(error)
                                return 0
                            return 1
        return 0

    def read(self, d_type="temp"):
        data = None
        if d_type == "get_freq":
            addr = 0xFD00  # todo
            param = {"functioncode": 3, "numberOfDecimals": 0, "signed": False}
        elif d_type == "get_sp_freq":
            addr = 0xFA01  # todo
            param = {"functioncode": 3, "numberOfDecimals": 0, "signed": False}
        elif d_type == "status":
            addr = 0xFD01  # todo
            param = {"functioncode": 3, "numberOfDecimals": 0, "signed": False}
        else:
            addr = 0xFD00  # todo
            param = {"functioncode": 3, "numberOfDecimals": 0, "signed": False}
        if param["functioncode"] != 1:
            if d_type == "temp_fp":
                try:
                    self._data_from_type(self.instrument.read_float(addr, **param), d_type=d_type)
                    self.state = 1
                except (ValueError, OSError, AttributeError) as error:
                    # print(error)
                    self.state = -1
            else:
                try:
                    self._data_from_type(self.instrument.read_register(addr, **param), d_type=d_type)
                    self.state = 1
                except (ValueError, OSError, AttributeError):
                    self.state = -1
        else:
            try:
                self._data_from_type(self.instrument.read_bit(addr, **param), d_type=d_type)
                self.state = 1
            except (ValueError, OSError, AttributeError):
                self.state = -1
        return data

    def read_freq(self):
        self.read(d_type="get_freq")
        # self.read(d_type="get_sp_freq")
        # self.read(d_type="status")
        # print(self.freq)
        self.create_data()
        pass

    def write(self, data, d_type="set_freq"):
        if d_type == "set_freq":
            addr = 0xFA01  # todo
            param = {"functioncode": 6, "numberOfDecimals": 0, "signed": False}
        elif d_type == "set_cw":
            addr = 0xFA00  # todo
            param = {"functioncode": 6, "numberOfDecimals": 0, "signed": False}
        else:
            addr = 0xFA01  # todo
            param = {"functioncode": 6, "numberOfDecimals": 0, "signed": False}
        if param["functioncode"] != 1:
            try:
                self.instrument.write_register(addr, data, **param)
                self.state = 1
            except (ValueError, OSError, AttributeError):
                self.state = -1
        else:
            try:
                self.instrument.write_bit(addr, data, **param)
                self.state = 1
            except (ValueError, OSError, AttributeError):
                self.state = -1
        return data

    def write_freq(self, data):
        self.write(0xC400, d_type="set_cw")  # 0xC400 - run forward, commands and setpoint from ModBus
        self.write(data, d_type="set_freq")
        # self.read(d_type="get_freq")
        pass

    def _data_from_type(self, data, d_type="get_freq"):
        if d_type == "get_freq":
            self.freq = data/100
        elif d_type == "get_sp_freq":
            self.sp_freq = data/100
        elif d_type == "status":
            self.status = data/100
        else:
            self.freq = data/100

    def create_data(self):
        self.data_field = [[], [], []]
        #
        try:
            self.data_field[0].append("Частота, Гц")  # 0
            #
            self.data_field[1].append("{:.2f}".format(self.freq))  # 0
            #
            self.data_field[2].append("Frequency, Hz")  # 0
        except (AttributeError, TypeError):
            self.data_field[1] = ["0" for i in range(len(self.data_field[0]))]
        pass


def str_to_list(send_str):  # функция, которая из последовательности шестнадцетиричных слов в строке без
    send_list = []  # идентификатора 0x делает лист шестнадцетиричных чисел
    send_str = send_str.split(' ')
    for i, ch in enumerate(send_str):
        send_str[i] = ch
        send_list.append(int(send_str[i], 16))
    return send_list


def bytes_array_to_str(bytes_array):
    bytes_string = "0x"
    for i, ch in enumerate(bytes_array):
        byte_str = (" %02X" % bytes_array[i])
        bytes_string += byte_str
    return bytes_string


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


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Тесты")
    root.geometry('750x600')
    root.resizable(False, False)
    root.config(bg="grey95")

    freq = DataFrame(root, text="Частотник", width=200, height=180)
    freq.pack()

    #  Main
    root.update()
    root.deiconify()
    root.mainloop()

