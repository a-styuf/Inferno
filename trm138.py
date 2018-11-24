
import serial
import serial.tools.list_ports
import tkinter as tk
import re
import minimalmodbus
import time


class DataFrame(tk.LabelFrame):
    def __init__(self, root, **kw):
        self.id = "013B3BBA"
        self.addr = 8
        for key in sorted(kw):
            if key == "id":
                self.id = kw.pop(key)
            elif key == "addr":
                self.addr = kw.pop(key)
            else:
                pass
        self.root = root
        self.tmr138 = Device(addr=self.addr, id=self.id)
        tk.LabelFrame.__init__(self, self.root, kw)
        self.set_gui()
        self.state_check()

    def set_gui(self):
        # таблица с данными
        self.table = Table(self, columns=2, rows=8)
        self.table.place(x=10, y=30)
        self.set_gui_data()
        # запрос данных
        self.get_data_button = tk.Button(self, text='Получить данные', command=self.get_data, bg="gray80")
        self.get_data_button.place(x=10, y=200, height=20, width=150)
        # кнопка переподключения
        self.get_data_button = tk.Button(self, text='Переподключение', command=self.get_data, bg="gray80")
        self.get_data_button.place(x=10, y=230, height=20, width=150)
        # отображение состояния
        self.state_label = tk.Label(self, text="ТМР138", font=("Helvetica", 10))
        self.state_label.place(relx=0.0, x=5, y=5, height=20, width=100)
        # задание id AC04
        self.id_var = tk.StringVar()
        self.id_var.set(self.id)
        self.id_entry = tk.Entry(self, textvar=self.id_var, font=("Helvetica", 10), justify="center")
        self.id_entry.place(relx=1.0, x=-95, y=5, height=20, width=90)

    def set_gui_data(self):
        self.tmr138.create_data()
        for i in range(len(self.table.cells[0])):
            self.table.cells[0][i].value.set(self.tmr138.data_field[0][i])
            self.table.cells[1][i].value.set(self.tmr138.data_field[1][i])
        pass

    def state_check(self):
        if self.tmr138.state == 1:
            self.state_label.configure(bg="PaleGreen3")
        elif self.tmr138.state == -1:
            self.state_label.configure(bg="coral2")
        elif self.tmr138.state == 0:
            self.state_label.configure(bg="gray")
        else:
            self.state_label.configure(bg="gray")
        pass

    def get_data(self):
        self.tmr138.read_all_temp()
        self.set_gui_data()
        self.state_check()
        pass


class Channel:
    def __init__(self, dev, in_num=1, out_num=5):
        self.in_num = in_num
        self.out_num = out_num
        self.device = dev
        self.temp = 0
        self.error = 0
        self.set_point = 25
        self.hyst = 1
        self.out_state = 0

    def read(self, d_type="temp"):
        data = None
        if d_type == "temp":
            addr = 0x0001+(self.in_num-1)*5
            param = {"functioncode": 4, "numberOfDecimals": 1, "signed": True}
        elif d_type == "error":
            addr = 0x0002 + (self.in_num - 1) * 5
            param = {"functioncode": 4, "numberOfDecimals": 0, "signed": True}
        elif d_type == "set_point":
            addr = 0x0011 + (self.in_num - 1) * 4
            param = {"functioncode": 3, "numberOfDecimals": 0, "signed": True}
        elif d_type == "hyst":
            addr = 0x0031 + (self.in_num - 1) * 4
            param = {"functioncode": 3, "numberOfDecimals": 0, "signed": True}
        elif d_type == "out_state":
            addr = 0x0000 + (self.out_num - 1) * 1
            param = {"functioncode": 1}
        else:
            addr = 0x0001 + (self.in_num - 1) * 5
            param = {"functioncode": 4, "numberOfDecimals": 1, "signed": True}
        if param["functioncode"] != 1:
            try:
                self._data_from_type(self.device.instr.read_register(addr, **param), d_type=d_type)
                self.device.state = 1
            except (ValueError, OSError, AttributeError):
                self.device.state = -1
        else:
            try:
                self._data_from_type(self.device.instr.read_bit(addr, **param), d_type=d_type)
                self.device.state = 1
            except (ValueError, OSError, AttributeError):
                self.device.state = -1
        return data

    def write(self, data, d_type="set_point"):
        if d_type == "set_point":
            addr = 0x0011 + (self.in_num - 1) * 4
            param = {"functioncode": 6, "numberOfDecimals": 0, "signed": True}
        elif d_type == "op_set_point":
            addr = 0x0013 + (self.in_num - 1) * 4
            param = {"functioncode": 6, "numberOfDecimals": 0, "signed": True}
        elif d_type == "hyst":
            addr = 0x0031 + (self.in_num - 1) * 4
            param = {"functioncode": 6, "numberOfDecimals": 0, "signed": True}
        elif d_type == "out_state":
            addr = 0x0000 + (self.out_num - 1) * 1
            param = {"functioncode": 5}
        else:
            addr = 0x0011 + (self.in_num - 1) * 4
            param = {"functioncode": 6, "numberOfDecimals": 1, "signed": True}
        if param["functioncode"] != 1:
            try:
                self.device.instr.write_register(addr, data, **param)
                self.device.state = 1
            except (ValueError, OSError):
                self.device.state = -1
        else:
            try:
                self.device.instr.write_bit(addr, data, **param)
                self.device.state = 1
            except (ValueError, OSError):
                self.device.state = -1
        return data

    def _data_from_type(self, data, d_type="temp"):
        if d_type == "temp":
            self.temp = data
        elif d_type == "error":
            self.error = data
        elif d_type == "set_point":
            self.set_point = data
        elif d_type == "hyst":
            self.hyst = data
        elif d_type == "out_state":
            self.out_state = data
        else:
            self.temp = data

    def __str__(self):
        tmr_ch_str = "{:.2f};\t{:d};\t{:.2f};\t{:.2f};\t{:d};\n"\
            .format(self.temp, self.error, self.set_point, self.hyst, self.out_state)
        return tmr_ch_str


class Device:
    def __init__(self, **kw):
        self.dev_id = ["013B3AB7"]
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
        self.br = 9600
        self.instrument = None
        self.row_temp = [0 for i in range(8)]
        self.num_of_dec = [0 for i in range(8)]
        self.temp = [0 for i in range(8)]
        self.error = [0 for i in range(8)]
        self.set_point = [0 for i in range(8)]
        self.hyst = [0 for i in range(8)]
        self.out_state = [0 for i in range(8)]
        # self.reconnection()
        self.state = 0
        self.chan = {i: Channel(self, in_num=i, out_num=i) for i in range(1, 9)}
        self.init_mb()

    def init_mb(self, br=9600):
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
                            minimalmodbus.TIMEOUT = 0.25
                            self.dev_port = com.device
                            try:
                                self.instrument = minimalmodbus.Instrument(com.device, self.mb_addr, mode="rtu")
                                self.instrument.debug = False
                            except serial.serialutil.SerialException:
                                return -1
                            return 1
        self.state = -1

    def chan_conf(self, num=1,  in_num=1, out_num=1):
        self.chan[num].in_num = in_num
        self.chan[num].out_num = out_num

    def read(self, d_type="temp", ch=1):
        data = None
        if d_type == "temp":
            addr = 0x0001+(ch-1)*5
            param = {"functioncode": 4, "numberOfDecimals": 0, "signed": True}
        elif d_type == "temp_fp":
            addr = 0x0003+(ch-1)*5
            param = {"functioncode": 4, "numberOfRegisters": 2}
        elif d_type == "numberOfDecimal":
            addr = 0x0000 + (ch - 1) * 5
            param = {"functioncode": 4, "numberOfDecimals": 0, "signed": True}
        elif d_type == "error":
            addr = 0x0002 + (ch - 1) * 5
            param = {"functioncode": 4, "numberOfDecimals": 0, "signed": True}
        elif d_type == "set_point":
            addr = 0x0011 + (ch - 1) * 4
            param = {"functioncode": 3, "numberOfDecimals": 0, "signed": True}
        elif d_type == "hyst":
            addr = 0x0031 + (ch - 1) * 4
            param = {"functioncode": 3, "numberOfDecimals": 0, "signed": True}
        elif d_type == "out_state":
            addr = 0x0000 + (ch - 1) * 1
            param = {"functioncode": 1}
        else:
            addr = 0x0001 + (ch - 1) * 5
            param = {"functioncode": 4, "numberOfDecimals": 1, "signed": True}
        if param["functioncode"] != 1:
            if d_type == "temp_fp":
                try:
                    self._data_from_type(self.instrument.read_float(addr, **param), d_type=d_type, ch=ch)
                    self.state = 1
                except (ValueError, OSError, AttributeError) as error:
                    # print(error)
                    self.state = -1
            else:
                try:
                    self._data_from_type(self.instrument.read_register(addr, **param), d_type=d_type, ch=ch)
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

    def read_temp(self, ch=1):
        self.read(d_type="numberOfDecimal", ch=ch)

        self.read(d_type="temp", ch=ch)
        # print(ch, self.num_of_dec[ch - 1], self.row_temp[ch - 1])
        self.temp[ch-1] = self.row_temp[ch-1]/(10**self.num_of_dec[ch-1])
        pass

    def write(self, data, d_type="set_point", ch=1):
        if d_type == "set_point":
            addr = 0x0011 + (ch - 1) * 4
            param = {"functioncode": 6, "numberOfDecimals": 0, "signed": True}
        elif d_type == "op_set_point":
            addr = 0x0013 + (ch - 1) * 4
            param = {"functioncode": 6, "numberOfDecimals": 0, "signed": True}
        elif d_type == "numberOfDecimal":
            addr = 0x0010 + (ch - 1) * 4
            param = {"functioncode": 6, "numberOfDecimals": 0, "signed": True}
        elif d_type == "hyst":
            addr = 0x0031 + (ch - 1) * 4
            param = {"functioncode": 6, "numberOfDecimals": 0, "signed": True}
        elif d_type == "out_state":
            addr = 0x0000 + (ch - 1) * 1
            param = {"functioncode": 5}
        else:
            addr = 0x0011 + (ch - 1) * 4
            param = {"functioncode": 6, "numberOfDecimals": 1, "signed": True}
        if param["functioncode"] != 1:
            try:
                self.instrument.write_register(addr, data, **param)
                self.state = 1
            except (ValueError, OSError):
                self.state = -1
        else:
            try:
                self.instrument.write_bit(addr, data, **param)
                self.state = 1
            except (ValueError, OSError):
                self.state = -1
        return data

    def _data_from_type(self, data, d_type="temp", ch=1):
        if d_type == "temp":
            self.row_temp[ch-1] = data
        elif d_type == "numberOfDecimal":
            self.num_of_dec[ch-1] = data
        elif d_type == "temp_fp":
            self.temp[ch-1] = data
        elif d_type == "error":
            self.error[ch-1] = data
        elif d_type == "set_point":
            self.set_point[ch-1] = data
        elif d_type == "hyst":
            self.hyst[ch-1] = data
        elif d_type == "out_state":
            self.out_state[ch-1] = data
        else:
            self.temp[ch-1] = data

    def read_all_temp(self):
        for i in range(1, 9):
            # self.write(0, d_type="numberOfDecimal", ch=i)
            # self.read_temp(ch=i)
            self.read(d_type="temp_fp", ch=i)
            time.sleep(0.05)
        pass
        self.create_data()

    def create_data(self):
        self.data_field = [[], [], []]
        #
        try:
            self.data_field[0].append("Канал 1, °С")  # 0
            self.data_field[0].append("Канал 2, °С")  # 1
            self.data_field[0].append("Канал 3, °С")  # 2
            self.data_field[0].append("Канал 4, °С")  # 3
            self.data_field[0].append("Канал 5, °С")  # 4
            self.data_field[0].append("Канал 6, °С")  # 5
            self.data_field[0].append("Канал 7, °С")  # 6
            self.data_field[0].append("Канал 8, °С")  # 7
            #
            self.data_field[1].append("{:.2f}".format(self.temp[0]))  # 0
            self.data_field[1].append("{:.2f}".format(self.temp[1]))  # 1
            self.data_field[1].append("{:.2f}".format(self.temp[2]))  # 2
            self.data_field[1].append("{:.2f}".format(self.temp[3]))  # 3
            self.data_field[1].append("{:.2f}".format(self.temp[4]))  # 4
            self.data_field[1].append("{:.2f}".format(self.temp[5]))  # 5
            self.data_field[1].append("{:.2f}".format(self.temp[6]))  # 6
            self.data_field[1].append("{:.2f}".format(self.temp[7]))  # 7
            #
            self.data_field[2].append("Channel 1, °С")  # 0
            self.data_field[2].append("Channel 2, °С")  # 1
            self.data_field[2].append("Channel 3, °С")  # 2
            self.data_field[2].append("Channel 4, °С")  # 3
            self.data_field[2].append("Channel 5, °С")  # 4
            self.data_field[2].append("Channel 6, °С")  # 5
            self.data_field[2].append("Channel 7, °С")  # 6
            self.data_field[2].append("Channel 8, °С")  # 7
        except (AttributeError, TypeError):
            self.data_field[1] = ["0" for i in range(len(self.data_field[0]))]
        pass

    def __str__(self):
        tmr_ch_str = "{:.2f};\t{:d};\t{:.2f};\t{:.2f};\t{:d};\n"\
            .format(self.temp, self.error, self.set_point, self.hyst, self.out_state)
        return tmr_ch_str


# заготовка под OVEN
def symb_for_tetrad(self, tetrad=0x00):
    return chr((tetrad & 0x0f) + 0x47)


def hash_calc(name="test."):
    symb_dig_pattern = re.compile(r"[0-9]")
    symb_lett_pattern = re.compile(r"[A-Za-z]")
    symb_spec0_pattern = re.compile(r"[-]")
    symb_spec1_pattern = re.compile(r"[_]")
    symb_spec2_pattern = re.compile(r"[/]")
    symb_spec3_pattern = re.compile(r"[ ]")
    symb_dot_pattern = re.compile(r"[.]")
    symb_code_list = []
    for symb in name:
        if re.findall(symb_dig_pattern, symb):
            symb_code = ord(symb) - ord("0")
        elif re.findall(symb_lett_pattern, symb):
            symb_code = ord(symb) - ord("A") + 10
        elif re.findall(symb_spec0_pattern, symb):
            symb_code = ord(symb) - 26
        elif re.findall(symb_spec1_pattern, symb):
            symb_code = ord(symb) - 27
        elif re.findall(symb_spec2_pattern, symb):
            symb_code = ord(symb) - 28
        elif re.findall(symb_spec3_pattern, symb):
            symb_code = ord(symb) - 29
        else:
            if re.findall(symb_dot_pattern, symb):
                symb_code_list[-1] += 1
                break
            else:
                break
        symb_code_list.append(symb_code * 2)
    hash = 0
    for symb_code in symb_code_list:
        hash = crc_16_oven(symb_code << 1, 7, hash)
    return hash & 0xFFFF
    pass


def symbs_for_byte(byte=0x00):
    symbs = (ord(symb_for_tetrad((byte >> 4) & 0x0f))) << 8 + (ord(symb_for_tetrad((byte >> 0) & 0x0f))) << 0
    return symbs


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


def crc_16_oven(byte, num_bit, CRC):
    for i in range(num_bit):
        byte <<= 1
        if (byte ^ (CRC>>8)) & 0x08:
            CRC <<= 1
            CRC ^= 0x8F57
        else:
            CRC <<= 1
    return CRC


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