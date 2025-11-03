from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import math

def draw_divided_circle(c, center_x, center_y, radius, divisions):
    # Desenha o círculo principal
    c.circle(center_x, center_y, radius, stroke=1, fill=0)
    
    # Se houver apenas uma divisão, não desenha linhas
    if divisions <= 1:
        return
    
    # Desenha as linhas divisórias
    for i in range(divisions):
        angle = 2 * math.pi * i / divisions
        end_x = center_x + radius * math.cos(angle)
        end_y = center_y + radius * math.sin(angle)
        c.line(center_x, center_y, end_x, end_y)

def create_circle_fractions_pdf(filename):
    # Cria o canvas (área de desenho)
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # Define um raio maior para o círculo
    radius = 250  # Aumentei o raio para 80 mm
    
    for divisions in range(1, 13):
        # Centraliza o círculo na página
        center_x = width / 2
        center_y = height / 2
        
        # Desenha o círculo dividido
        draw_divided_circle(c, center_x, center_y, radius, divisions)
        
        # Adiciona o texto com o número de divisões
        # c.setFont("Helvetica", 16)
        # c.drawCentredString(center_x, center_y - radius - 20, f"Círculo dividido em {divisions} parte(s) igual(is)")
        
        # Adiciona o texto da fração
        if divisions > 1:
            c.setFont("Helvetica", 14)
            c.drawCentredString(center_x, center_y - radius - 40, f"Cada parte representa 1/{divisions} do todo")
        else:
            c.setFont("Helvetica", 14)
            c.drawCentredString(center_x, center_y - radius - 40, "O círculo inteiro (1/1)")
        
        # Finaliza a página atual e inicia uma nova
        c.showPage()
    
    # Salva o PDF
    c.save()

# Cria o PDF com os círculos
create_circle_fractions_pdf("circulos_fracoes.pdf")
print("PDF criado com sucesso: circulos_fracoes.pdf")