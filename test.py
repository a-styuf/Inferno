import freq_machine_atv212
import struct
import tkinter as tk



#  саздание основного окна для tkinter
root = tk.Tk()
root.title("Тесты")
root.geometry('750x600')
root.resizable(False, False)
root.config(bg="grey95")

freq = freq_machine_atv212.DataFrame(root, text="Частотник", width=300, height=300)
freq.pack()

#  Main
root.update()
root.deiconify()
root.mainloop()
