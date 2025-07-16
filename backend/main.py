import os
from dotenv import load_dotenv
import time
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
from sqlalchemy.exc import OperationalError
from pydantic import BaseModel

# ReportLab Imports
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors

load_dotenv()

# --- Configuração do Banco de Dados PostgreSQL ---
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("POSTGRES_HOST", "db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ContratoDB(Base):
    __tablename__ = "contratos"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(String, index=True)
    cliente_nome = Column(String)
    caminho_pdf = Column(String, unique=True)
    data_criacao = Column(DateTime, default=datetime.utcnow)

try:
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("Tabelas do banco de dados verificadas/criadas com sucesso.")
except Exception as e:
    print(f"Erro ao criar tabelas do banco de dados: {e}")
    exit(1)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="API de Geração de Contratos", version="1.0.0")

origins = [
    "http://localhost:3000",
    "http://localhost",
    "http://31.97.253.178:3000",
    "http://31.97.253.178",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONTRATO_DIR = "contratos_gerados"
CONTRATO_DIR_PATH = f"/app/{CONTRATO_DIR}"
os.makedirs(CONTRATO_DIR_PATH, exist_ok=True)
app.mount(f"/{CONTRATO_DIR}", StaticFiles(directory=CONTRATO_DIR_PATH), name="contratos")

CLIENTE_API_URL = os.getenv("API_CLIENTES_URL")
API_USER = os.getenv("API_USER")
API_PASSWORD = os.getenv("API_PASSWORD")

if not all([CLIENTE_API_URL, API_USER, API_PASSWORD]):
    raise RuntimeError("Variáveis de ambiente da API de clientes não configuradas!")

API_AUTH = (API_USER, API_PASSWORD)

class UserLogin(BaseModel):
    user: str
    password: str

# --- Funções de Geração de PDF ---

def desenhar_cabecalho_e_watermark(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 100)
    canvas.setFillGray(0.90)
    canvas.translate(A4[0] / 2, A4[1] / 2)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "COMETA")
    canvas.restoreState()
    canvas.setFont('Helvetica', 10)
    try:
        logo_path = 'logo.png' 
        if os.path.exists(logo_path):
            logo = ImageReader(logo_path)
            # [CORREÇÃO]: Aumenta a margem superior da logo de 2.5cm para 3cm
            canvas.drawImage(logo, 2 * cm, A4[1] - 3 * cm, width=2.5*cm, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print(f"AVISO: Não foi possível carregar a imagem da logo: {e}")
    # [CORREÇÃO]: Ajusta a posição da linha para corresponder à nova margem da logo
    canvas.line(2*cm, A4[1] - 3.5*cm, A4[0] - 2*cm, A4[1] - 3.5*cm)

def criar_pdf_contrato(cliente_data: dict, assinaturas: dict, anexos: list, output_path: str):
    # [CORREÇÃO]: Aumenta a margem superior do documento para acomodar a logo
    doc = SimpleDocTemplate(output_path, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=4*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    style_body = ParagraphStyle(name='Body', parent=styles['BodyText'], alignment=TA_JUSTIFY, fontSize=11, leading=14)
    style_h5 = ParagraphStyle(name='H5', parent=styles['h5'], fontSize=11, leading=14, spaceBefore=12, spaceAfter=4, fontName='Helvetica-Bold')
    style_center = ParagraphStyle(name='Center', parent=style_body, alignment=TA_CENTER)
    style_main_header = ParagraphStyle(name='MainHeader', parent=styles['h4'], alignment=TA_CENTER, spaceAfter=20)
    story = []

    story.append(Paragraph("INSTRUMENTO PARTICULAR DE CONTRATO DE COMPRA E VENDA DE BENS DE CONSUMO COM ABERTURA DE CRÉDITO", style_main_header))
    
    dados_formatados = {
        'CLIENTE_FILIAL': cliente_data.get('nome_filial', ''),
        'CLIENTE_CNPJ_FILIAL': cliente_data.get('cnpj_filial', ''),
        'CLIENTE_END_FILIAL': cliente_data.get('endereco_filial', ''),
        'CLIENTE_NOME': cliente_data.get('nome_comprador', ''),
        'CLIENTE_RG': cliente_data.get('rg', ''),
        'CLIENTE_CPF': cliente_data.get('cpf', ''),
        'CLIENTE_END': f"{cliente_data.get('endereco', '')}",
        'CLIENTE_NUM': cliente_data.get('numero', ''),
        'CLIENTE_CIDADE': cliente_data.get('cidade', ''),
        'CLIENTE_LIMITE': f"{float(cliente_data.get('limite_credito', 0)):.2f}".replace('.',','),
        'CLIENTE_DIA': datetime.now().strftime('%d'),
        'CLIENTE_MES': datetime.now().strftime('%B'),
        'CLIENTE_ANO': datetime.now().strftime('%Y'),
    }

    texto_contrato = f"""
        Contrato de Compra e Venda de Bens de Consumo com abertura de crédito que celebram entre si, de um lado, a <b>{dados_formatados['CLIENTE_FILIAL']}</b>, inscrita no CNPJ {dados_formatados['CLIENTE_CNPJ_FILIAL']} estabelecida em Endereço {dados_formatados['CLIENTE_END_FILIAL']}, doravante denominada COMETA CALÇADOS, neste ato por seu preposto abaixo assinado, e do outro lado, <b>{dados_formatados['CLIENTE_NOME']}</b> RG {dados_formatados['CLIENTE_RG']} CPF: {dados_formatados['CLIENTE_CPF']} End.: {dados_formatados['CLIENTE_END']}, {dados_formatados['CLIENTE_NUM']}- BA, doravante denominada COMPRADOR (A), através das cláusulas e condições seguintes:
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
        2.3. O(a) COMPRADOR(a) declara ter sido cientificado que a concessão e manutenção de crédito é revisada com base na Política de Crédito vigente na empresa, conforme informações regulamente consultadas nos bureaus de crédito, e assim tanto a concessão quanto o limite descrito no item 2.3 será reavaliado a cada aquisição de MERCADORIAS.
        <br/><br/>
        2.4. Em cumprimento ao item acima, e visando a concessão e manutenção do de crediário de forma sustentável, o(a) COMPRADOR(A) reconhece que a COMETA CALÇADOS poderá revisar o crédito disponibilizado, em virtude da variação positiva ou negativa do histórico de crédito do(a) próprio(a) COMPRADOR(a), e por esse motivo, o(a) COMPRADOR(A) autoriza a COMETA CALÇADOS realizar análises periódicas do seu perfil de crédito , podendo aumento ou diminuir o valor disponibilizado. O (a) COMPRADOR(A) poderá revogar a autorização para aumento de valores disponibilizados, a qualquer momento, através de solicitação por escrito na loja COMETA CALÇADOS.
        <br/><br/>
        2.5. O(a) COMPRADOR(a)resta cientificado(a) que o não pagamento de qualquer parcela dos contatos de compra e venda na sua respectiva data de vencimento definida e discriminada nos comprovantes de compra, ou a inclusão do seu CPF em cadastro de inadimplente por qualquer credor terceiro, são motivos suficientes para a imediata suspensão da concessão de crédito.
        <br/><br/>
        <b>3. DA FORMA E CONDIÇÕES DE PAGAMENTO.</b><br/>
        3.1 No ato da aquisição das MERCADORIAS (a) COMPRADOR(A) receberá comprovantes de compra (carnê), representativo de sua dívida, onde constará os valores devidos à COMETA CALÇADOS as respectivas datas de vencimentos, o qual integrará o presente contrato para todos os efeitos.
        <br/><br/>
        3.2. O(a) COMPRADOR(a)se obriga a pagar a quantia indicada no contrato de venda e compra e MERCADORIAS de consumo conforme parcelamento com valores definidos e datas de vencimento discriminadas nos comprovantes de compra, portanto, o(a) COMPRADOR(a) efetuará o pagamento das parcelas com valores e datas de vencimento definidos e discriminados nos comprovantes de compra (carnê).
        <br/><br/>
        3.3. O limite máximo de parcelas, o qual é sempre baseado no valor mínimo de cada parcela, será estabelecido pela política de crédito da empresa trimestralmente e sempre será divulgado de forma ampla e irrestrita pela COMETA CALÇADOS em suas propagandas, banners, outdoors, redes e mídias sociais de internet, e ainda, na própria sede da loja em cartazes de publicidade.
        <br/><br/>
        3.4. Dessa forma, o(a) COMPRADOR(A) resta cientificado que o valor mínimo da prestação poderá ser revisado, para mais ou para menos, cabendo a ele(a) observar o valor mínimo da prestação, no moldo item acima, antes da realização de qualquer aquisição de MERCADORIAS.
        <br/><br/>
        <b>4. DO LOCAL DE PAGAMENTO.</b><br/>
        Para que possa se valer de todas as modalidades de pagamento disponíveis (PIX, espécie, cartões de débito e crédito), (a) COMPRADOR(a) deverá efetuar os pagamentos das parcelas discriminadas nos comprovantes de compra na própria loja COMETA CALÇADOS em que foi realizada a aquisição dos bens os bens, cujo endereço está descrito no carnê de pagamentos. O (a) COMPRADOR(a) poderá efetuar o pagamento em loja COMETA CALÇADOS diversa da que foi realizada a aquisição dos MERCADORIAS, contudo, nessa hipótese não será possível a realização de pagamentos mediante o uso de cartões de crédito ou débito.
        <br/><br/>
        4.1. Na hipótese de pagamento das mensalidades com cartão de crédito/débito serão acrescidas as taxas de administração das operadoras de cartão.
        <br/><br/>
        <b>5. DO VENCIMENTO ANTECIPADO</b><br/>
        O não pagamento de qualquer parcela na sua respectiva data de vencimento definida e discriminada nos comprovantes de compra por prazo superior a 30 (trinta) dias, conforme disposto no art. 394 do Código Civil, ocasionará, imediatamente, sem necessidade de qualquer notificação ou interpelação prévia, o vencimento antecipado de todas as parcelas vincendas à época do inadimplemento e a imediata execução do(s) contrato(s) de compra e venda a ser(em) firmado(s) com base no crédito concedido por meio deste instrumento.
        <br/><br/>
        <b>6. DA MULTA E DOS ENCARGOS DE MORA POR INADIMPLEMENTO</b><br/>
        Em caso de atraso ou não pagamento das prestações pactuadas o Comprador estará sujeito ao pagamento da multa única de 2% indicada no art. § 1°do art. 52 do CDC, além de encargos moratórios mensais/pro rata dia incidentes sobre o valor inadimplido, os quais serão expressamente indicados no (s) contrato(s) de compra e venda a ser(em) firmado(s) (carnês) com base no crédito concedido no momento da aquisição.
        <br/><br/>
        <b>7. DA INSCRIÇÃO EM CADASTROS DE CONTROLE DE CRÉDITO.</b><br/>
        7.1. Além das penalidades acima descritas, em caso de inadimplemento das obrigações pactuadas, persistindo o inadimplemento de qualquer parcela do carnê por mais de 15 (quinze) dias, confere a COMETA CALÇADOS o direito potestativo de inscrever o(a) COMPRADOR(A) em cadastros de inadimplentes (bureaus de crédito), tais como SPC, SERASA, etc.
        <br/><br/>
        <b>8. DO FORNECIMENTO E DA AUTORIZAÇÃO PARA TRATAMENTO DOS DADOS.</b><br/>
        8.1. O(a) COMPRADOR(A), declara e assume inteira responsabilidade pelos dados fornecidos, confirmando a veracidade das informações prestadas, comprometendo-se a informar a Vendedora toda e qualquer alteração no seu endereço comercial e ou residencial.
        <br/><br/>
        8.2. Declaro meu expresso CONSENTIMENTO para que a {dados_formatados['CLIENTE_FILIAL']}, inscrita no CNPJ {dados_formatados['CLIENTE_CNPJ_FILIAL']} estabelecida em Endereço {dados_formatados['CLIENTE_END_FILIAL']}, doravante denominada COMETA CALÇADOS torne-se controladora dos dados por mim cedidos através deste documento, nos termos do artigo 5º, VI, da Lei Geral de Proteção de Dados (LGPD). Necessário ainda afirmar que esta autorização está sendo por mim concedida de maneira expressa conforme o art.7ª, I, e art. 8º da referida lei com o fito de instrumentalizar a execução do contrato de crediário dos futuros contratos de venda e compra a crediário por mim firmados com a controladora, para que esta tenha informações suficientes para cumprir com suas obrigações legais, os dados necessários para cumprimento das obrigações legais, assim como para a proteção ao crédito (Art.7º, II, V, X).
        <br/><br/>
        8.3. Ainda se destaca que estou ciente de que a controladora faz uso da marca COMETA CALÇADOS, de propriedade da COMETA ADMINISTRAÇÃO EMPRESARIAL , inscrita no CNPJ sob o registro 12.532.642/0001-10 . Assim sendo, declaro plena ciência e acordo que os dados aqui tratados poderão ser compartilhados e utilizados, em todo ou em parte, com pessoas físicas ou jurídicas, departamentos internos, setores e empresas vinculadas e/ou associadas a COMETA ADMINISTRAÇÃO EMPRESARIAL e as outras empresas cessionárias das marcas COMETA CALÇADOS.
        <br/><br/>
        8.4. A COMETA CALÇADOS declara e cientifica a(o) COMPRADOR(A), portanto, que no tratamento dos dados pessoais, sempre que necessário, ela poderá compartilhar os dados pessoais com outras empresas cessionárias da marca COMETA CALÇADOS (que se obrigam a manter idêntico nível de segurança e privacidade), com prestadores de serviços de análises antifraude, intermediação de pagamentos, cobrança terceirizada, empresas de confecção de material e envio de correspondência, gestão de campanhas de marketing, enriquecimento de base de dados e armazenamento em nuvem, bem como, os órgãos reguladores. A COMETA CALÇADOS declara e cientifica o(a) COMPRADOR(A) que não efetua a comercialização de dados pessoais. Apresentamos a seguir um resumo destas possibilidades:
        <br/><br/>
        8.5. O(a) COMPRADOR(A) se compromete a manter seus dados sempre atualizados, inclusive para efeito de comunicação entre as partes, e por esse motivo se compromete a informar todas as alterações em seu endereço residencial e profissional e dados eletrônicos. O(a) COMPRADOR(A) declara ter sido cientificado que em caso de não comunicação de alteração dos seus dados pessoais, considerar-se-á válida a notificação enviada ao endereço indicado pelo comprador no ato da assinatura do presente contrato, para o fim do que dispõe o artigo 43 parágrafo segundo do Código de Defesa do Consumidor.
        <br/><br/>
        <b>9. DAS CONDIÇÕES GERAIS.</b><br/>
        9.1 As partes procurarão sempre o comum acordo para resolverem as pendências, lacunas e omissões que emergirem deste contrato.
        <br/><br/>
        9.2. Para dirimir as controvérsias e pendencias oriundas da aplicação deste contrato, fica eleito o foro da comarca do domicílio do(a) COMPRADOR(A).
    """
    story.append(Paragraph(texto_contrato, style_body))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(f"E por estarem assim ajustado assinam o presente, em 02 Vias, para que produza os jurídicos e legais efeitos, na presença de suas testemunhas.", style_body))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f"{dados_formatados['CLIENTE_CIDADE']}, {dados_formatados['CLIENTE_DIA']} de {dados_formatados['CLIENTE_MES']} de {dados_formatados['CLIENTE_ANO']}", style_center))
    
    story.append(Spacer(1, 2*cm))

    def get_signature_image(image_path):
        if image_path and os.path.exists(image_path):
            try:
                return Image(image_path, width=5*cm, height=2.5*cm, kind='proportional')
            except Exception as e:
                print(f"Não foi possível carregar a imagem da assinatura {image_path}: {e}")
                return Spacer(0, 0)
        return Spacer(0, 2.5*cm)

    style_assinatura = ParagraphStyle(name='Signature', parent=style_center, fontSize=9, leading=12)

    p_comprador = Paragraph(f"_________________________<br/>Comprador(a): {dados_formatados['CLIENTE_NOME']}", style_assinatura)
    p_testemunha1 = Paragraph("_________________________<br/>Testemunha 1<br/>R.G:", style_assinatura)
    p_vendedor = Paragraph("_________________________<br/>Vendedor(a)", style_assinatura)
    p_testemunha2 = Paragraph("_________________________<br/>Testemunha 2<br/>R.G:", style_assinatura)

    assinatura_comprador = get_signature_image(assinaturas.get('cliente'))
    assinatura_testemunha1 = get_signature_image(assinaturas.get('testemunha1'))
    assinatura_vendedor = get_signature_image(assinaturas.get('vendedor'))
    assinatura_testemunha2 = get_signature_image(assinaturas.get('testemunha2'))

    data = [
        [assinatura_comprador, assinatura_testemunha1],
        [p_comprador, p_testemunha1],
        [Spacer(0, 2*cm), Spacer(0, 2*cm)],
        [assinatura_vendedor, assinatura_testemunha2],
        [p_vendedor, p_testemunha2]
    ]

    signature_table = Table(data, colWidths=[doc.width/2.0, doc.width/2.0])
    signature_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    
    story.append(signature_table)
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(f"Obs. O presente contrato está registrado no Cartório de Títulos e Documentos da Comarca de {dados_formatados['CLIENTE_CIDADE']}.", style_body))

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

    doc.build(story, onFirstPage=desenhar_cabecalho_e_watermark, onLaterPages=desenhar_cabecalho_e_watermark)


# --- Endpoints da API ---

@app.post("/login", summary="Autentica um usuário")
def login_user(login_data: UserLogin):
    auth_url = "http://168.0.238.158:8094/contract/api/userscontract/"
    auth_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic Y29tZXRhLnNlcnZpY2U6MTAzMDIw'
    }
    auth_payload = {
        "user": login_data.user,
        "password": login_data.password
    }
    try:
        response = requests.post(auth_url, json=auth_payload, headers=auth_headers, timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            return {"status": "sucesso", "user": {"nome": user_data.get("user", login_data.user), "token": user_data.get("token")}}
        else:
            raise HTTPException(status_code=401, detail="Credenciais inválidas.")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Serviço de autenticação indisponível: {e}")

@app.get("/clientes/{cliente_id}", summary="Busca dados de um cliente")
def buscar_cliente(cliente_id: str):
    try:
        response = requests.get(f"{CLIENTE_API_URL}?id={cliente_id}", auth=API_AUTH, timeout=10)
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Cliente não encontrado na API externa.")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=504,
            detail=f"Não foi possível comunicar com a API de clientes. Verifique a conexão. Erro: {e}"
        )

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
    try:
        cliente_data = buscar_cliente(cliente_id)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    temp_files = []
    assinaturas_salvas = {}
    anexos_salvos = []

    def salvar_arquivo(arquivo: UploadFile, prefixo: str) -> str:
        ext = os.path.splitext(arquivo.filename)[-1] or '.png'
        path = os.path.join(CONTRATO_DIR_PATH, f"temp_{prefixo}_{uuid.uuid4()}{ext}")
        with open(path, "wb") as buffer:
            shutil.copyfileobj(arquivo.file, buffer)
        temp_files.append(path)
        return path

    arquivos_assinatura = {
        'cliente': assinatura_cliente, 'vendedor': assinatura_vendedor,
        'testemunha1': assinatura_testemunha1, 'testemunha2': assinatura_testemunha2
    }
    for nome, arquivo in arquivos_assinatura.items():
        if arquivo and arquivo.filename:
            assinaturas_salvas[nome] = salvar_arquivo(arquivo, f"ass_{nome}")
    
    for i, anexo in enumerate(anexos):
        if anexo and anexo.filename:
            anexos_salvos.append(salvar_arquivo(anexo, f"anexo_{i}"))

    pdf_filename = f"contrato_{cliente_id}_{uuid.uuid4().hex[:8]}.pdf"
    pdf_path = os.path.join(CONTRATO_DIR_PATH, pdf_filename)
    
    try:
        criar_pdf_contrato(cliente_data, assinaturas_salvas, anexos_salvos, pdf_path)
    except Exception as e:
        print(f"ERRO DETALHADO AO GERAR PDF: {e}")
        for path in temp_files:
            try:
                os.remove(path)
            except OSError:
                pass
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro interno ao gerar o documento PDF: {e}")
    finally:
        for path in temp_files:
            try:
                os.remove(path)
            except OSError:
                pass

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
    contratos = db.query(ContratoDB).order_by(ContratoDB.data_criacao.desc()).all()
    return [{"id": c.id, "cliente_id": c.cliente_id, "cliente_nome": c.cliente_nome, "url": f"/{CONTRATO_DIR}/{c.caminho_pdf}", "data_criacao": c.data_criacao} for c in contratos]
