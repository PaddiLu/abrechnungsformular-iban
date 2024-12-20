"""
Modul, welches die URL-Pfade für die Flask-App definiert und die
entsprechenden Inhalte anzeigt.
"""

# Imports
from flask import Blueprint, render_template, request, abort
from flask_weasyprint import HTML, CSS, render_pdf

from app import aktive, VERSION

# Constants
AKTIVE_HTML = 'templates/documents/aktive_template.html'
AKTIVE_CSS = 'templates/documents/aktive_template.css'
STATIC = 'pages.static'

# Routes
pages = Blueprint('pages',__name__,
                  template_folder='templates',
                  static_folder='../static',
                  static_url_path='/static')

@pages.route('/index')
@pages.route('/')
def index():
    """
    Zeigt das Formular zur Erstellung einer Aktivenabrechnung an
    """
    return render_template('form_aktive.html', static=STATIC, version=VERSION)

@pages.route('/abrechnung', methods=['GET'])
def aktive_pdf():
    """
    Zeigt eine Aktivenabrechnung als PDF-Datei an.

    Daten werden aus einem GET-Querystring ausgelesen. Falls es keinen
    gibt, wird ein vorgefertigtes leeres PDF-Dokument angezeigt.
    """
    if request.method == 'GET' and request.args:
        # Query provided; create new PDF
        abrechnung = aktive.Abrechnung()
        try:
            # Get data from query string
            abrechnung.evaluate_query(request.args.to_dict())
        except:
            # Bad Request
            abort(400)
        # Prepare document as HTML
        printer = aktive.HTMLPrinter(AKTIVE_HTML)
        document = printer.html_compose(abrechnung)
        # Read in CSS file
        with open(AKTIVE_CSS) as f:
            formatting = f.read()
        # Select a filename for the resulting file
        filename = abrechnung.suggest_filename()+'.pdf'
        # Create PDF from HTML and CSS
        return render_pdf(HTML(string=document),
                          stylesheets=[CSS(string=formatting)],
                          download_filename=filename)
    else:
        # No query provided; use premade empty PDF instead
        return pages.send_static_file('blank/Aktivenabrechnung.pdf')

@pages.route('/favicon.ico')
def favicon():
    """Returns the favicon."""
    return pages.send_static_file('img/favicon.ico')
