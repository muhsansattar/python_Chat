# importamo vse potrebne knjižnjice
import tkinter as tk
from tkinter import messagebox
import socket
import threading
import json

# funkcija ki poskrbi da se uporabnik pridruzi skupini
def vpisi_v_skupino():
    # iz polja za vnos vzdevka in kode skupine vzame vpisano vrednost
    vzdevek = vzdevek_vnos.get()
    koda_skupine = koda_skupine_vnos.get()

    # preverimo da sta vpisana vzdevek in veljavna koda
    if vzdevek and len(koda_skupine) == 6 and koda_skupine.isdigit():
        povezi_s_streznikom(vzdevek, koda_skupine)
    elif not vzdevek:
        # ni vzdevka - javi napako
        messagebox.showwarning("Opozorilo!", "Vpiši svoj vzdevek.")
    elif not (len(koda_skupine) == 6 or koda_skupine.isdigit()):
        # napačna koda - javi napako
        messagebox.showwarning("Opozorilo!", "Vpiši veljavno kodo skupine.")


# funkcija ki poskrbi za da uporabnik ustvari novo skupino
def ustvari_skupino():
    # iz polja za vnos vzdevka vzame vpisano vrednost
    vzdevek = vzdevek_vnos.get()

    # v primeru da je vzdevek vpisan se izvede funkcija ki uporabnika vpise in ustvari novo skupino - drugače pa javi napako
    if vzdevek:
        povezi_s_streznikom(vzdevek, "")    # za kodo skupine uporabi: "" ker v primeru "ustvarjanja" nove skupine kode ni
    else:
        messagebox.showwarning("Opozorilo!", "Vpiši svoj vzdevek.")


# funkcija ki uporabnika poveze z strežnikom in 
def povezi_s_streznikom(vzdevek, koda_skupine):
    global gui_socket
    try:
        # ustvari vtičnico za povezavo s strežnikom
        gui_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # poveži se s strežnikom na določenem naslovu in portu (nastavljeno spodaj)
        gui_socket.connect((streznik_ipnaslov, streznik_port))

        # pripravi podatke za posredovanje strežniku (vzdevek in koda_skupine) v JSONu
        json_podatki = {'vzdevek': vzdevek, 'koda_skupine': koda_skupine}
        json_string = json.dumps(json_podatki)
        # pošlji podatke na strežnik v formatu utf-8
        gui_socket.send(json_string.encode("utf-8"))

        # prejmi pozdravno sporočilo od strežnika in ga prikaže uporabniku
        dobrodoslica = gui_socket.recv(1024).decode('utf-8')
        messagebox.showinfo("Dobrodošel", dobrodoslica)

        # če koda_skupine ni podana bo streznik ustvaril skupino (kodo prememo od strežnika)
        if len(koda_skupine) == 0:
            # prejmemo kodo in jo izpišemo uporabniku
            koda_skupine = gui_socket.recv(1024).decode('utf-8')
            messagebox.showinfo("Koda skupine", f"Koda ustvarjene skupine: {koda_skupine}")

        # skrij zaslon za vpis in prikaži zaslon za klepet
        vpisi_se_zaslon.pack_forget()
        klepet_zaslon.pack(padx=20, pady=20)
        osnova.title(f"Klepet - {vzdevek}")
        vzdevek_text.config(text=f"Vpisan kot: {vzdevek}\nV skupino: {koda_skupine}")

        # Zaženi novo nit (oz thread) za nenehno prejemanje sporočil
        receive_thread = threading.Thread(target=prejmi_sporocilo)
        receive_thread.start()

    except Exception as e:
        # v primeru napake - javi uporabniku
        messagebox.showerror("Napaka", f"Neuspešna povezava s stražnikom: {e}")


# funkcija ki poskrbi za posiljanje sporocil
def poslji_sporocilo():
    global gui_socket
    # prebere in shrani vrednost sporocila
    sporocilo = sporocilo_vnos.get()

    # preveri da sporocilo obstaja, če ne javi napako
    if sporocilo:
        gui_socket.send(sporocilo.encode('utf-8'))  # poslje sporocilo strežniku
        sporocilo_vnos.delete(0, tk.END)            # izprazne polje za vnos sporočila
    else:
        messagebox.showwarning("Opozorilo!", "Najprej napiši sporočilo.")


# funkcija ki odjavi uporabnika
def odjavi():
    global gui_socket
    try:
        gui_socket.close()              # zapre povezavo z strežnikom
        sporocila_box.delete(0, 'end')  # počisti zgodovino klepeta
        klepet_zaslon.pack_forget()     # zamenja okvir/zaslon nazaj na zaslon za vpis
        vpisi_se_zaslon.pack(padx=20, pady=20)
    except Exception as e:
        # v primeru napake jo javi uporabniku
        print(f"Napaka pri odjavi: {e}")


# funkcija ki skrbi za prejemanje sporočil
def prejmi_sporocilo():
    global gui_socket
    try:
        # zanka za neskončno prejemanje sporočil
        while True:
            # sprejmi sporočilo iz vtičnice in ga dekodira iz bajtov v utf-8
            message = gui_socket.recv(1024).decode('utf-8')
            # to sporocilo vpise v prostor za sporočila
            sporocila_box.insert(tk.END, message)
    except Exception as e:
        # v primeru napake jo javi uporabniku
        print(f"Napaka pri sprejemanju sporočil: {e}")


# Konfiguracija serverja port in ip naslov
streznik_ipnaslov = '127.0.0.1'
streznik_port = 11111


# osnova za izdelavo gui-a z tkinterjem
osnova = tk.Tk()
osnova.title("Klepet")

# zaslon za vpis
vpisi_se_zaslon = tk.Frame(osnova)
vpisi_se_zaslon.pack(padx=20, pady=20)

## labela in vnosno polje za vzdevek
tk.Label(vpisi_se_zaslon, text="Vzdevek:").grid(row=0, column=0, padx=5, pady=5)
vzdevek_vnos = tk.Entry(vpisi_se_zaslon)
vzdevek_vnos.grid(row=0, column=1, padx=5, pady=5)

## labela in vnosno polje za kodo skupine
tk.Label(vpisi_se_zaslon, text="Koda skupine:").grid(row=1, column=0, padx=5, pady=5)
koda_skupine_vnos = tk.Entry(vpisi_se_zaslon)
koda_skupine_vnos.grid(row=1, column=1, padx=5, pady=5)

# Gumba za vpis v skupino oz ustvarjanje nove skupine
tk.Button(vpisi_se_zaslon, text="Vpiši me v skupino", command=vpisi_v_skupino).grid(row=2, column=0, columnspan=2, pady=10)
tk.Button(vpisi_se_zaslon, text="Vpiši me in ustvari skupino", command=ustvari_skupino).grid(row=3, column=0, columnspan=2, pady=5)

# zaslon za klepet
klepet_zaslon = tk.Frame(osnova)

# gumb za odjavo
odjavi_gumb = tk.Button(klepet_zaslon, text="Odjavi se", command=odjavi)
odjavi_gumb.grid(row=0, column=0, pady=5, sticky="nw")

# besedilo z vzdevkom in kodo skupine
vzdevek_text = tk.Label(klepet_zaslon, text="")
vzdevek_text.grid(row=0, column=1, pady=5, padx=5, sticky="nw")

# okno/seznam za prikaz sporočil
sporocila_box = tk.Listbox(klepet_zaslon, width=50, height=15)
sporocila_box.grid(row=1, column=0, padx=10, pady=10, columnspan=2)

# vnosno polje za sporočila
sporocilo_vnos = tk.Entry(klepet_zaslon, width=40)
sporocilo_vnos.grid(row=2, column=0, padx=0, pady=10, sticky="w")

# gumb za pošiljanje sporočil
poslji_gumb = tk.Button(klepet_zaslon, text="Pošlji", command=poslji_sporocilo)
poslji_gumb.grid(row=2, column=1, pady=10, sticky="e")

# skrij zaslon za klepet ob začetku programa - pokaži samo zaslon za vpis
klepet_zaslon.pack_forget()


# zaženi glavno zanko aplikacije
osnova.mainloop()
