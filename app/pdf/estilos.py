from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

estilos = getSampleStyleSheet()

titulo = estilos["Title"]
titulo.alignment = TA_CENTER

normal = estilos["Normal"]

heading = estilos["Heading2"]