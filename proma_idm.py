import minimalmodbus
import serial
import serial.tools.list_ports
import tkinter as tk
import struct


class DataFrame(tk.LabelFrame):
    def __init__(self, root, **kw):
        self.name = "PROMA-IDM"
        self.id = "013B3AB7"
        self.br = 9600
        self.addr = 2
        self.debug = False
        self.a = 6.9513
        self.k = 0.4851
        for key in sorted(kw):
            if key == "name":
                self.name = kw.pop(key)
            elif key == "id":
                self.id = kw.pop(key)
            elif key == "addr":
                self.addr = kw.pop(key)
            elif key == "br":
                self.br = kw.pop(key)
            elif key == "debug":
                self.debug = kw.pop(key)
            elif key == "a":
                self.a = kw.pop(key)
            elif key == "k":
                self.k = kw.pop(key)
            else:
                pass
        self.root = root
        self.proma_idm = Data(proma_id=self.id, addr=self.addr, a=self.a, k=self.k)
        tk.LabelFrame.__init__(self, self.root, kw)
        self.set_cfg()
        self.set_gui()
        self.state_check()

    def connect(self):
        #
        self.proma_idm.a = self.a
        self.proma_idm.k = self.k
        #
        self.proma_idm.init_mb(br=self.br, dev_id=self.id, address=self.addr)
        self.state_check()
        try:
            print("%s: connect" % self.name, "\t", self.proma_idm.instrument.serial)
        except AttributeError:
            print("%s: connect errror" % self.name)

    def get_cfg(self):
        self.cfg_dict = {}
        self.cfg_dict["name"] = self.name
        #
        self.cfg_dict["address"] = "%d" % self.addr
        #
        self.cfg_dict["baudrate"] = "%d" % self.br
        #
        self.cfg_dict["ac-04 serial number"] = self.id
        #
        self.cfg_dict["a"] = "%f" % self.a
        #
        self.cfg_dict["k"] = "%f" % self.k
        #
        print("%s: get cfg - " % self.name, self.cfg_dict)
        return self.cfg_dict

    def set_cfg(self, cfg=None):
        if cfg:
            self.cfg_dict = cfg
            self.name = self.cfg_dict.get("name", self.name)
            self.addr = int(self.cfg_dict.get("address", self.addr))
            self.br = int(self.cfg_dict.get("baudrate", self.br))
            self.id = self.cfg_dict.get("ac-04 serial number", self.id)
            self.a = self.cfg_dict.get("a", self.a)
            self.k = self.cfg_dict.get("k", self.k)
        else:
            pass

    def set_gui(self):
        # таблица с данными
        self.table = Table(self, columns=2, rows=2)
        self.table.place(x=10, y=30)
        self.set_gui_data()
        # запрос данных
        self.get_data_button = tk.Button(self, text='Данные', command=self.get_data, bg="gray80")
        self.get_data_button.place(relx=0, x=5, y=120, height=20, relwidth=0.5, width=-10)

        self.calibr_data_button = tk.Button(self, text='Уст. калибр.', command=self.get_calibr_data, bg="gray80")
        self.calibr_data_button.place(relx=0.5, x=5, y=120, height=20, relwidth=0.5, width=-10)
        # # установка границ
        # self.set_data_button = tk.Button(self, text='Установить', command=self.set_data, bg="gray80")
        # self.set_data_button.place(relx=0.5, x=5, y=120, height=20, relwidth=0.5, width=-10)
        # калибровочная кривая
        self.state_label = tk.Label(self, text="Q[м3/ч]=a*(P[кПа]^k)", font=("Helvetica", 10), justify="center")
        self.state_label.place(relx=0.0, x=5, y=70, height=20, relwidth=1, width=-10)

        self.a_var = tk.StringVar()
        self.a_var.set(self.a)
        self.a_entry = tk.Entry(self, textvar=self.a_var, bg="white", justify="center")
        self.a_entry.place(relx=0.0, x=5, y=90, height=20, relwidth=0.5, width=-10)

        self.k_var = tk.StringVar()
        self.k_var.set(self.k)
        self.k_entry = tk.Entry(self, textvar=self.k_var, bg="white", justify="center")
        self.k_entry.place(relx=0.5, x=5, y=90, height=20, relwidth=0.5, width=-10)
        # переподключиться
        self.reconnect_button = tk.Button(self, text='Подключение', command=self.reconnect, bg="gray80")
        self.reconnect_button.place(relx=0.0, x=5, y=150, height=20, relwidth=0.5, width=-10)
        self.addr_var = tk.StringVar()
        self.addr_var.set(self.addr)
        self.addr_entry = tk.Entry(self, textvar=self.addr_var, bg="gray80", justify="center", state="disable")
        self.addr_entry.place(relx=0.5, x=5, y=150, height=20, relwidth=0.5, width=-10)
        # отображение состояния
        self.state_label = tk.Label(self, text=self.name, font=("Helvetica", 10), justify="center")
        self.state_label.place(relx=0.0, x=5, y=5, height=20, width=100)
        # отображение id AC04
        self.id_var = tk.StringVar()
        self.id_var.set(self.id)
        self.id_entry = tk.Entry(self, textvar=self.id_var, font=("Helvetica", 10), justify="center", state="disable")
        self.id_entry.place(relx=1.0, x=-95, y=5, height=20, width=90)
        pass

    def set_gui_data(self):
        self.proma_idm.create_data()
        for i in range(len(self.table.cells[0])):
            self.table.cells[0][i].value.set(self.proma_idm.data_field[0][i])
            self.table.cells[1][i].value.set(self.proma_idm.data_field[1][i])
        pass

    def get_data(self):
        self.proma_idm.get_bounds()
        self.proma_idm.read_pressure()
        self.set_gui_data()
        self.state_check()
        pass

    def get_calibr_data(self):
        a = self.a_var.get()
        k = self.k_var.get()
        try:
            self.a = float(a)
            self.k = float(k)
            self.proma_idm.a = float(a)
            self.proma_idm.k = float(k)
        except ValueError:
            pass
        finally:
            self.a_var.set(self.a)
            self.k_var.set(self.k)
        pass

    def set_data(self):
        try:
            bounds_var = [float(self.table.cells[1][i].value.get()) for i in range(1, 5)]
            # print(bounds_var)
            self.proma_idm.set_bounds(bounds_var)
        except (ValueError, IndexError) as error:
            print(error)
            pass
        finally:
            self.set_gui_data()
            self.state_check()
        pass

    def state_check(self):
        if self.proma_idm.state == 1:
            self.state_label.configure(bg="PaleGreen3")
        elif self.proma_idm.state == -1:
            self.state_label.configure(bg="coral2")
        elif self.proma_idm.state == 0:
            self.state_label.configure(bg="gray")
        else:
            self.state_label.configure(bg="gray")
        pass

    def reconnect(self):
        self.proma_idm.dev_id = [self.id_var.get()]
        self.proma_idm.init_mb()
        self.state_check()
        pass


class Data:
    def __init__(self, proma_id="013B3AB7", addr=2, a=6.9513, k=0.4851):
        self.instrument = None
        self.a = a  # коэффициенты пересчета давления в расход по формуле Cons[m3/h]=a*(P[kPa]**k)
        self.k = k
        self.mb_addr = addr  # здесь и далее: mb - ModeBus
        self.dev_port = None
        self.dev_br = None
        self.dev_id = [proma_id]
        self.state = 0  # состояние подключения к устройству
        self.min_1, self.max_1 = 0, 0  # пороги дискретки
        self.rl_min_1, self.rl_max_1 = 0, 0  # состояние дискретки
        self.consumption = 0  # расход
        self.pressure = 0  # kPa
        self.error = ""
        self.data_field = [[], [], []]
        self.init_mb()
        pass

    def init_mb(self, br=None, dev_id=None, address=None):
        if br:
            self.br = br
        if dev_id:
            self.dev_id = [dev_id]
        if address:
            self.mb_addr = address
        self.state = self._connect_serial_by_ser_num()
        return self.state

    def _connect_serial_by_ser_num(self):  # функция для установки связи с устройством по его ID
        com_list = serial.tools.list_ports.comports()
        for com in com_list:
            for serial_number in self.dev_id:
                if com.serial_number is not None:
                    if com.serial_number in serial_number:
                        if self.instrument is None:
                            self.dev_port = com.device
                            try:
                                self.instrument = minimalmodbus.Instrument(com.device, self.mb_addr, mode="rtu")
                                self.instrument.debug = self.debug
                                self.instrument.close_port_after_each_call = False
                                self.instrument.serial.baudrate = self.br
                                self.instrument.serial.timeout = 0.25
                            except serial.serialutil.SerialException:
                                return -1
                            return 1
        self.state = -1

    def read_rl_state(self):
        try:
            self.rl_min_1 = self.instrument.read_bit(0, functioncode=0x01)
            self.rl_max_1 = self.instrument.read_bit(1, functioncode=0x01)
        except (AttributeError, OSError) as error:
            self.error = error
            self.state = -1
        return self.rl_min_1, self.rl_max_1

    def write_rl_state(self):
        try:
            self.instrument.writ_bit(0, self.rl_min_1, functioncode=0x05)
            self.instrument.writ_bit(1, self.rl_max_1, functioncode=0x05)
        except (AttributeError, OSError) as error:
            self.error = error
            self.state = -1
        return 1

    def read_pressure(self):
        try:
            self.pressure = self.instrument.read_float(0, functioncode=0x04)
            self.consumption = self.a * (self.pressure ** self.k)
            self.state = 1
        except (AttributeError, OSError) as error:
            self.error = error
            self.state = -1
        return self.pressure

    def get_bounds(self):
        data = None
        try:
            data = self.instrument.read_registers(18, 8)
        except (AttributeError, OSError) as error:
            self.error = error
            self.state = -1
            return self.min_1, self.max_1
        self.min_1 = hex_to_float((data[0] << 16) + data[1])
        self.max_1 = hex_to_float((data[2] << 16) + data[3])
        return self.min_1, self.max_1

    def set_bounds(self, bounds):  # todo функция не работает, не происходит запись в регистры
        data = struct.pack("!ffff", bounds[2],
                           bounds[1],
                           bounds[3],
                           bounds[0])

        data_list = []
        for i in range(len(data)//2):
            data_list.append(((data[2*i + 0] << 8) + (data[2*i + 1] << 0)) & 0xffff)
        print(data_list)
        try:
            self.instrument.write_registers(18, data_list)
        except AttributeError as error:
            self.error = error
            self.state = -1
        self.min_1, self.max_1 = self.get_bounds()
        return self.min_1, self.max_1

    def create_data(self):
        self.data_field = [[], [], []]
        #
        try:
            self.data_field[0].append("Расход, м3/ч")  # 0
            self.data_field[0].append("Давление, кПа")  # 1
            self.data_field[0].append("Макс_1, кПа")  # 2
            self.data_field[0].append("Мин_1, кПа")  # 3
            #
            self.data_field[1].append("{:.4f}".format(self.consumption))  # 0
            self.data_field[1].append("{:.4f}".format(self.pressure))  # 1
            self.data_field[1].append("{:.2f}".format(self.max_1))  # 2
            self.data_field[1].append("{:.2f}".format(self.min_1))  # 3
            #
            self.data_field[2].append("Consumption, m3/h")  # 0
            self.data_field[2].append("Pressure, kPa")  # 1
            self.data_field[2].append("Max_1, kPa")  # 2
            self.data_field[2].append("Min_1, kPa")  # 3
        except (AttributeError, TypeError):
            self.data_field[1] = ["0" for i in range(len(self.data_field[0]))]
        pass


def hex_to_float(data):  # todo use struct
    s = (-1) ** ((data >> 31) & 0x01)
    exp = ((data & 0x7F800000) >> 23)
    man = ((data & 0x007FFFFF) | 0x800000) if exp != 0 else ((data & 0x7FFFFF) << 1)
    float_data = float(s*(man*(2**-23))*(2**(exp-127)))
    return float_data


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