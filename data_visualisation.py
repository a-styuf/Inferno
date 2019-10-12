from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import tkinter as tk
import tkinter.ttk as ttk
import my_gui
import numpy
import copy
import threading
import warnings
warnings.filterwarnings("ignore", category=UserWarning)


class DVFrame(tk.Frame):
    def __init__(self, root, **kw):
        self.root = root
        self.row_data = ""
        self.r_after_id = None
        for key in sorted(kw):
            if key == "var":
                self.client = kw.pop(key)
            else:
                pass
        tk.Frame.__init__(self, self.root, kw)
        self._redraw_ready = 1
        # создание полей под объекты GUI
        self.frame, self.f_1, self.ax, self.label_font, self.f_1_canvas = None, None, None, None, None
        self.pause_button = None
        self.data, self.legend = [["Имя 0", [1, 2, 3], "Name 0"]], None
        self.table = None
        self._show_time = 1000
        self.show_time_var, self.show_time_label, self.show_time_entry = None, None, None
        self.gui_set()

    def gui_set(self):
        # graph
        self.frame = tk.Frame(self, bg="gray10")
        self.frame.place(x=10, y=10, relwidth=1, relheight=1, width=-320, height=-50)
        self.f_1 = Figure(figsize=(6.5, 5.5), dpi=100, facecolor="#A9A9A9", frameon=True)
        ax0 = self.f_1.add_axes((0.1, 0.15, 0.65, 0.80), facecolor="#D3D3D3", frameon=True, yscale="linear")
        ax1 = ax0.twinx()
        self.ax = [ax0, ax1]
        self.label_font = {'family': 'Arial',
                           'color': 'Black',
                           'weight': 'normal',
                           'size': 12,
                           }
        self.f_1_canvas = FigureCanvasTkAgg(self.f_1, master=self.frame)
        self.f_1_canvas.get_tk_widget().pack(fill="both", expand=1)
        self.f_1_canvas.draw()
        self.resize()
        toolbar = NavigationToolbar2Tk(self.f_1_canvas, self)
        toolbar.place(x=0, rely=1, y=-35)
        toolbar.update()
        # таблица с типами данных
        self.table = my_gui.ScrollbarTable(self)
        self.table.place(relx=1, x=-310, y=10, relheight=1, height=-50, width=300)
        [self.table.cells[i][j].configure(command=self.checkbutton_redraw) for i in range(2) for j in range(self.table.rows)]
        self.table.cells[0][1].value.set("1")
        self.table.cells[1][2].value.set("1")
        # кнопки управления
        self.pause_button = tk.Button(self, text='Пауза', command=self.change_button_state)
        self.pause_button.place(relx=1, x=-250, rely=1, y=-35, height=30, width=200)

        self.show_time_var = tk.StringVar(self)
        self.show_time_var.set("1000")
        self.show_time_label = tk.Label(self, width=20, bd=2, text="Интервал отображения")
        self.show_time_label.place(relx=1, x=-520, rely=1, y=-35, height=30, width=150)
        self.show_time_entry = tk.Entry(self, width=5, bd=2, textvariable=self.show_time_var, justify="center")
        self.show_time_entry.place(relx=1, x=-370, rely=1, y=-35, height=30, width=50)

    def change_button_state(self):
        if self.pause_button["relief"] == "raised":
            self._redraw_ready = 0
            self.pause_button.configure(relief="sunken", text="Продолжить")
        else:
            self._redraw_ready = 1
            self.pause_button.configure(relief="raised", text="Пауза")
        pass

    def checkbutton_redraw(self):
        self.data_manager(self.data)
        pass

    def resize(self):
        self.frame.update_idletasks()
        dx = self.frame.winfo_width()
        dy = self.frame.winfo_height()
        if dx > 1 and dx > 1:
            try:
                frame_info = self.frame.place_info()
                dpi = self.f_1.get_dpi()
                f_1_height = (float(frame_info["relheight"]) * dy + float(frame_info["height"])) / dpi
                f_1_width = (float(frame_info["relwidth"]) * dx + float(frame_info["width"])) / dpi
                self.f_1.set_size_inches(f_1_width, f_1_height)
            except:
                pass
            self.f_1_canvas.show()
            # self.f_1_canvas.get_tk_widget().pack(fill="both", expand=1)
        pass

    def data_manager(self, data):
        """
        Функция обработки входных данных с последующей отрисовкой и заполнением таблицы
        Формат data:
        [ ["Имя_0", [data_0, data_1 ... data_N], "Name_0"],
          ["Имя_2", [data_0, data_1 ... data_N], "Name_1"],
          ...
          ["Имя_n", [data_0, data_1 ... data_N], "Name_n"]]
        #
        """
        if data:
            self.data = copy.deepcopy(data)

        if self._redraw_ready == 1:
            self.table.redraw(self.data, self.checkbutton_redraw)
            data_list = [[], []]
            data_list[0].append(self.data[0])
            data_list[1].append(self.data[0])
            [data_list[0].append(self.data[i]) for i in range(len(self.data)) if int(self.table.enable_list[i][0]) != 0]
            [data_list[1].append(self.data[i]) for i in range(len(self.data)) if int(self.table.enable_list[i][1]) != 0]
            self.graph_data(data=data_list)

    def calc_show_time(self):
        sh_t_str = self.show_time_var.get()
        try:
            sh_t = int(sh_t_str)
        except ValueError:
            sh_t = self._show_time
        if sh_t < 2:
            sh_t = 2
        elif sh_t > 24*3600:
            sh_t = 24*3600
        self._show_time = sh_t
        self.show_time_var.set(self._show_time)
        return self._show_time

    def calc_show_num(self, time_data):
        stop_num = len(time_data) - 1
        try:
            for i in range(len(time_data) - 2, 0, -1):
                if time_data[i] + self._show_time <= time_data[-1]:
                    start_num = i
                    return stop_num - start_num
                pass
        except IndexError:
            pass
        return len(time_data)

    def graph_data(self, data=None):
        """
        Функция отрисовки графиков из данных data, который состоит из двух листов
        Формат data_1 и data_2:
        [ ["Имя_0", [data_0, data_1 ... data_N], "Name_0"],
          ["Имя_2", [data_0, data_1 ... data_N], "Name_1"],
          ...
          ["Имя_n", [data_0, data_1 ... data_N], "Name_n"]]
        #
        """
        handles = []
        labels = []
        try:
            self.legend.remove()
        except (AttributeError, ValueError):
            pass
        color_num = 0
        name_list = []
        data_list = []
        label_list = []
        for j in range(2):
            name_list.append([data[j][i][0] for i in range(len(data[j]))])
            data_list.append([data[j][i][1] for i in range(len(data[j]))])
            label_list.append([data[j][i][2] for i in range(len(data[j]))])
        for j in range(2):
            try:
                x_name = name_list[j][0]
            except ValueError:
                x_name = "Время от великого потопа, кг/с^3."
            ax = self.ax[j]
            ax.cla()
            if data_list[j][1:]:  # проверка на наличие данных в целом
                for i in range(1, len(data_list[j])):
                    color_num += 1
                    # проверка на рисование графиков
                    try:
                        label = label_list[j][i]
                    except ValueError:
                        label = "{:d}".format(i)
                    self.calc_show_time()
                    data_leng = self.calc_show_num(data_list[j][0])
                    data_max = numpy.minimum(len(data_list[j][0]), len(data_list[j][i]))
                    data_min = numpy.maximum(0, data_max - data_leng)
                    ax.plot(data_list[j][0][data_min:data_max], data_list[j][i][data_min:data_max],
                            str(line_type_from_index(color_num)), label=label)
                    ax.set_xlim(data_list[j][0][data_min], data_list[j][0][data_max - 1])
                    pass
                ax_handles, ax_labels = ax.get_legend_handles_labels()
                handles.extend(ax_handles)
                labels.extend(ax_labels)
            ax.set_xlabel(x_name)
            ax.grid(which="both")
        if handles:
            self.legend = self.f_1.legend(handles=handles, labels=labels, loc=1, markerscale=0.5, fontsize="x-small",
                                          bbox_to_anchor=(0.96, 0.99))
        self.f_1_canvas.draw()
        pass


class GraphFrame(tk.Frame):
    def __init__(self, root, **kw):
        self.root = root
        tk.Frame.__init__(self, self.root, kw)
        # создание полей под объекты GUI
        self.frame, self.f_1, self.ax0, self.label_font, self.f_1_canvas = None, None, None, None, None
        self.pause_button = None
        self.data, self.legend = [["Имя 0", [1, 2, 3], "Name 0"]], None
        self.table = None
        self._show_time = 1000
        self.show_time_var, self.show_time_label, self.show_time_entry = None, None, None
        self.gui_set()
        self.x_label = "Напряжение ЗС, В"
        self.y_label = "Ток МПЗ, А"

    def gui_set(self):
        # graph
        self.frame = tk.Frame(self, bg="gray10")
        self.frame.place(x=10, y=10, relwidth=1, relheight=1, width=-20, height=-40)
        self.f_1 = Figure(figsize=(6.5, 5.5), dpi=100, facecolor="#A9A9A9", frameon=True)
        self.ax0 = self.f_1.add_axes((0.1, 0.15, 0.88, 0.83), facecolor="#D3D3D3", frameon=True, yscale="linear")
        self.label_font = {'family': 'Arial',
                           'color': 'Black',
                           'weight': 'normal',
                           'size': 12,
                           }
        self.f_1_canvas = FigureCanvasTkAgg(self.f_1, master=self.frame)
        self.f_1_canvas.get_tk_widget().pack(fill="both", expand=1)
        self.f_1_canvas.draw()
        self.resize()
        toolbar = NavigationToolbar2Tk(self.f_1_canvas, self)
        toolbar.place(x=0, rely=1, y=-35)
        toolbar.update()

    def resize(self):
        self.frame.update_idletasks()
        dx = self.frame.winfo_width()
        dy = self.frame.winfo_height()
        if dx > 1 and dx > 1:
            try:
                frame_info = self.frame.place_info()
                dpi = self.f_1.get_dpi()
                f_1_height = (float(frame_info["relheight"]) * dy + float(frame_info["height"])) / dpi
                f_1_width = (float(frame_info["relwidth"]) * dx + float(frame_info["width"])) / dpi
                self.f_1.set_size_inches(f_1_width, f_1_height)
            except:
                pass
            self.f_1_canvas.show()
            # self.f_1_canvas.get_tk_widget().pack(fill="both", expand=1)
        pass

    def plot(self, *arg, **kw):
        self.ax0.cla()
        self.ax0.plot(*arg, **kw)
        self.ax0.set_xlabel(self.x_label)
        self.ax0.set_ylabel(self.y_label)
        self.ax0.grid(which="both")
        self.f_1_canvas.draw()
        pass


def line_type_from_index(n):
    color_line = ["b", "r", "g", "c", "m", "y", "k"]
    style_line = ["-", "--", "-.", ":"]
    try:
        color = color_line[n % len(color_line)]
        style = style_line[n // len(color_line)]
        # print(n % len(color_line), n // len(color_line))
        return style + color
    except:
        return "-r"


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
class Visual_Table(tk.Frame):  # не забываем, что таблица наследуется от Фрэйма
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
