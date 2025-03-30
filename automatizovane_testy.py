import pytest

def vytvor_testovaci_databazi():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='1234'
    )
    cursor = connection.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS test_mojedatabaze")
    cursor.close()
    connection.close()

def smaz_testovaci_databazi():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='1234'
    )
    cursor = connection.cursor()
    cursor.execute("DROP DATABASE IF EXISTS test_mojedatabaze")
    cursor.close()
    connection.close()

import mysql.connector

@pytest.fixture(scope="session", autouse=True)
def priprav_testovaci_db():
    vytvor_testovaci_databazi()
    setup_test_db()
    yield
    smaz_testovaci_databazi()

from main import pridat_ukol, aktualizovat_ukol, odstranit_ukol, pripojeni_db

# Funkce co udela tabulku na testy
def setup_test_db():
    spojeni = pripojeni_db(test_db=True)
    if spojeni is None:
        print('Nepodařilo se připojit k testovací databázi')
        return
    kurzor = spojeni.cursor()
    kurzor.execute("""
        CREATE TABLE IF NOT EXISTS ukoly (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nazev VARCHAR(255) NOT NULL,
            popis TEXT NOT NULL,
            stav ENUM('Nezahajeno', 'Probíhá', 'Hotovo') NOT NULL DEFAULT 'Nezahajeno',
            datum_vytvoreni TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    spojeni.commit()
    kurzor.close()
    spojeni.close()

# Funkce pro vymazání tabulky ukoly v testovací databázi (abychom po testech neměli žádné testovací data)
def vymazat_testovaci_data():
    connection = pripojeni_db(test_db=True)
    if connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM ukoly;")
        connection.commit()
        cursor.close()
        connection.close()

# Testovací šablona
@pytest.fixture(scope="function")
def test_db():
    setup_test_db()
    yield
    vymazat_testovaci_data()

# Funkce pro přidání úkolu
def pridat_ukol(tabulka='ukoly', nazev='', popis=''):
    connection = pripojeni_db(test_db=True)
    if connection:
        cursor = connection.cursor()
        if not nazev or not popis:
            print("Název a popis úkolu jsou povinné!")
            return
        cursor.execute("INSERT INTO ukoly (nazev, popis, stav, datum_vytvoreni) VALUES (%s, %s, 'Nezahájeno', NOW())",
                       (nazev, popis))
        connection.commit()
        cursor.close()
        connection.close()

# Test pro přidání úkolu (pozitivní)
def test_pridat_ukol():
    vymazat_testovaci_data()  # Vymažeme testovací data před testem

    pridat_ukol(nazev="Testovací úkol", popis="Popis testovacího úkolu")
    connection = pripojeni_db(test_db=True)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM ukoly WHERE nazev = 'Testovací úkol'")
    ukol = cursor.fetchone()
    cursor.close()
    connection.close()

    assert ukol is not None, "Úkol nebyl přidán do databáze."
    assert ukol[1] == "Testovací úkol", "Název úkolu není správný."


# Test pro přidání úkolu (negativní)
def test_pridat_ukol_nevalidni_data():
    vymazat_testovaci_data()  # Vymažeme testovací data před testem

    # Pokusíme se přidat úkol bez názvu nebo popisu
    pridat_ukol(nazev="", popis="Popis bez názvu")
    connection = pripojeni_db(test_db=True)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM ukoly WHERE popis = 'Popis bez názvu'")
    ukol = cursor.fetchone()
    cursor.close()
    connection.close()

    assert ukol is None, "Úkol s neplatnými daty byl přidán."

# Funkce pro aktualizaci úkolu
def aktualizovat_ukol(id_ukolu, novy_stav):
    if novy_stav not in ['Nezahajeno', 'Probíhá', 'Hotovo']:
        print("Neplatný stav.")
        return 
    connection = pripojeni_db(test_db=True)
    if connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE ukoly SET stav = %s WHERE id = %s", (novy_stav, id_ukolu))
        connection.commit()
        cursor.close()
        connection.close()

    # Test pro aktualizaci úkolu (pozitivní)
def test_aktualizovat_ukol():
    vymazat_testovaci_data()
    pridat_ukol(nazev="Testovací úkol", popis="Popis testovacího úkolu")
    
    connection = pripojeni_db(test_db=True)
    if not connection:
        pytest.fail('Nepodařilo se připojit k DB')
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM ukoly WHERE nazev = 'Testovací úkol'")
    ukol_id = cursor.fetchone()[0]
    cursor.close()
    connection.close()

    aktualizovat_ukol(ukol_id, "Probíhá")

    connection = pripojeni_db(test_db=True)
    if not connection:
        pytest.fail('Nepodařilo se připojit k DB.')
    cursor = connection.cursor()
    cursor.execute("SELECT stav FROM ukoly WHERE id = %s", (ukol_id,))
    stav = cursor.fetchone()[0]
    cursor.close()
    connection.close()

    assert stav == "Probíhá", "Stav úkolu se neaktualizoval správně."

# Test pro aktualizaci úkolu (negativní)
def test_aktualizovat_ukol_nevalidni_id():
    vymazat_testovaci_data()

    aktualizovat_ukol(9999, "Hotovo")  # ID, které neexistuje
    connection = pripojeni_db(test_db=True)
    cursor = connection.cursor()
    cursor.execute("SELECT stav FROM ukoly WHERE id = 9999")
    stav = cursor.fetchone()
    cursor.close()
    connection.close()

    assert stav is None, "Stav úkolu s neexistujícím ID byl změněn."

# Test na aktualizaci ukolu - spatny stav
def test_aktualizovat_ukol_neplatny_stav(monkeypatch, test_db, capsys):
    spojeni = pripojeni_db(test_db=True)
    if not spojeni:
        pytest.fail('Nepodařilo se připojit k DB')
    kurzor = spojeni.cursor()
    kurzor.execute("INSERT INTO ukoly (nazev, popis) VALUES ('Test', 'Neplatny stav')")
    spojeni.commit()
    kurzor.execute("SELECT id FROM ukoly LIMIT 1")
    ukol_id = kurzor.fetchone()[0]
    kurzor.close()
    spojeni.close()

    vstupy = iter([str(ukol_id), "neco divneho"])
    monkeypatch.setattr('builtins.input', lambda _: next(vstupy))
    aktualizovat_ukol(ukol_id, 'neco divneho')
    vystup = capsys.readouterr()
    assert "Neplatný stav." in vystup.out

# Funkce pro odstranění úkolu
def odstranit_ukol(id_ukolu):
    connection = pripojeni_db(test_db=True)
    if connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM ukoly WHERE id = %s", (id_ukolu,))
        connection.commit()
        cursor.close()
        connection.close()

# Test pro odstranění úkolu (pozitivní)
def test_odstranit_ukol():
    vymazat_testovaci_data()
    pridat_ukol(nazev="Testovací úkol", popis="Popis testovacího úkolu")
    
    connection = pripojeni_db(test_db=True)
    if not connection:
        pytest.fail('Nepodařilo se připojit k DB')
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM ukoly WHERE nazev = 'Testovací úkol'")
    ukol_id = cursor.fetchone()[0]
    cursor.close()

    odstranit_ukol(ukol_id)

    connection = pripojeni_db(test_db=True)
    if not connection:
        pytest.fail('Nepodařilo se připojit k DB')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM ukoly WHERE id = %s", (ukol_id,))
    ukol = cursor.fetchone()
    cursor.close()
    connection.close()

    assert ukol is None, "Úkol nebyl správně odstraněn."

# Test pro odstranění úkolu (negativní)
def test_odstranit_ukol_nevalidni_id():
    vymazat_testovaci_data()
    odstranit_ukol(9999)  # Neexistující ID
    connection = pripojeni_db(test_db=True)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM ukoly WHERE id = 9999")
    ukol = cursor.fetchone()
    cursor.close()
    connection.close()

    assert ukol is None, "Úkol s neexistujícím ID byl odstraněn."

