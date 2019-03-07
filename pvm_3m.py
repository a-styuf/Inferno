import tkinter as tk
import time
import numpy as np
import serial
import serial.tools.list_ports


class DataFrame(tk.LabelFrame):
    def __init__(self, root, **kw):
        self.root = root
        tk.LabelFrame.__init__(self, self.root, kw)
        self.serial_numbers = []  # это лист возможных серийников!!! (не строка)
        self.vid_numbers = ["1A86"]
        self.pid_numbers = ["7523"]
        self.baudrate = 4800
        self.timeout = 0.2
        self.port = "COM0"
        self.serial = serial.Serial()
        self.state = 0
        self.error_string = "Ок"
        self.addr = 0x00
        # data
        self.data_field = [[], [], []]
        self.mass = 0
        self.mass_list = []
        self.time_list = []
        self.consumption_lpf = 10
        self.consumption = 0
        #
        self.set_gui()
        self.open_id()

    def open_id(self):
        com_list = serial.tools.list_ports.comports()
        # print(com_list)
        for com in com_list:
            # print(com.vid)
            for vid_number in self.vid_numbers:
                # print(vid_number)
                if com.vid is not None:
                    if com.vid == int(vid_number, 16) >= 0:
                        #
                        # print(com.vid, vid_number)
                        self.serial.port = com.device
                        self.serial.parity = serial.PARITY_EVEN
                        self.serial.stopbits = serial.STOPBITS_TWO
                        self.serial.timeout = self.timeout
                        self.serial.baudrate = self.baudrate
                        try:
                            self.serial.open()
                        except serial.serialutil.SerialException as error:
                            self.error_string = str(error)
                            # print(self.error_string)
                        self.state = 1
                        self.state_check()
                        return True
        self.state = -0
        self.state_check()
        return False
        pass

    def set_gui(self):
        # таблица с данными
        self.table = Table(self, columns=2, rows=2)
        self.table.place(x=10, y=30)
        self.set_gui_data()
        # отображение состояния
        self.state_label = tk.Label(self, text="ПВМ-3М/150", font=("Helvetica", 10), justify="center")
        self.state_label.place(relx=0.0, x=5, y=5, height=20, width=100)
        # переподключиться
        self.connect_button = tk.Button(self, text='Подключение', command=self.open_id, bg="gray80")
        self.connect_button.place(relx=0.5, x=5, y=80, height=20, relwidth=0.5, width=-10)
        #
        self.mass_button = tk.Button(self, text='Масса', command=self.get_mass, bg="gray80")
        self.mass_button.place(relx=0.0, x=5, y=80, height=20, relwidth=0.5, width=-10)
        pass

    def disconnect(self):
        self.serial.close()
        pass

    def get_mass(self):
        # формирование пакета для чтения данных массы
        data_to_write = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02,
                         0x09, 0x09, 0x09, 0x09, 0x09, 0x09]
        # запрос данных
        data_read = b""
        if self.serial.is_open:
            try:
                self.serial.reset_input_buffer()
                self.serial.write(data_to_write)
                # print(">> %.3f" % time.clock(), bytes_array_to_str(data_to_write))
                data_read = self.serial.read(24)
                # print(self.serial.in_waiting)
                # print("<< %.3f" % time.clock(), bytes_array_to_str(data_read))
                self.state = 1
            except serial.serialutil.SerialException as error:
                # print(error)
                self.state = -1
        else:
            self.state = -1
        #
        try:
            if data_read:
                self.mass = data_read[5] * 100 + data_read[4] * 10 + data_read[3] * 1 + \
                            data_read[2] * 0.1 + data_read[1] * 0.01 + data_read[1] * 0.001
            self.calc_consumption()
            self.set_gui_data()
        except IndexError as error:
            print(error)
        # print(bytes_array_to_str(data_read), self.mass, self.calc_consumption)
        self.state_check()
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

    def set_gui_data(self):
        self.create_data()
        for i in range(len(self.table.cells[0])):
            self.table.cells[0][i].value.set(self.data_field[0][i])
            self.table.cells[1][i].value.set(self.data_field[1][i])
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


def get_time():
    return time.strftime("%H-%M-%S", time.localtime()) + "." + ("%.3f: " % time.clock()).split(".")[1]


def str_to_list(send_str):  # функция, которая из последовательности шестнадцетиричных слов в строке без
    send_list = []  # идентификатора 0x делает лист шестнадцетиричных чисел
    send_str = send_str.split(' ')
    for i, ch in enumerate(send_str):
        send_str[i] = ch
        send_list.append(int(send_str[i], 16))
    return send_list


def bytes_array_to_str(bytes_array):
    bytes_string = ""
    for i, ch in enumerate(bytes_array):
        byte_str = (" %02X" % bytes_array[i])
        bytes_string += byte_str
    return bytes_string


if __name__ == "__main__":

    # саздание основного окна для tkinter
    root = tk.Tk()
    root.title("Inferno - Дожигатель дожигаемого.")
    root.geometry('210x135')
    root.resizable(False, False)
    root.config(bg="grey95")

    pvm_frame = DataFrame(root, text="Измеритель массы/Расходомер", width=200, height=125)
    pvm_frame.place(x=5, y=5)

    root.mainloop()
    pass



