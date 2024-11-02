from datetime import date
from html import escape

from babel.dates import format_date

import tools


class Position:
    """
    Beschreibt eine Position in einer Aktivenabrechnung.
    """
    
    # Dunder methods
    def __init__(self,name:str = "",unitcount:int = 1,
                 unitprice=0.0,value=0.0):
        """
        Initialisiert ein Objekt der Klasse Position.
        
        Argumente:
        name: Name der Position
        count: Anzahl der Einheiten
        unitprice: Preis pro Einheit (nur, wenn Anzahl relevant ist)
        value: Einnahmen oder (wenn negativ) Ausgaben
        """
        self.setname(name)
        self.setunitcount(unitcount)
        self.setunitprice(unitprice)
        self.setvalue(value)
    
    def __str__(self):
        return tools.euro(self.getvalue())
    
    def __repr__(self):
        return (f"Position(name='{self.getname()}',"
               +f"unitcount={self.getunitcount()},"
               +f"unitprice={self.getunitprice()},"
               +f"value={self.getvalue()})")
    
    def __bool__(self):
        return bool(self._name != ""
                    or self._unitprice != 0.0
                    or self._value != 0.0)
    
    # Methods for output
    def htmlcells(self,indent:int = 0) -> str:
        """
        Gibt fünf Zellen im HTML-Format aus.
        Jede Zelle hat eine eigene Zeile, außer indent ist negativ.
        Die Reihenfolge lautet:
        Name, Anzahl Einheiten, Kosten pro Einheit, Einnahmen, Ausgaben
        """
        out = []
        
        if indent<0:
            joiner=""
        else:
            joiner = "\n" + "\t"*indent
        
        out.append( tools.cell( escape(self._name) ) )
        
        if self._unitprice:
            out.append( tools.cell(self.getunitcount()) )
        else:
            out.append( tools.cell() )
        
        out.append( tools.cell( tools.euro(abs(self.getunitprice()),True) ) )
        out.append( tools.cell( tools.euro(self.getincome(),True) ) )
        out.append( tools.cell( tools.euro(self.getcost(),True) ) )
        
        return "\t"*indent+joiner.join(out)

    # Variable getters and setters
    def setname(self,value:str = ""):
        """Legt den Namen der Position fest."""
        self._name = str(value)
    
    def getname(self) -> str:
        """Gibt den Namen der Position zurück."""
        return self._name
    
    def setunitcount(self,value:int = 1):
        """
        Legt die Mengenzahl der Position fest.
        Kann nicht kleiner als 1 sein; wird automatisch korrigiert.
        """
        self._unitcount = int(value)
        if self._unitcount < 1:
            self._unitcount = 1
    
    def getunitcount(self) -> int:
        """Gibt die Mengenzahl der Position zurück."""
        return self._unitcount
    
    def setunitprice(self,value=0.0):
        """Legt den Preis pro Einheit der Position fest."""
        self._unitprice = float(value)
    
    def getunitprice(self) -> float:
        """Gibt den Preis pro Einheit der Position zurück."""
        return self._unitprice
    
    def setvalue(self,value=0.0):
        """
        Legt den Gesamtpreis der Position fest.
        Einnahmen sind positiv, Ausgaben negativ.
        """
        self._value = float(value)
    
    def getvalue(self) -> float:
        """
        Gibt den Gesamtpreis der Position zurück.
        Bei vorhandendem Stückpreis wird der
        gespeicherte Gesamtpreis ignoriert.
        """
        if self._unitprice != 0:
            return self._unitprice * self._unitcount
        return self._value
    
    def setminusvalue(self,value=0.0):
        """
        Legt den Gesamtpreis der Position fest.
        Ausgaben sind positiv, Einnahmen negativ.
        """
        self._value = float(value)*-1
    
    def getincome(self) -> float:
        """
        Gibt die Gesamteinnahmen der Position zurück.
        Bei Ausgaben wird Null zurückgegeben.
        """
        return max(0.0, self.getvalue())
    
    def getcost(self) -> float:
        """
        Gibt die Gesamtausgaben der Position zurück.
        Bei Einnahmen wird Null zurückgegeben.
        """
        return max(0.0, self.getvalue()*-1)
    
    # Properties
    name = property(getname,setname,None,
        "Der Name der Position.")
    unitcount = property(getunitcount,setunitcount,None,
        "Anzahl der Einheiten in der Position.")
    unitprice = property(getunitprice,setunitprice,None,
        "Preis pro Einheit der Position.")
    value = property(getvalue,setvalue,None,
        "Der Gesamtwert der Position in Euro.")
    income = property(getincome,setvalue,None,
        "Die Einnahmen der Position; gibt bei Ausgaben 0 aus.")
    cost = property(getcost,setminusvalue,None,
        "Die Kosten der Position; gibt bei Einnahmen 0 aus.")


class Abrechnung:
    """
    Beschreibt eine Aktivenabrechnung für den ADFC Hamburg.
    Beinhaltet 7 Objekte der Klasse Position im Tupel positions.
    """
    
    # Class constants
    _IBANSPACES = range(18,0,-4)
    _MODES_IBAN = (1,2,3)
    _MODES_SEPA = (2,3)
    _POSITIONCOUNT = 7
    
    # Dunder methods
    def __init__(self):
        """
        Initialisiert ein Objekt der Klasse Abrechnung.
        """
        
        self.positions = self._create_positions(self._POSITIONCOUNT)
        
        self._user = {"name": "", "group": ""}
        self._project = {"name": "", "date": None}
        self._donations = 0.0
        self._payment = {"ibanmode": None, "sepamode": None,
                         "ibanknown": False, "iban": "", "name": ""}
    
    def __str__(self):
        """
        Gibt den Abrechnungsbetrag zurück.
        """
        return tools.euro(self._gettotal())

    def __bool__(self):
        """
        Gibt True zurück, falls eine Position einen Wert hat
        oder eine Spendensumme angegeben wurde.
        """
        for position in self.positions:
            if position:
                return True
        return bool(self.donations)

    # Part of initialization
    def _create_positions(self,amount:int):
        """
        Gibt einen Tupel aus neuen Positionen zurück.
        """
        out = []
        for i in range(amount):
            out.append(Position())
        return tuple(out)

    # Variable getters and setters
    def setusername(self,value:str = ""):
        """Legt den Namen des Aktiven fest."""
        self._user["name"] = str(value)
    
    def getusername(self) -> str:
        """Gibt den Namen des Aktiven zurück."""
        return self._user["name"]
    
    def setusergroup(self,value:str = ""):
        """Legt die Gruppe des Aktiven fest."""
        self._user["group"] = str(value)
    
    def getusergroup(self) -> str:
        """Gibt die Gruppe des Aktiven zurück."""
        return self._user["group"]
    
    def setprojectname(self,value:str = ""):
        """Legt den Namen des Projekts fest."""
        self._project["name"] = str(value)
    
    def getprojectname(self) -> str:
        """Gibt den Namen des Projekts zurück."""
        return self._project["name"]
    
    def setprojectdate(self,value=None):
        """
        Legt das Datum der Abrechnung fest.

        Akzepiert Datums-Objekte oder
        Strings im Format (year-month-day)
        """
        if type(value) == date:
            self._project["date"] = value
        else:
            try:
                temp = str(value).split("-")
                self._project["date"] = date(
                    int(temp[0]), int(temp[1]), int(temp[2]))
            except:
                self._project["date"] = None
    
    def getprojectdate(self) -> date|None:
        """Gibt das Datum der Abrechnung zurück."""
        return self._project["date"]
    
    def setdonations(self,value=0.0):
        """Legt den Betrag eingenommener Spenden fest."""
        self._donations = float(value)
        if self._donations < 0:
            self._donations = 0.0
    
    def getdonations(self) -> float:
        """Gibt den Betrag eingenommener Spenden zurück."""
        return self._donations
    
    def getincome(self) -> float:
        """Gibt den Gesamtbetrag der Einnahmen zurück."""
        out = 0.0
        for i in range(self._POSITIONCOUNT):
            out += self.positions[i].income
        out += self.getdonations()
        return out

    def getcost(self) -> float:
        """Gibt den Gesamtbetrag der Ausgaben zurück."""
        out = 0.0
        for i in range(self._POSITIONCOUNT):
            out += self.positions[i].cost
        return out
    
    def gettotal(self) -> float:
        """Gibt den Betrag der Einnahmen minus Ausgaben zurück."""
        out = 0.0
        for i in range(self._POSITIONCOUNT):
            out += self.positions[i].value
        out += self.getdonations()
        return out
    
    def setaccountname(self,name:str = ""):
        """Legt den Namen des Kontoinhabers fest."""
        self._payment["name"] = str(name)
    
    def getaccountname(self) -> str:
        """Gibt den Namen des Kontoinhabers zurück."""
        return self._payment["name"]
    
    def setaccountiban(self,value=""):
        """
        Legt die IBAN des Bankkontos fest.
        Diese muss aus exakt 20 Ziffern bestehen (kein Ländercode).
        """
        value = str(value).replace(" ","")
        if len(value) == 20 and value.isdigit():
            self._payment["iban"] = str(value)
        else:
            self._payment["iban"] = ""
    
    def getaccountiban(self,spaces:bool = True) -> str:
        """Gibt die IBAN des Bankkontos zurück."""
        out = self._payment["iban"]
        if spaces and len(out) > self._IBANSPACES[0]:
            # add spaces
            for i in self._IBANSPACES:
                out = out[:i] + " " + out[i:]
        return out

    def setibanmode(self,mode=None):
        if mode and int(mode) in self._MODES_IBAN:
            self._payment["ibanmode"] = int(mode)
        else:
            self._payment["ibanmode"] = None
    
    def getibanmode(self) -> int|None:
        return self._payment["ibanmode"]
    
    def setsepamode(self,mode=None):
        if mode and int(mode) in self._MODES_SEPA:
            self._payment["sepamode"] = int(mode)
        else:
            self._payment["sepamode"] = None
    
    def getsepamode(self) -> int|None:
        return self._payment["sepamode"]

    def setibanknown(self,mode=False):
        self._payment["ibanknown"] = bool(mode)
    
    def getibanknown(self) -> bool:
        return self._payment["ibanknown"]

    # Properties
    username = property(getusername,setusername,None,
                        "Der Name des Aktiven.")
    usergroup = property(getusergroup,setusergroup,None,
                         "Der Arbeitsbereich des Aktiven.")
    projectname = property(getprojectname,setprojectname,None,
                           "Der Name der Aktion oder des Projekts.")
    projectdate = property(getprojectdate,setprojectdate,None,
                           "Das Datum der Aktion oder des Projekts.")
    donations = property(getdonations,setdonations,None,
                         "Eingenommene Spenden in Euro.")
    income = property(getincome,None,None,
                      "Gesamteinnahmen in Euro.")
    cost = property(getcost,None,None,
                      "Gesamtausgaben in Euro.")
    total = property(gettotal,None,None,
                     "Gesamtwert Einnahmen minus Ausgaben, in Euro.")
    accountname = property(getaccountname,setaccountname,None,
                           "Der Name des Bankkontoimhabers.")
    iban = property(getaccountiban,setaccountiban,None,
                    "Die IBAN (ohne einleitendes DE) des Bankkontos.")
    accountiban = iban
    ibanmode = property(getibanmode,setibanmode,None,"""
                        Wie die Zahlung abgehandelt wird:

                        1 – Ausgaben werden auf Konto überwiesen.
                        2 – Einnahmen werden von Konto abgebucht.
                        3 – Einnahmen werden von Benutzer überwiesen.
                        """)
    sepamode = property(getsepamode,setsepamode,None,"""
                        Ob ein SEPA-Mandatsformular angefordert wird.

                        1 – Nein, Mandat ist schon erteilt.
                        2 – Ja, Mandat liegt noch nicht vor.
                        3 – Ja, Mandat ist veraltet.
                        """)
    ibanknown = property(getibanknown,setibanknown,None,
                         "Ob die IBAN dem ADFC schon vorliegt.")


class HTMLPrinter:
    """
    Ein Objekt, welches eine HTML-Vorlage einliest
    und dann aus dieser und Objekten der Klasse Abrechnung
    fertig ausgefüllte Abrechnungsformulare im HTML-Format erstellt.
    """
    
    # Class constants
    _CHECKBOXES = {False:"&#9744;",True:"&#9746;"}
    _FILE = "aktive_template.html"
    _PLACEHOLDER = "<!--PLACEHOLDER-->"
    _POSITIONCOUNT = 7
    _SPLIT = "<!--SPLIT-->\n"
    
    # Dunder methods
    def __init__(self):
        """
        Initialisiert ein Objekt der Klasse HTMLPrinter.
        Im Rahmen dessen wird eine HTML-Datei als Template geladen.
        """
        self._template = self._fetch_html()
    
    def __str__(self):
        return self.html_compose()
    
    def __repr__(self):
        return __class__.__name__+"()"
    
    # Template loading
    @classmethod
    def _fetch_html(cls) -> tuple:
        """
        Öffnet das HTML-Template, teilt den Inhalt in Sektionen und
        gegebenenfalls Subsektionen auf und gibt das Ergebnis als
        Tupel zurück.
        """
        with open(cls._FILE) as f:
            sections = f.read().split(cls._SPLIT)
        out = []
        for i in sections:
            out.append (i)
        return tuple(out)
    
    _USER_FIELDS = {0: lambda obj: obj.username, 1: lambda obj: obj.usergroup,
                          2: lambda obj: obj.projectname, 3: lambda obj: obj.projectdate}

    # Methods for template sections
    def _fill_user(self,text:str,input:Abrechnung|None = None):
        segments = text.split(self._PLACEHOLDER)
        if type(input) == Abrechnung:
            for index in range(len(segments)):
                if index in self._USER_FIELDS.keys():
                    segments[index] += str(self._USER_FIELDS[index](input))
        return "".join(segments)
    
    def _fill_positions(self,text:str,input:Abrechnung|None = None):
        """
        Gibt HTML-Tabellenreihen mit 8 Spalten aus und fügt
        gegebenenfalls Positionsdaten mit ein.
        Spalte 1: Index (1 bis 7)
        Spalten 2-6: Siehe Positions.htmlcells()
        Spalten 7,8: leer
        """
        # text should be empty and will be ignored
        TAB = "\t"
        NL = "\n"
        output = []

        for index in range(self._POSITIONCOUNT):
            # One table row for each potential position
            line=""
            line += TAB*4+"<tr>"+NL
            line += TAB*5+tools.cell(str(index+1))+NL

            if (type(input) == Abrechnung and index < len(input.positions)):

                # Position exists, use htmlcells
                line += input.positions[index].htmlcells(indent=5)+NL
                line += TAB*5+tools.cell()*2+NL
            
            else:
                # No position, empty cells
                line += TAB*5+tools.cell()*7+NL
            
            line += TAB*4+"</tr>"+NL
            output.append(line)
        
        return "".join(output)

    def _fill_total(self,text:str,input:Abrechnung|None = None):
        segments = text.split(self._PLACEHOLDER)
        if type(input) == Abrechnung:
            pass
        return "".join(segments)
    
    def _fill_payment(self,text:str,input:Abrechnung|None = None):
        segments = text.split(self._PLACEHOLDER)
        if type(input) == Abrechnung:
            pass
        return "".join(segments)
    
    # Section keywords and corresponding methods
    _SECTIONS = {"USERDATA": _fill_user, "POSITIONS": _fill_positions,
                 "TOTAL": _fill_total, "PAYMENT": _fill_payment}
    
    # Callable methods
    def html_compose(self,input:Abrechnung|None = None):
        """
        Füllt die HTML-Vorlage mit Angaben aus einer Abrechnung aus.
        
        Argumente:
        input: Ein Objekt der Klasse Abrechnung (optional)
        """
        
        out = ""
        
        for section in self._template:
            # Does this section start with a keyword?
            for key in self._SECTIONS.keys():
                if section.startswith("<!--"+key+"-->\n"):
                    # Keyword found; use corresponding method
                    out += self._SECTIONS[key](self,
                        text=section.removeprefix("<!--"+key+"-->\n"),
                        input=input)
                    break
            else:
                # No keyword; use string as is
                out += section
        
        return out
