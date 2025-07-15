import os
from dotenv import load_dotenv
import uuid
import requests
import shutil
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

# ReportLab Imports
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.utils import ImageReader

# Carrega variáveis de ambiente do ficheiro .env
load_dotenv()

# --- Configuração do DB e FastAPI (Preparado para Produção) ---
# O diretório /app/database será mapeado para um volume persistente no docker-compose.yml
DB_DIR = "/app/database"
os.makedirs(DB_DIR, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_DIR}/contratos.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ContratoDB(Base):
    """Modelo da tabela de contratos no banco de dados."""
    __tablename__ = "contratos"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(String, index=True)
    cliente_nome = Column(String)
    caminho_pdf = Column(String, unique=True)
    data_criacao = Column(DateTime, default=datetime.utcnow)

# Cria a tabela no banco de dados se ela não existir
Base.metadata.create_all(bind=engine)

def get_db():
    """Função de dependência para obter uma sessão do banco de dados."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="API de Geração de Contratos", version="1.0.0")

# --- Middlewares e Configurações ---
origins = ["http://localhost:3000", "http://localhost", "https://seu_dominio.com"] # Adicione o seu domínio de produção
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diretório para salvar os contratos gerados
CONTRATO_DIR = "contratos_gerados"
os.makedirs(CONTRATO_DIR, exist_ok=True)
app.mount(f"/{CONTRATO_DIR}", StaticFiles(directory=CONTRATO_DIR), name="contratos")

# Configuração da API de Clientes
CLIENTE_API_URL = os.getenv("API_CLIENTES_URL")
API_USER = os.getenv("API_USER")
API_PASSWORD = os.getenv("API_PASSWORD")

# Verifica se as variáveis de ambiente essenciais foram carregadas
if not all([CLIENTE_API_URL, API_USER, API_PASSWORD]):
    raise RuntimeError("Variáveis de ambiente (API_CLIENTES_URL, API_USER, API_PASSWORD) não configuradas!")

API_AUTH = (API_USER, API_PASSWORD)

# --- Funções de Geração de PDF ---

def desenhar_cabecalho_e_watermark(canvas, doc):
    """Desenha a marca d'água e o cabeçalho em TODAS as páginas do contrato."""
    canvas.saveState()
    # Marca d'água
    canvas.setFont('Helvetica-Bold', 100)
    canvas.setFillGray(0.90)
    canvas.translate(A4[0] / 2, A4[1] / 2)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "COMETA")
    canvas.restoreState()
    
    # Cabeçalho com Logo
    canvas.setFont('Helvetica', 10)
    try:
        # Assumindo que a logo está na raiz do backend
        logo_path = 'logo.png' 
        if os.path.exists(logo_path):
            logo = ImageReader(logo_path)
            canvas.drawImage(logo, 2 * cm, A4[1] - 2.5 * cm, width=2.5*cm, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print(f"AVISO: Não foi possível carregar a imagem da logo: {e}")
    
    canvas.line(2*cm, A4[1] - 3*cm, A4[0] - 2*cm, A4[1] - 3*cm)


def criar_pdf_contrato(cliente_data: dict, assinaturas: dict, anexos: list, output_path: str):
    """
    Gera o documento PDF completo do contrato, com texto, assinaturas e anexos.
    """
    doc = SimpleDocTemplate(output_path, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=3.5*cm, bottomMargin=2*cm)
    
    # --- Estilos ---
    styles = getSampleStyleSheet()
    style_body = ParagraphStyle(name='Body', parent=styles['BodyText'], alignment=TA_JUSTIFY, fontSize=11, leading=14)
    style_h5 = ParagraphStyle(name='H5', parent=styles['h5'], fontSize=11, leading=14, spaceBefore=10, spaceAfter=2, fontName='Helvetica-Bold')
    style_center = ParagraphStyle(name='Center', parent=style_body, alignment=TA_CENTER)
    style_main_header = ParagraphStyle(name='MainHeader', parent=styles['h4'], alignment=TA_CENTER, spaceAfter=20)
    
    story = []

    # --- Conteúdo do Contrato (Baseado em contrato.docx) ---
    story.append(Paragraph("INSTRUMENTO PARTICULAR DE CONTRATO DE COMPRA E VENDA DE BENS DE CONSUMO COM ABERTURA DE CRÉDITO", style_main_header))
    
    # Dados do cliente para preenchimento
    dados_formatados = {
        'CLIENTE_FILIAL': cliente_data.get('nome_filial', ''),
        'CLIENTE_CNPJ_FILIAL': cliente_data.get('cnpj_filial', ''),
        'CLIENTE_END_FILIAL': cliente_data.get('endereco_filial', ''),
        'CLIENTE_NOME': cliente_data.get('nome_comprador', ''),
        'CLIENTE_RG': cliente_data.get('rg', ''),
        'CLIENTE_CPF': cliente_data.get('cpf', ''),
        'CLIENTE_END': f"{cliente_data.get('endereco', '')}, {cliente_data.get('numero', '')}",
        'CLIENTE_CIDADE': cliente_data.get('cidade', ''),
        'CLIENTE_LIMITE': f"{float(cliente_data.get('limite_credito', 0)):.2f}".replace('.',','),
        'CLIENTE_DIA': datetime.now().strftime('%d'),
        'CLIENTE_MES': datetime.now().strftime('%B'),
        'CLIENTE_ANO': datetime.now().strftime('%Y'),
    }

    texto_contrato = f"""
        Contrato de Compra e Venda de Bens de Consumo com abertura de crédito que celebram entre si, de um lado, a <b>{dados_formatados['CLIENTE_FILIAL']}</b>, inscrita no CNPJ {dados_formatados['CLIENTE_CNPJ_FILIAL']} estabelecida em Endereço {dados_formatados['CLIENTE_END_FILIAL']}, doravante denominada COMETA CALÇADOS, neste ato por seu preposto abaixo assinado, e do outro lado, <b>{dados_formatados['CLIENTE_NOME']}</b> RG {dados_formatados['CLIENTE_RG']} CPF: {dados_formatados['CLIENTE_CPF']} End.: {dados_formatados['CLIENTE_END']} - BA, doravante denominada COMPRADOR(A), através das cláusulas e condições seguintes:
        <br/><br/>
        <b>1. DO OBJETO.</b><br/>
        1.1 O objeto do presente instrumento é abertura e concessão de crédito para futura aquisição de bens de consumo comercializados exclusivamente pela COMETA CALÇADOS, não sendo possível o uso do crédito concedido no presente contrato de qualquer outra forma. Os bens de consumo, comercializados pela COMETA CALÇADOS e doravante denominados MERCADORIAS, serão individualizados, descritos e precificados no(s) comprovante(s) de compra(s) devidamente assinado(s) pelo COMPRADOR(A) quando se der(em) a(s) sua(s) respetiva(s) aquisição(ões).
        <br/><br/>
        1.2 O COMPRADOR declara plena ciência e expressa concordância de que o(s) contrato(s) de compra e venda a serem firmados com base no crédito concedido por meio deste instrumento, o(s) qual(ais) será(ão) devidamente assinado(s) pelo COMPRADOR, mediante rubrica, conforme disposto no art. 784 do CPC, se constituirá em título executivo extrajudicial.
        <br/><br/>
        <b>2. DA CONCESSÃO E REVISÃO DO CRÉDITO</b><br/>
        2.1. O(a) COMPRADOR(a) foi devidamente informado e declara plena ciência de que o crédito ora concedido somente poderá ser utilizado para aquisição de MERCADORIAS na própria loja COMETA CALÇADOS ora signatária, ou ainda, em qualquer uma das lojas cessionárias da marca COMETA CALÇADOS.
        <br/><br/>
        2.2. No momento da assinatura deste instrumento a COMETA CALÇADOS disponibiliza o(a) Comprador(a) o limite de crédito no importe de <b>R$ {dados_formatados['CLIENTE_LIMITE']}</b> Reais para aquisição parcelada dos bens de consumo na própria loja COMETA CALÇADOS ora signatária, ou ainda, em qualquer uma das lojas cessionárias da marca COMETA CALÇADOS.
        <br/><br/>
        <b>6. DA MULTA E DOS ENCARGOS DE MORA POR INADIMPLEMENTO</b><br/>
        Em caso de atraso ou não pagamento das prestações pactuadas o Comprador estará sujeito ao pagamento da multa única de 2% indicada no art. § 1°do art. 52 do CDC, além de encargos moratórios mensais/pro rata dia incidentes sobre o valor inadimplido, os quais serão expressamente indicados no (s) contrato(s) de compra e venda a ser(em) firmado(s) (carnês) com base no crédito concedido no momento da aquisição.
        <br/><br/>
        <b>8. DO FORNECIMENTO E DA AUTORIZAÇÃO PARA TRATAMENTO DOS DADOS.</b><br/>
        8.2. Declaro meu expresso CONSENTIMENTO para que a {dados_formatados['CLIENTE_FILIAL']}, inscrita no CNPJ {dados_formatados['CLIENTE_CNPJ_FILIAL']} estabelecida em Endereço {dados_formatados['CLIENTE_END_FILIAL']}, doravante denominada COMETA CALÇADOS torne-se controladora dos dados por mim cedidos através deste documento, nos termos do artigo 5º, VI, da Lei Geral de Proteção de Dados (LGPD).
        <br/><br/>
        <b>9. DAS CONDIÇÕES GERAIS.</b><br/>
        9.2. Para dirimir as controvérsias e pendencias oriundas da aplicação deste contrato, fica eleito o foro da comarca do domicílio do(a) COMPRADOR(A).
    """
    story.append(Paragraph(texto_contrato, style_body))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(f"E por estarem assim ajustado assinam o presente, em 02 Vias, para que produza os jurídicos e legais efeitos, na presença de suas testemunhas.", style_body))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f"Obs. O presente contrato está registrado no Cartório de Títulos e Documentos da Comarca de {dados_formatados['CLIENTE_CIDADE']}.", style_body))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(f"{dados_formatados['CLIENTE_CIDADE']}, {dados_formatados['CLIENTE_DIA']} de {dados_formatados['CLIENTE_MES']} de {dados_formatados['CLIENTE_ANO']}", style_center))
    story.append(Spacer(1, 4*cm))

    # --- Assinaturas (desenhadas diretamente no canvas para posicionamento preciso) ---
    def draw_assinaturas_na_ultima_pagina(canvas, doc):
        """Usa o canvas para desenhar as linhas e imagens das assinaturas."""
        y_pos_1 = 6 * cm  # Altura da primeira linha
        y_pos_2 = 3 * cm  # Altura da segunda linha
        x_col_1 = 2.5 * cm
        x_col_2 = 11.5 * cm
        largura_linha = 7 * cm
        
        # Função auxiliar para desenhar uma assinatura
        def desenhar_assinatura(x, y, imagem_path, texto, texto_rg=False):
            if imagem_path:
                try:
                    canvas.drawImage(ImageReader(imagem_path), x, y + 5, width=4*cm, height=2*cm, preserveAspectRatio=True, mask='auto')
                except Exception as e:
                    print(f"Erro ao desenhar imagem da assinatura {imagem_path}: {e}")
            canvas.line(x, y, x + largura_linha, y)
            canvas.drawCentredString(x + largura_linha/2, y - 0.5*cm, texto)
            if texto_rg:
                canvas.drawCentredString(x + largura_linha/2, y - 1*cm, "R.G:")

        # Desenha as 4 assinaturas
        desenhar_assinatura(x_col_1, y_pos_1, assinaturas.get('cliente'), f"Comprador(a): {dados_formatados['CLIENTE_NOME']}")
        desenhar_assinatura(x_col_2, y_pos_1, assinaturas.get('testemunha1'), "Testemunha 1", texto_rg=True)
        desenhar_assinatura(x_col_1, y_pos_2, assinaturas.get('vendedor'), "Vendedor(a)")
        desenhar_assinatura(x_col_2, y_pos_2, assinaturas.get('testemunha2'), "Testemunha 2", texto_rg=True)

    # --- Anexos ---
    if anexos:
        story.append(PageBreak())
        story.append(Paragraph("DOCUMENTOS ANEXADOS", style_h5))
        story.append(Spacer(1, 1*cm))
        for anexo_path in anexos:
            try:
                img = Image(anexo_path, width=16*cm, preserveAspectRatio=True, hAlign='CENTER')
                story.append(img)
                story.append(Spacer(1, 1*cm))
            except Exception as e:
                print(f"Não foi possível adicionar o anexo {anexo_path} ao PDF: {e}")

    # --- Constrói o PDF ---
    # A função de desenhar assinaturas só é chamada na última página de conteúdo
    doc.build(story, onFirstPage=desenhar_cabecalho_e_watermark, onLaterPages=desenhar_cabecalho_e_watermark, canvasmaker=lambda *args, **kwargs: draw_assinaturas_na_ultima_pagina(*args, **kwargs) or type(doc).CANVAS_CLASS(*args, **kwargs))


# --- Endpoints da API ---

@app.get("/clientes/{cliente_id}", summary="Busca dados de um cliente")
def buscar_cliente(cliente_id: str):
    """
    Consulta uma API externa para obter os dados de um cliente específico pelo seu ID.
    """
    try:
        response = requests.get(f"{CLIENTE_API_URL}?id={cliente_id}", auth=API_AUTH, timeout=10)
        response.raise_for_status() # Lança um erro para respostas 4xx/5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        # Log do erro pode ser adicionado aqui
        raise HTTPException(status_code=404, detail=f"Erro ao comunicar com a API de clientes ou cliente não encontrado: {e}")


@app.post("/gerar-contrato", summary="Gera um novo contrato em PDF")
async def gerar_contrato_endpoint(
    db: Session = Depends(get_db),
    cliente_id: str = Form(...),
    assinatura_cliente: Optional[UploadFile] = File(None),
    assinatura_vendedor: Optional[UploadFile] = File(None),
    assinatura_testemunha1: Optional[UploadFile] = File(None),
    assinatura_testemunha2: Optional[UploadFile] = File(None),
    anexos: List[UploadFile] = File([])
):
    """
    Recebe os dados do formulário, gera o PDF do contrato, salva no servidor,
    registra no banco de dados e retorna a URL do ficheiro.
    """
    try:
        cliente_data = buscar_cliente(cliente_id)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=f"Falha ao obter dados do cliente: {e.detail}")

    temp_files = []
    assinaturas_salvas = {}
    anexos_salvos = []

    # Função para salvar um UploadFile temporariamente
    def salvar_arquivo(arquivo: UploadFile, prefixo: str) -> str:
        ext = os.path.splitext(arquivo.filename)[-1] or '.png'
        path = os.path.join(CONTRATO_DIR, f"temp_{prefixo}_{uuid.uuid4()}{ext}")
        with open(path, "wb") as buffer:
            shutil.copyfileobj(arquivo.file, buffer)
        temp_files.append(path)
        return path

    # Salva assinaturas
    arquivos_assinatura = {
        'cliente': assinatura_cliente, 'vendedor': assinatura_vendedor,
        'testemunha1': assinatura_testemunha1, 'testemunha2': assinatura_testemunha2
    }
    for nome, arquivo in arquivos_assinatura.items():
        if arquivo and arquivo.filename:
            assinaturas_salvas[nome] = salvar_arquivo(arquivo, f"ass_{nome}")
    
    # Salva anexos
    for i, anexo in enumerate(anexos):
        if anexo and anexo.filename:
            anexos_salvos.append(salvar_arquivo(anexo, f"anexo_{i}"))

    # Gera o nome final do PDF
    pdf_filename = f"contrato_{cliente_id}_{uuid.uuid4().hex[:8]}.pdf"
    pdf_path = os.path.join(CONTRATO_DIR, pdf_filename)
    
    try:
        # Chama a função principal de criação do PDF
        criar_pdf_contrato(cliente_data, assinaturas_salvas, anexos_salvos, pdf_path)
    except Exception as e:
        # Em caso de erro na geração, limpa os ficheiros temporários
        for path in temp_files: os.remove(path)
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro interno ao gerar o documento PDF: {e}")
    finally:
        # Limpa os ficheiros temporários após a geração (sucesso ou falha)
        for path in temp_files:
            try:
                os.remove(path)
            except OSError:
                pass

    # Salva o registo do contrato no banco de dados
    novo_contrato = ContratoDB(
        cliente_id=cliente_id, 
        cliente_nome=cliente_data.get("nome_comprador", "N/A"), 
        caminho_pdf=pdf_filename
    )
    db.add(novo_contrato)
    db.commit()

    return JSONResponse(
        status_code=201,
        content={
            "status": "sucesso", 
            "message": "Contrato gerado com sucesso!",
            "contrato_url": f"/{CONTRATO_DIR}/{pdf_filename}"
        }
    )

@app.get("/contratos", summary="Lista os contratos gerados")
def listar_contratos(db: Session = Depends(get_db)):
    """
    Retorna uma lista de todos os contratos registrados no banco de dados.
    """
    contratos = db.query(ContratoDB).order_by(ContratoDB.data_criacao.desc()).all()
    return [{"id": c.id, "cliente_id": c.cliente_id, "cliente_nome": c.cliente_nome, "url": f"/{CONTRATO_DIR}/{c.caminho_pdf}", "data_criacao": c.data_criacao} for c in contratos]