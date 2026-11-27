#!/usr/bin/env python3
"""
Prelucrare firme din judetul Timis + coduri CAEN.

Pasul 1: filtreaza fisierul cu firme dupa ADR_JUDET (streaming).
Pasul 2: citeste fisierul CAEN (streaming), retine codurile firmelor din Timis.
Pasul 3: alatura codurile CAEN firmelor din Timis.
Pasul 4: pastreaza doar firmele care au cel putin un cod CAEN din lista de filtrare.
"""
import sys
import time
import unicodedata
from collections import defaultdict

# ======================= SETARI (modifica aici) =======================
# Cai absolute. Pe Windows foloseste prefixul r"..." (raw string).
FISIER_FIRME = r"C:\Users\Dan\Downloads\Firme research\04.11.2026\od_firme_04.11.2026.csv"                              # intrare: firme (4 mil. linii)
FISIER_CAEN = r"C:\Users\Dan\Downloads\Firme research\04.11.2026\od_caen_autorizat_04.11.2026.csv"                                # intrare: coduri CAEN (19 mil. linii)
FISIER_FIRME_TIMIS = r"C:\Users\Dan\Downloads\Firme research\04.11.2026\od_firme_Timis_04.11.2026.csv"                  # iesire pas 1: firme din Timis
FISIER_FIRME_TIMIS_CU_CAEN = r"C:\Users\Dan\Downloads\Firme research\04.11.2026\firme_timis_caen.csv"  # iesire pas 3: firme Timis + coduri CAEN
FISIER_FIRME_TIMIS_FILTRAT_CAEN = r"C:\Users\Dan\Downloads\Firme research\04.11.2026\firme_timis_filtrat_caen.csv"  # iesire pas 4: dupa filtrul CAEN

JUDET = "Timis"        # judetul de filtrat (diacriticele nu conteaza)
ENCODING = "utf-8"     # encoding fisiere intrare (utf-8, cp1250, latin-2 ...)
FORMAT_LONG = False    # False: toate codurile CAEN ale firmei pe un rand, separate prin ;
                       # True:  un rand per cod CAEN (firma se repeta)

# Coduri CAEN de cautat, separate prin ; (se pastreaza firmele care au cel putin unul).
# Lasa gol ("") pentru a sari peste pasul 4.
CODURI_CAEN_FILTRU = "6110;6120;6210;6220;6290;6310;6391;6392"
# ======================================================================

SEP = "^"
COL_CAEN = "COD_CAEN_AUTORIZAT"
COL_VER = "VER_CAEN_AUTORIZAT"


def normalizeaza(text: str) -> str:
    """'Timiş' / 'Timiș' / 'TIMIS' -> 'timis' (ignora diacritice si majuscule)."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.strip().casefold()


def pas1_filtrare_judet():
    t0 = time.time()
    judet_norm = normalizeaza(JUDET)
    coduri_firme = set()
    total = pastrate = 0

    with open(FISIER_FIRME, "r", encoding=ENCODING, errors="replace", newline="") as fin, \
         open(FISIER_FIRME_TIMIS, "w", encoding="utf-8", newline="") as fout:

        antet = fin.readline()
        fout.write(antet.rstrip("\r\n").lstrip("\ufeff") + "\n")
        coloane = antet.rstrip("\r\n").lstrip("\ufeff").split(SEP)
        try:
            i_judet = coloane.index("ADR_JUDET")
            i_cod = coloane.index("COD_INMATRICULARE")
        except ValueError as e:
            sys.exit(f"Coloana lipsa in antet: {e}")

        cache = {}  # valoare ADR_JUDET -> bool (putine valori distincte => rapid)
        for linie in fin:
            total += 1
            campuri = linie.rstrip("\r\n").split(SEP)
            if len(campuri) <= max(i_judet, i_cod):
                continue
            val = campuri[i_judet]
            ok = cache.get(val)
            if ok is None:
                ok = cache[val] = (normalizeaza(val) == judet_norm)
            if ok:
                fout.write(linie if linie.endswith("\n") else linie + "\n")
                coduri_firme.add(campuri[i_cod])
                pastrate += 1
            if total % 1_000_000 == 0:
                print(f"  [pas 1] {total:,} linii citite, {pastrate:,} pastrate", flush=True)

    print(f"Pas 1 gata: {pastrate:,} firme din {total:,} ({time.time()-t0:.1f}s) -> {FISIER_FIRME_TIMIS}")
    return antet.rstrip("\r\n").lstrip("\ufeff"), i_cod, coduri_firme


def pas2_citire_caen(coduri_firme):
    t0 = time.time()
    caen = defaultdict(list)  # COD_INMATRICULARE -> [(cod_caen, versiune), ...]
    total = potrivite = 0

    with open(FISIER_CAEN, "r", encoding=ENCODING, errors="replace", newline="") as f:
        antet = f.readline().rstrip("\r\n").lstrip("\ufeff").split(SEP)
        try:
            i_cod = antet.index("COD_INMATRICULARE")
            i_caen = antet.index(COL_CAEN)
            i_ver = antet.index(COL_VER)
        except ValueError as e:
            sys.exit(f"Coloana lipsa in fisierul CAEN: {e}")

        for linie in f:
            total += 1
            campuri = linie.rstrip("\r\n").split(SEP)
            cod = campuri[i_cod] if len(campuri) > i_cod else ""
            if cod in coduri_firme:
                caen[cod].append((campuri[i_caen].strip(), campuri[i_ver].strip()))
                potrivite += 1
            if total % 2_000_000 == 0:
                print(f"  [pas 2] {total:,} linii citite, {potrivite:,} potrivite", flush=True)

    print(f"Pas 2 gata: {potrivite:,} coduri CAEN pentru {len(caen):,} firme "
          f"din {total:,} linii ({time.time()-t0:.1f}s)")
    return caen


def pas3_alaturare_caen(antet, i_cod, caen):
    t0 = time.time()
    with open(FISIER_FIRME_TIMIS, "r", encoding="utf-8", newline="") as fin, \
         open(FISIER_FIRME_TIMIS_CU_CAEN, "w", encoding="utf-8", newline="") as fout:
        fin.readline()
        fout.write(antet + SEP + COL_CAEN + SEP + COL_VER + "\n")

        for linie in fin:
            linie = linie.rstrip("\r\n")
            cod = linie.split(SEP)[i_cod]
            perechi = caen.get(cod)
            if not perechi:
                fout.write(f"{linie}{SEP}{SEP}\n")
            elif FORMAT_LONG:
                for c, v in perechi:
                    fout.write(f"{linie}{SEP}{c}{SEP}{v}\n")
            else:
                coduri = ";".join(c for c, _ in perechi)
                versiuni = ";".join(v for _, v in perechi)
                fout.write(f"{linie}{SEP}{coduri}{SEP}{versiuni}\n")
    print(f"Pas 3 gata ({time.time()-t0:.1f}s) -> {FISIER_FIRME_TIMIS_CU_CAEN}")


def pas4_filtrare_caen():
    t0 = time.time()
    cautate = {c.strip() for c in CODURI_CAEN_FILTRU.split(";") if c.strip()}
    if not cautate:
        print("Pas 4 omis: CODURI_CAEN_FILTRU este gol.")
        return

    total = pastrate = 0
    with open(FISIER_FIRME_TIMIS_CU_CAEN, "r", encoding="utf-8", newline="") as fin, \
         open(FISIER_FIRME_TIMIS_FILTRAT_CAEN, "w", encoding="utf-8", newline="") as fout:
        antet = fin.readline()
        fout.write(antet)
        coloane = antet.rstrip("\r\n").split(SEP)
        i_caen = coloane.index(COL_CAEN)

        for linie in fin:
            total += 1
            campuri = linie.rstrip("\r\n").split(SEP)
            if len(campuri) <= i_caen or not campuri[i_caen]:
                continue
            coduri_firma = {c.strip() for c in campuri[i_caen].split(";")}
            if not coduri_firma.isdisjoint(cautate):   # cel putin un cod in comun
                fout.write(linie if linie.endswith("\n") else linie + "\n")
                pastrate += 1

    print(f"Pas 4 gata: {pastrate:,} linii din {total:,} contin cel putin unul dintre codurile "
          f"{sorted(cautate)} ({time.time()-t0:.1f}s) -> {FISIER_FIRME_TIMIS_FILTRAT_CAEN}")


def main():
    antet, i_cod, coduri = pas1_filtrare_judet()
    caen = pas2_citire_caen(coduri)
    pas3_alaturare_caen(antet, i_cod, caen)
    pas4_filtrare_caen()


if __name__ == "__main__":
    main()