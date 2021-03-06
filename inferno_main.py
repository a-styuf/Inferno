import proma_idm
import trm138
import graph_window as gw
import tkinter as tk
import time
import pvm_3m
import air_analyser
import os
import freq_machine_atv212
import copy
import configparser
import mv110


debug = False
version = "v1.3.3"


cycle_after_id = 0
graph_data_initial = [
    ["Время, c", [], "Time, s"],  # 0
    ["ПР-ИДМ1 расх.,м3/ч", [], "PR-IDM1 cons.,m3/h"],  # 1
    ["ПР-ИДМ2 расх.,м3/ч", [], "PR-IDM2 cons.,m3/h"],  # 2
    ["Масса, кг", [], "mass, kg"],  # 3
    ["Расх., кг/ч", [], "cons, kg/h"],  # 4
    ["Частота 1, Гц", [], "Freq 1, Hz"],  # 5
    ["Частота 2, Гц", [], "Freq 2, Hz"],  # 6
    ["ТМР-138 к1, °С", [], "TMR-138 ch1, °С"],  # 7
    ["ТМР-138 к2, °С", [], "TMR-138 ch2, °С"],  # 8
    ["ТМР-138 к3, °С", [], "TMR-138 ch3, °С"],  # 9
    ["ТМР-138 к4, °С", [], "TMR-138 ch4, °С"],  # 10
    ["ТМР-138 к5, °С", [], "TMR-138 ch5, °С"],  # 11
    ["ТМР-138 к6, °С", [], "TMR-138 ch6, °С"],  # 12
    ["ТМР-138 к7, °С", [], "TMR-138 ch7, °С"],  # 13
    ["ТМР-138 к8, °С", [], "TMR-138 ch8, °С"],  # 14
    ["МВ-110 к1, °С", [], "MV-110 ch1, °С"],  # 15
    ["МВ-110 к2, °С", [], "MV-110 ch2, °С"],  # 16
    ["МВ-110 к3, °С", [], "MV-110 ch3, °С"],  # 17
    ["МВ-110 к4, °С", [], "MV-110 ch4, °С"],  # 18
    ["МВ-110 к5, °С", [], "MV-110 ch5, °С"],  # 19
    ["МВ-110 к6, °С", [], "MV-110 ch6, °С"],  # 20
    ["МВ-110 к7, °С", [], "MV-110 ch7, °С"],  # 21
    ["МВ-110 к8, °С", [], "MV-110 ch8, °С"],  # 22
]
graph_data = copy.deepcopy(graph_data_initial)
air_graph_data = [
    ["Время, c", [], "Time, s"],  # 0
    ["O2, %", [], "O2, %"],  # 1
    ["CO, %", [], "CO, %"],  # 2
    ["H2, %", [], "H2, %"],  # 3
    ["CO2, %", [], "CO2, %"],  # 4
    ["NO, ppm", [], "NO, ppm"],  # 5
    ["SO2, ppm", [], "SO2, ppm"],  # 6
]
log_file = None
config = None

# функции
def cycle_start():
    global cycle_after_id, log_file, graph_data, air_graph_data
    if cycle_after_id == 0:
        cycle_start_button.configure(bg="gray80", text="Стоп", relief="sunken")
        log_file = create_log_file(dir_name="Inferno_Log_Files", name="Inferno_log")
        log_file_title = ""
        for i in range(len(graph_data)):
            log_file_title += graph_data[i][0] + ";"
        for i in range(1, len(air_graph_data)):
            log_file_title += air_graph_data[i][0] + ";"
        log_file.write(log_file_title + "\n")
        cycle_after_id = root.after(1000, cycle_body)
    else:
        cycle_start_button.configure(bg="gray80", text="Запуск цикл", relief="raised")
        root.after_cancel(cycle_after_id)
        cycle_after_id = 0
        graph_data = copy.deepcopy(graph_data_initial)
        air_graph_data = [
            ["Время, c", [], "Time, s"],  # 0
            ["O2, %", [], "O2, %"],  # 1
            ["CO, %", [], "CO, %"],  # 2
            ["H2, %", [], "H2, %"],  # 3
            ["CO2, %", [], "CO2, %"],  # 4
            ["NO, ppm", [], "NO, ppm"],  # 5
            ["SO2, ppm", [], "SO2, ppm"],  # 6
        ]
        log_file.close()
    pass


def cycle_body():
    global cycle_after_id, graph_data
    # # # сбор данных # # #
    # Прома 1
    proma1_frame.get_data()
    # Прома 2
    proma2_frame.get_data()
    # ТМР 138
    tmr138_frame.get_data()
    # MV110
    mv110_frame.get_data()
    # ВЛТЭ-6100 запрос массы
    pvm_frame.get_mass()
    # запрос газоанализатора
    air_analyser_frame.get_data()
    # частотник 1
    freq_machine_atv212_075.get_data()
    # частотник 2
    freq_machine_atv212_U55.get_data()
    # частотник 3
    freq_machine_atv212_HD18.get_data()
    # формирование данных для графика
    main_graph_root.place_data(form_graph_data())
    air_analyser_graph_root.place_data(form_air_graph_data())
    root.update_idletasks()
    # пишем в лог
    log_file_str = ""
    for i in range(len(graph_data)):
        log_file_str += "%.3f" % graph_data[i][1][-1] + ";"
    for i in range(1, len(air_graph_data)):
        log_file_str += "%.3f" % air_graph_data[i][1][-1] + ";"
    log_file.write((log_file_str + "\n").replace(".", ","))
    cycle_after_id = root.after(100, cycle_body)
    pass


def form_graph_data():
    global graph_data
    graph_data[0][1].append(round(time.perf_counter(), 3))  # давление первой помы
    graph_data[1][1].append(proma1_frame.proma_idm.consumption)  # давление первой помы
    graph_data[2][1].append(proma2_frame.proma_idm.consumption)  # давление второй помы
    graph_data[3][1].append(pvm_frame.mass)  # давление второй помы
    graph_data[4][1].append(pvm_frame.consumption)  # давление второй помы
    graph_data[5][1].append(freq_machine_atv212_075.fr_machine.freq)  # частота первого частотника
    graph_data[6][1].append(freq_machine_atv212_U55.fr_machine.freq)  # частота второго частотника
    graph_data[6][1].append(freq_machine_atv212_HD18.fr_machine.freq)  # частота второго частотника
    [graph_data[i + 7][1].append(tmr138_frame.trm138.temp[i]) for i in range(8)]  # 8 каналов ТМР-138
    [graph_data[i + 15][1].append(mv110_frame.mv110.temp[i]) for i in range(8)]  # 8 каналов MV-110
    return graph_data


def form_air_graph_data():
    global air_graph_data
    air_graph_data[0][1].append(round(time.perf_counter(), 3))  # давление первой помы
    air_graph_data[1][1].append(air_analyser_frame.o2_prc)
    air_graph_data[2][1].append(air_analyser_frame.co_prc)
    air_graph_data[3][1].append(air_analyser_frame.h2_prc)
    air_graph_data[4][1].append(air_analyser_frame.co2_prc)
    air_graph_data[5][1].append(air_analyser_frame.no_ppm)
    air_graph_data[6][1].append(air_analyser_frame.so2_ppm)
    return air_graph_data


def main_graph_win_open():
    main_graph_root.deiconify()
    pass


def air_graph_win_open():
    air_analyser_graph_root.deiconify()
    pass


def create_log_file(dir_name="tmp", name="tmp"):
    try:
        os.makedirs(dir_name)
    except OSError as error:
        print(error)
        pass
    finally:
        pass
    full_name = dir_name + "\\" + name + "_" + time.strftime("%Y_%m_%d %H-%M-%S", time.localtime())
    log_file = open(full_name + ".csv", 'a')
    return log_file


def load_init_cfg():
    cfg = configparser.ConfigParser()
    file_name = "init.cfg"
    cfg.read(file_name)
    if cfg.sections():
        print(cfg.sections())
        return cfg
    else:
        print("Config error")
        return None


def save_init_cfg(devs=None):
    cfg = configparser.ConfigParser()
    if devices:
        for dev in devs:
            print(dev.name, dev.get_cfg())
            cfg[dev.name] = dev.get_cfg()
        pass
    file_name = "init.cfg"
    try:
        with open(file_name, 'w') as configfile:
            cfg.write(configfile)
    except FileNotFoundError:
        pass
    return cfg


# саздание основного окна для tkinter
root = tk.Tk()
root.title("Inferno %s" % version)
root.geometry('850x550')
root.resizable(False, False)
root.config(bg="grey95")

# окно с графиками
main_graph_root = gw.GraphWindow(root)

# окно с графиками
air_analyser_graph_root = gw.GraphWindow(root, title="Газоанализатор")

# заготовка под хранение переферии
devices = []

# окно расходомера 1
proma1_frame = proma_idm.DataFrame(root, text="Расходомер",
                                   name="PROMA-IDM 1",
                                   id="013B3AB7", addr=2, br=9600,
                                   a=6.9513, k=0.4851,
                                   debug=debug,
                                   width=200, height=200
                                   )
proma1_frame.place(x=10, y=5)
devices.append(proma1_frame)

# окно расходомера 2
proma2_frame = proma_idm.DataFrame(root, text="Расходомер",
                                   name="PROMA-IDM 2",
                                   id="013B3C31", addr=3, br=9600,
                                   a=27.812, k=0.4855,
                                   debug=debug,
                                   width=200, height=200
                                   )
proma2_frame.place(x=10, y=210)
devices.append(proma2_frame)

# окно пвм-3м
pvm_frame = pvm_3m.DataFrame(root, text="Расходомер",
                             name="PVM-3M",
                             vid="1A86", pid="7523", br=4800,
                             filter_points=10,
                             debug=debug,
                             width=200, height=125)
pvm_frame.place(x=10, y=415)
devices.append(pvm_frame)

# окно тмр138
tmr138_frame = trm138.DataFrame(root, text="Измеритель температуры",
                                name="TMR138",
                                id="013B3BBA", addr=8, br=9600,
                                debug=debug,
                                width=200, height=250)
tmr138_frame.place(x=220, y=10)
devices.append(tmr138_frame)

# окно МВ110
mv110_frame = mv110.DataFrame(root, text="Измеритель температуры",
                              name="MB110",
                              id="01688B11", addr=16, br=115200,
                              debug=debug,
                              width=200, height=250)
mv110_frame.place(x=220, y=290)
devices.append(mv110_frame)

# окно анализатора
air_analyser_frame = air_analyser.DataFrame(root, text="Газоанализатор",
                                            name="Air analyzer",
                                            id="00A2C0E6",
                                            addr=1, br=9600,
                                            debug=debug,
                                            width=200, height=250)
air_analyser_frame.place(x=640, y=10)
devices.append(air_analyser_frame)

# частотник 1 - Schnider 0.75kW
freq_machine_atv212_075 = freq_machine_atv212.DataFrame(root, text="Преобразователь частоты",
                                                        name="ATV212-H075",
                                                        id="013B3BC1",
                                                        addr=1, br=9600,
                                                        debug=debug,
                                                        width=200, height=180)
freq_machine_atv212_075.place(x=430, y=10)
devices.append(freq_machine_atv212_075)

# частотник 2 - Schnider 5.5kW
freq_machine_atv212_U55 = freq_machine_atv212.DataFrame(root, text="Преобразователь частоты",
                                                        name="ATV212-HU55",
                                                        id="013B3C47",
                                                        addr=1, br=9600,
                                                        debug=debug,
                                                        width=200, height=180)
freq_machine_atv212_U55.place(x=430, y=190)
devices.append(freq_machine_atv212_U55)

# частотник 2 - Schnider 18kW
freq_machine_atv212_HD18 = freq_machine_atv212.DataFrame(root, text="Преобразователь частоты",
                                                         name="ATV212-HD18",
                                                         id="00A2C251",
                                                         addr=1, br=9600,
                                                         debug=debug,
                                                         width=200, height=180)
freq_machine_atv212_HD18.place(x=430, y=370)
devices.append(freq_machine_atv212_HD18)

# загрузка параметров в модули и последующее их подключение
inferno_config = load_init_cfg()
if inferno_config is None:
    inferno_config = save_init_cfg(devices)
for dev in devices:
    try:
        dev.set_cfg(inferno_config[dev.name])
        print("Inferno: to %s set cfg: " % dev.name, str(inferno_config[dev.name]))
        print(' '.join(["%s: <%s> " % (str(var), str(inferno_config[dev.name][var])) for var in inferno_config[dev.name]]))
        dev.connect()
    except Exception as error:
        print(error)

# кнопки
cycle_start_button = tk.Button(root, text='Запуск цикла', command=cycle_start, bg="gray80")
cycle_start_button.place(x=-210, relx=1, rely=1, y=-120, height=25, width=200)

save_cfg_button = tk.Button(root, text='Сохранение настроек', command=lambda: save_init_cfg(devices), bg="gray80")
save_cfg_button.place(x=-210, relx=1, rely=1, y=-150, height=25, width=200)

state_label = tk.Label(root, text="Графики", font=("Helvetica", 10))
state_label.place(x=-210, relx=1, rely=1, y=-90, height=25, width=200)

graph_win_button = tk.Button(root, text='Основные', command=main_graph_win_open, bg="gray80")
graph_win_button.place(x=-210, relx=1, rely=1, y=-60, height=25, width=95)

graph_win_button = tk.Button(root, text='Газоанализатор', command=air_graph_win_open, bg="gray80")
graph_win_button.place(x=-105, relx=1, rely=1, y=-60, height=25, width=95)

#  Main
root.update()
root.deiconify()
root.mainloop()

# закрытие файла
try:
    log_file.close()
    root.after_cancel(cycle_after_id)
except:
    pass
