# importamo vse potrebne knjižnjice
import socket
import threading
import random
import json


# slovar za shranjevanje povezanih odjemalcev in njihovih vzdevkov
uporabniki = {}

# slovar za shranjevanje klepetalnic in njihovih kod
kode_skupin = {}


# funkcija ki obravnava vsakega odjemalca posebej
def obravnavaj_odjemalca(vticnica_odjemalca):
    try:
        # prejmi vzdevek od odjemalca
        received_data = vticnica_odjemalca.recv(1024).decode('utf-8')

        # pretvori JSON nazaj v slovar
        received_json_data = json.loads(received_data)

        # vrednosti iz slovarja shrani v spremenljivke
        vzdevek = received_json_data['vzdevek']
        koda_skupine = received_json_data['koda_skupine']
        
        # pošlje dobrodošlico odjemalcu
        vticnica_odjemalca.send(f"Dobrodošel v skupino, {vzdevek}!\n".encode('utf-8'))

        # v primeru da koda ni podana pomeni da uporabnik ustvarja novo skupino
        if len(koda_skupine) == 0:
            # ustvari kodo za vsako skupino (naključna šestmestna številka)
            koda_skupine = str(random.randint(100000, 999999))
            kode_skupin[koda_skupine] = []
            uporabniki[vticnica_odjemalca] = {'vzdevek': vzdevek, 'koda_skupine': koda_skupine}
            # pošlje to kodo skupine odjemalcu
            vticnica_odjemalca.send(koda_skupine.encode("utf-8"))
        else:
            # preveri da ta koda obstaja
            if koda_skupine in kode_skupin:
                # koda obstaja, uporabnika doda v slovar vseh uporabnikov
                uporabniki[vticnica_odjemalca] = {'vzdevek': vzdevek, 'koda_skupine': koda_skupine}
            else:
                # če ne to uporabniku javi
                vticnica_odjemalca.send("Napačna koda skupine.\n".encode('utf-8'))
                return

        # obvesti vse odjemalce v skupini o novem članu
        # za vsakega odjemalca v slovarju 'uporabniki' preverimo če je v skupini v katero se bo uporabnik (ta 'odjemalec') pridružil,
        # ter da sporocila ne pošlje samemu sebi (odjemalec != vticnica_odjemalca)
        for odjemalec, info in uporabniki.items():
            if info['koda_skupine'] == koda_skupine and odjemalec != vticnica_odjemalca:
                odjemalec.send(f"{vzdevek} se je pridružil.\n".encode('utf-8'))

        # glavna zanka za klepet - se izvaja dokler odjemalec (upoprabnik) ne zapusti skupine
        while True:
            sporocilo = vticnica_odjemalca.recv(1024).decode('utf-8')
            # nobeno sporocilo ni bilo prejeto - zaključi zanko
            if not sporocilo:
                break

            # obvesti vse odjemalce v skupini o odhodu člana
            # vsem uporabnikum v slovarju 'uporabniki' pošljemo to obvestilo
            for odjemalec, info in uporabniki.items():
                if info['koda_skupine'] == koda_skupine:
                    odjemalec.send(f"{vzdevek}: {sporocilo}\n".encode('utf-8'))

    except Exception as e:
        # v primeru kakeršne koli napake to javi uporabniku
        print(f"Napaka: {e}")

    finally:
        # odstrani odjemalca iz slovarja ko je povezava prekinjena
        if vticnica_odjemalca in uporabniki:
            vzdevek = uporabniki[vticnica_odjemalca]['vzdevek']
            koda_skupine = uporabniki[vticnica_odjemalca]['koda_skupine']
            del uporabniki[vticnica_odjemalca]

            # obvesti druge odjemalce v skupini o prekinitvi povezave (izpisu člana)
            for odjemalec, info in uporabniki.items():
                if info['koda_skupine'] == koda_skupine:
                    odjemalec.send(f"{vzdevek} je odšel.\n".encode('utf-8'))
            
            # prekine povezavo z odjemalcem (uporabikom) ker je "odšel"
            vticnica_odjemalca.close()


def main():
    # Konfiguracija serverja port in ip naslov
    streznik_ipnaslov = '127.0.0.1'
    streznik_port = 11111

    # ustvari vtičnico za strežnik
    streznik_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    streznik_socket.bind((streznik_ipnaslov, streznik_port))
    streznik_socket.listen(5)

    print(f"Streznik zagnan na: {streznik_socket}")

    try:
        while True:
            # prejeta povezava z odjemalcem/uporabnikom
            vticnica_odjemalca, addr = streznik_socket.accept()
            print(f"Sprejel povezavo z: {addr}")
            
            # zaženi novo nit za obravnavo odjemalca/uporabnika
            odjemalec_thread = threading.Thread(target=obravnavaj_odjemalca, args=(vticnica_odjemalca,))
            odjemalec_thread.start()

    except KeyboardInterrupt:
        # ob prekinitvi (Ctrl+C) zapri strežnik
        streznik_socket.close()
        print("Streznik ugasnjen.")


# poženemo strežnik
main()
