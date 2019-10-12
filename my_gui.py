import tkinter as tk


# попробуем создать клас с скролируемой таблицей
class ScrollbarTable(tk.Canvas):
    def __init__(self, root, **kw):
        self.list = [
                    ["Имя 0", [1, 2, 3], "Name 0"],
                    ["Имя 1", [1, 2, 3], "Name 1"],
                    ["Имя 2", [2, 4, 6], "Name 2"],
                    ["Имя 3", [3, 2, 1], "Name 3"],
                    ]
        for key in sorted(kw):
            if key == "list":
                self.list = kw.pop(key)
            else:
                pass
        #  создание основных элементов интерфейса
        tk.Canvas.__init__(self, root, kw)
        self.frame = tk.Frame(self)
        self.y_scrollbar = tk.Scrollbar(self)
        # объявление дополнительных параметров
        self.frame_window = self.create_window(0, 0, anchor='nw', window=self.frame)
        self._frame_position = [0, 0, 0, 0]
        self.cells = []
        self.rows = 0
        self.columns = 0
        self.name_list = []
        self.enable_list = []
        # перереисовка объекта
        #
        self.frame.pack(side="left")
        self.y_scrollbar.pack(side="right", fill="y")
        self.configure(yscrollcommand=self.y_scrollbar.set)
        self.y_scrollbar.configure(command=self.yview)
        #
        self.frame_window = self.create_window(0, 0, anchor='nw',
                                               window=self.frame)  # создаем окно в канве для фрэйма
        #
        self.redraw(self.list, None)
        pass

    def frame_fill(self, name_list):
            self.cells = []
            self.rows = len(name_list)
            self.columns = 4
            for j in range(self.columns):
                self.cells.append([])
                for i in range(self.rows):
                    if j == 0 or j == 1:
                        self.cells[j].append(Cell(self.frame, type="checkbutton"))
                    elif j == 2:
                        self.cells[j].append(Cell(self.frame, width=20, justify="left", type="label", relief="ridge"))
                        self.cells[j][i].value.set(name_list[i])
                    elif j == 3:
                        self.cells[j].append(Cell(self.frame, width=10, justify="left", type="label", relief="ridge"))
            [self.cells[j][i].grid(row=i, column=j) for i in range(self.rows) for j in range(self.columns)]
            pass

    def redraw(self, data_list, command):
        if data_list:
            self.list = data_list
            name_list = [data_list[i][0] for i in range(len(data_list))]
            last_data_vals=[]
            for i in range(len(data_list)):
                try:
                    last_data_vals.append("%.2E" % data_list[i][1][-1])
                except IndexError:
                    last_data_vals.append("...")
            self.enable_list = [([self.cells[0][i].value.get(), self.cells[1][i].value.get()])
                                for i in range(self.rows)]
            if self.name_list == name_list:
                pass
            else:
                self.name_list = name_list
                self.clear_frame_table()
                self.frame_fill(name_list)  # заполняем таблицу для отображения шагов
                self.frame.update_idletasks()  # обновляем фрэйм, что бы получить актуальные размеры и координаты
                self._frame_position = [self.frame.winfo_x(),
                                        self.frame.winfo_y(),
                                        self.frame.winfo_x() + self.frame.winfo_reqwidth(),
                                        self.frame.winfo_y() + self.frame.winfo_reqheight()]
                self.config(scrollregion=self._frame_position)
                while 1:
                    if len(self.enable_list) < self.rows:
                        self.enable_list.append([0, 0])
                    else:
                        break
                [self.cells[j][i].configure(bg="gray95") for i in range(self.rows) for j in range(self.columns)]
                [self.cells[i][j].configure(command=command) for i in range(2) for j in range(self.rows)]
            [self.cells[3][i].value.set(last_data_vals[i]) for i in range(self.rows)]
            if self.enable_list:
                [self.cells[j][i].value.set(self.enable_list[i][j]) for i in range(self.rows) for j in range(2)]
        pass

    def color_row(self, row_num, color="gray90"):
        if self.rows != 0:
            [self.cells[columns][row_num].configure(bg=color) for columns in range(self.columns)]
        pass

    def clear_frame_table(self):
        [self.cells[j][i].destroy() for i in range(self.rows) for j in range(self.columns)]
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
            self.configure(variable=self.value, )
            self.value.set(0)
        else:
            tk.Widget.__init__(self, parent, 'entry', kw)
            self.configure(textvariable=self.value)


#  описание таблице, состоящей из клеток  и чекбоксов  #
class VisualTable(tk.Frame):  # не забываем, что таблица наследуется от Фрэйма
    def __init__(self, parent, columns=2, rows=7):  # указываем родителя + указываем количество строк и столбцов
        tk.Frame.__init__(self, parent)  # дял начала инициализируем родительский фрэйм
        self.cells = []  # теперь создаем лист под будущие ячейки таблицы. В будущем этот лист будет двумерным
        for j in range(columns):
            self.cells.append([])  # тут как раз и делаем лист для ячеек двумерным
            for i in range(rows):  # в данном цикле мы указываем тип ячейки который будет стоять по координате (j, i)
                if j == 0 or j == 1:
                    self.cells[j].append(Cell(self, type="checkbutton"))
                else:
                    self.cells[j].append(Cell(self, width=15, justify="left", type="label", relief="ridge"))
        [self.cells[j][i].grid(row=i, column=j) for i in range(rows) for j in range(columns)]