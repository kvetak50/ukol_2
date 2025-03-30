import mysql.connector

# Funkce pro připojení k databázi
def pripojeni_db(test_db=False):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1234',
            database='test_mojedatabaze' if test_db else 'mojedatabaze'
        )
        return connection            # Pokud připojení funguje, vrátí se connection
    except mysql.connector.Error as err:      # Pokud dojde k chybě při připojování, vypíše se chybová zpráva
        print(f"Chyba při připojení k databázi: {err}")
        return None

# Funkce pro vytvoření tabulky v databázi
def vytvoreni_tabulky():
    connection = pripojeni_db()
    if connection:
        cursor = connection.cursor()
        # Tento SQL dotaz vytvoří tabulku 'ukoly' pokud ještě neexistuje
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ukoly (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nazev VARCHAR(255) NOT NULL,
                popis TEXT NOT NULL,
                stav ENUM('Nezahájeno', 'Probíhá', 'Hotovo') NOT NULL DEFAULT 'Nezahájeno',
                datum_vytvoreni TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        connection.commit()  # Tímto se uloží změny v databázi
        cursor.close()
        connection.close()  # tímto uzavírám připojení k databázi

# Funkce pro přidání nového úkolu do databáze
def pridat_ukol():
    connection = pripojeni_db()
    if connection:
        nazev = input("Zadejte název úkolu: ").strip()
        popis = input("Zadejte popis úkolu: ").strip()
        if not nazev or not popis:
            print("Název a popis úkolu jsou povinné!")
            return
        cursor = connection.cursor()
        # Vložíme úkol do databáze
        cursor.execute("INSERT INTO ukoly (nazev, popis, stav, datum_vytvoreni) VALUES (%s, %s, 'Nezahájeno', NOW())", 
            (nazev, popis))
        connection.commit()        # Uložíme změny
        print("Úkol byl přidán do databáze.")
        cursor.close()
        connection.close()

# Funkce pro zobrazení všech úkolů z databáze
def zobrazit_ukoly():
    connection = pripojeni_db()
    if connection:
        cursor = connection.cursor()
        # Dotaz na všechny úkoly, které mají stav 'Nezahájeno' nebo 'Probíhá'
        cursor.execute("SELECT id, nazev, popis, stav FROM ukoly WHERE stav IN ('Nezahájeno', 'Probíhá')")
        ukoly = cursor.fetchall()  # fetchall = Získáme všechny úkoly
        
        if not ukoly:
            print("Seznam úkolů je prázdný.\n")
        else:
            print("Seznam úkolů:")
            for x, (id_ukolu, nazev, popis, stav) in enumerate(ukoly, start=1):
                print(f"{x}. {nazev.capitalize()} - {popis} (Stav: {stav})")
            print()
        cursor.close()
        connection.close()

# Funkce pro aktualizaci stavu úkolu
def aktualizovat_ukol():
    connection = pripojeni_db()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id, nazev, stav FROM ukoly")
        ukoly = cursor.fetchall()

        if not ukoly:
            print("Seznam úkolů je prázdný. Aktualizace není možná.\n")
            connection.close()      # Zavřu připojení k databázi, protože nebudu pokračovat dál
            return                  # Ukončím funkci, aby se nezobrazovalo zadání ID úkolu

        print("Seznam úkolů k aktualizaci")
        for ukol in ukoly:
            print(f"ID: {ukol[0]}, Název: {ukol[1]}, Stav: {ukol[2]}")

        try:
            vybrane_id = int(input("Zadejte ID úkolu pro aktualizaci: "))
            novy_stav = input("Zadejte nový stav (Probíhá/Hotovo): ").strip()
            if novy_stav not in ['Probíhá', 'Hotovo']:
                print("Neplatný stav.")
                return
            
            cursor.execute("UPDATE ukoly SET stav = %s WHERE id = %s", (novy_stav, vybrane_id))
            if cursor.rowcount == 0:    # Pokud úkol neexistuje
                print("Úkol s tímto ID neexistuje.")
            else:
                connection.commit()     # commit = uložení změn
                print("Stav úkolu byl aktualizován.")
        except ValueError:
            print("Neplatné ID.")

        cursor.close()
        connection.close()

# Funkce pro odstranění úkolu
def odstranit_ukol():
    connection = pripojeni_db()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id, nazev FROM ukoly WHERE stav != 'Hotovo'")
        ukoly = cursor.fetchall()
        
        if not ukoly:
            print("Není žádný úkol k odstranění.")
            connection.close()
            return

        print("Úkoly k odstranění:")
        for index, ukol in enumerate(ukoly, start=1):
            print(f"{index}. {ukol[1]} (ID: {ukol[0]})")
        
        while True:
            try:
                cislo = int(input("Zadejte číslo úkolu, který chcete odstranit: "))
                if 1 <= cislo <= len(ukoly):
                    vybrane_id = ukoly[cislo - 1][0]
                    cursor.execute("DELETE FROM ukoly WHERE id = %s", (vybrane_id,))
                    if cursor.rowcount == 0:
                        print("Úkol s tímto ID neexistuje.")
                    else:
                        connection.commit()
                        print(f"Úkol '{ukoly[cislo - 1][1]}' byl odstraněn.\n")
                    return
                else:
                    print("Neplatné číslo úkolu.\n")
            except ValueError:
                print("Neplatný vstup. Zadejte prosím číslo.\n")

            cursor.close()
            connection.close()

def hlavni_menu():
    while True:
        print("Správce úkolů - Hlavní menu")
        print("1. Přidat nový úkol")
        print("2. Zobrazit všechny úkoly")
        print("3. Odstranit úkol")
        print("4. Aktualizovat úkol")
        print("5. Konec programu")
        
        volba = input("Vyberte možnost (1-5): ")
        print()
        
        if volba == "1":
            pridat_ukol()
        elif volba == "2":
            zobrazit_ukoly()
        elif volba == "3":
            odstranit_ukol()
        elif volba == "4":
            aktualizovat_ukol()
        elif volba == "5":
            print("Ukončování programu...")
            break
        else:
            print("Neplatná volba, zkuste to znovu.\n")

if __name__ == "__main__":
    vytvoreni_tabulky()
    hlavni_menu()

# přepnutí do venv = .\venv\Scripts\Activate
# spuštění = python main.py
