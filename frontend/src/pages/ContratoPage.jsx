import React, { useRef, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import SignatureCanvas from 'react-signature-canvas';
import { gerarContrato } from '../services/api';
import './ContratoPage.css';

// Função para converter data URL para Blob
const dataURLtoBlob = (dataurl) => {
    if (!dataurl) return null;
    const arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while(n--){
        u8arr[n] = bstr.charCodeAt(n);
    }
    return new Blob([u8arr], {type:mime});
};

// Componente do Modal de Assinatura
const SignatureModal = ({ onConfirm, onClear, nomeAssinante }) => {
    const sigRef = useRef(null);
    return (
        <div className="modal-assinatura">
            <div className="modal-content">
                <p>Por favor, assine acima da linha:</p>
                <div className="signing-area-container">
                    <SignatureCanvas
                        ref={sigRef}
                        penColor="black"
                        canvasProps={{ width: 400, height: 150, className: 'sigCanvas' }}
                        minWidth={0.5}
                        maxWidth={2.0}
                    />
                    <div className="signature-guide">
                        <span className="signature-guide-name">{nomeAssinante}</span>
                        <hr className="signature-guide-line" />
                    </div>
                </div>
                <div className="modal-botoes">
                    <button onClick={() => onConfirm(sigRef.current)}>Adicionar</button>
                    <button onClick={() => sigRef.current.clear()}>Limpar</button>
                    <button onClick={onClear}>Fechar</button>
                </div>
            </div>
        </div>
    );
};


const ContratoPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    
    const cliente = location.state?.cliente;
    const anexos = location.state?.anexos || [];

    const [loading, setLoading] = useState(false);
    const [assinaturas, setAssinaturas] = useState({ cliente: null, vendedor: null, testemunha1: null, testemunha2: null });
    const [modalVisible, setModalVisible] = useState(false);
    const [assinaturaAtiva, setAssinaturaAtiva] = useState(null);
    const [anexoPreviews, setAnexoPreviews] = useState([]);

    useEffect(() => {
        if (anexos && anexos.length > 0) {
            const previewUrls = anexos.map(file => URL.createObjectURL(file));
            setAnexoPreviews(previewUrls);
            return () => {
                previewUrls.forEach(url => URL.revokeObjectURL(url));
            };
        }
    }, [anexos]);

    const abrirModalAssinatura = (tipo) => {
        setAssinaturaAtiva(tipo);
        setModalVisible(true);
    };

    const handleConfirmarAssinatura = (sigRef) => {
        if (sigRef.isEmpty()) {
            setModalVisible(false);
            return;
        }
        const dataUrl = sigRef.getTrimmedCanvas().toDataURL('image/png');
        setAssinaturas(prev => ({ ...prev, [assinaturaAtiva]: dataUrl }));
        setModalVisible(false);
    };
    
    const handleFecharModal = () => setModalVisible(false);

    const handleSalvarContrato = async () => {
        if (!assinaturas.cliente) {
            alert("A assinatura do cliente é obrigatória.");
            return;
        }
        setLoading(true);
        const formData = new FormData();
        formData.append('cliente_id', cliente.id);
        if (assinaturas.cliente) formData.append('assinatura_cliente', dataURLtoBlob(assinaturas.cliente), 'ass_cliente.png');
        if (assinaturas.vendedor) formData.append('assinatura_vendedor', dataURLtoBlob(assinaturas.vendedor), 'ass_vendedor.png');
        if (assinaturas.testemunha1) formData.append('assinatura_testemunha1', dataURLtoBlob(assinaturas.testemunha1), 'ass_test1.png');
        if (assinaturas.testemunha2) formData.append('assinatura_testemunha2', dataURLtoBlob(assinaturas.testemunha2), 'ass_test2.png');
        
        anexos.forEach((file, index) => {
            formData.append('anexos', file, `anexo_${index + 1}.png`);
        });
        
        try {
            const result = await gerarContrato(formData);
            if (result && result.contrato_url) {
                alert("Contrato gerado com sucesso!");
                window.open(`http://localhost:8000${result.contrato_url}`, '_blank');
                sessionStorage.removeItem(`anexosOk_${cliente.id}`);
                navigate('/');
            } else {
                throw new Error("O servidor não retornou uma URL de contrato válida.");
            }
        } catch (error) {
            alert(`Falha ao gerar o contrato: ${error.message}`);
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    if (!cliente) return <div>Cliente não encontrado. Volte e consulte novamente.</div>;

    // Determina o nome a ser exibido no modal
    let nomeParaModal = "Assinatura";
    if (assinaturaAtiva === 'cliente') {
        nomeParaModal = cliente.nome_comprador;
    } else if (assinaturaAtiva) {
        nomeParaModal = assinaturaAtiva.charAt(0).toUpperCase() + assinaturaAtiva.slice(1);
    }
    
    const renderLinhaAssinatura = (tipo, nome, rg = false) => (
        <div className="linha-assinatura" onClick={() => abrirModalAssinatura(tipo)}>
            <div className="assinatura-imagem-container">
                {assinaturas[tipo] ? <img src={assinaturas[tipo]} alt={`Assinatura ${nome}`} /> : <div className="placeholder-assinatura">Clique para assinar</div>}
            </div>
            <div className="nome-assinatura">
                <p>{nome}</p>
                {rg && <p>R.G:</p>}
            </div>
        </div>
    );
    
    return (
        <div className="container-contrato">
            <div className="contrato-header">
                <button onClick={handleSalvarContrato} disabled={loading} className="gerar-btn">
                    {loading ? "Salvando..." : "Salvar e Gerar Contrato"}
                </button>
            </div>

            {modalVisible && <SignatureModal onConfirm={handleConfirmarAssinatura} onClear={handleFecharModal} nomeAssinante={nomeParaModal} />}

            <div className="folha-sulfite">
                <div className="watermark">COMETA</div>
                <div className="cabecalho-contrato">
                    <img src="https://lojascometa.com.br/i/logo_02_img_1@2x.png" alt="Logo" className="logo-contrato"/>
                    <h4>INSTRUMENTO PARTICULAR DE CONTRATO DE COMPRA E VENDA DE BENS DE CONSUMO COM ABERTURA DE CRÉDITO</h4>
                </div>
                
                <div className="corpo-contrato">
                    <p>
                        Pelo presente instrumento, de um lado, a <strong>{cliente.nome_filial}</strong>, inscrita no CNPJ <strong>{cliente.cnpj_filial}</strong>, estabelecida em <strong>{cliente.endereco_filial}</strong>, doravante denominada VENDEDORA, e de outro lado, <strong>{cliente.nome_comprador}</strong>, portador(a) do RG nº <strong>{cliente.rg}</strong> e do CPF nº <strong>{cliente.cpf}</strong>, residente no endereço <strong>{`${cliente.endereco}, ${cliente.numero}, ${cliente.cidade}`}</strong>, doravante denominado(a) COMPRADOR(A), celebram o presente contrato sob as seguintes cláusulas:
                    </p>
                    
                    <h5>1. DO OBJETO.</h5>
                    <p>1.1 O objeto do presente instrumento é abertura e concessão de crédito para futura aquisição de bens de consumo comercializados exclusivamente pela VENDEDORA, não sendo possível o uso do crédito concedido no presente contrato de qualquer outra forma. Os bens de consumo, comercializados pela VENDEDORA e doravante denominados MERCADORIAS, serão individualizados, descritos e precificados no(s) comprovante(s) de compra(s) devidamente assinado(s) pelo COMPRADOR(A) quando se der(em) a(s) sua(s) respetiva(s) aquisição(ões).</p>
                    <p>1.2 O COMPRADOR declara plena ciência e expressa concordância de que o(s) contrato(s) de compra e venda a serem firmados com base no crédito concedido por meio deste instrumento, o(s) qual(ais) será(ão) devidamente assinado(s) pelo COMPRADOR, mediante rubrica, conforme disposto no art. 784 do CPC, se constituirá em título executivo extrajudicial.</p>

                    <h5>2. DA CONCESSÃO E REVISÃO DO CRÉDITO</h5>
                    <p>2.1.  O(a) COMPRADOR(a) foi devidamente informado e declara plena ciência de que o crédito ora concedido somente poderá ser utilizado para aquisição de MERCADORIAS na própria loja VENDEDORA ora signatária, ou ainda, em qualquer uma das lojas cessionárias da marca VENDEDORA.</p>
                    <p>2.2. No momento da assinatura deste instrumento a VENDEDORA disponibiliza o(a) Comprador(a) o limite de crédito no importe de <strong>R$ {parseFloat(cliente.limite_credito).toFixed(2)}</strong> para aquisição parcelada dos bens de consumo na própria loja VENDEDORA ora signatária, ou ainda, em qualquer uma das lojas cessionárias da marca VENDEDORA.</p>
                    <p>2.3. O(a) COMPRADOR(a) declara ter sido cientificado que a concessão e manutenção de crédito é revisada com base na Política de Crédito vigente na empresa, conforme informações regulamente consultadas nos bureaus de crédito, e assim tanto a concessão quanto o limite descrito no item 2.3 será reavaliado a cada aquisição de MERCADORIAS.</p>
                    <p>2.4. Em cumprimento ao item acima, e visando a concessão e manutenção do de crediário de forma sustentável, o(a) COMPRADOR(A) reconhece que a VENDEDORA poderá revisar o crédito disponibilizado, em virtude da variação positiva ou negativa do histórico de crédito do(a) próprio(a) COMPRADOR(a), e por esse motivo,  o(a) COMPRADOR(A) autoriza a VENDEDORA a realizar análises periódicas do seu perfil de crédito , podendo aumento ou diminuir o valor disponibilizado. O (a) COMPRADOR(A) poderá revogar a autorização para aumento de valores disponibilizados, a qualquer momento, através de solicitação por escrito na loja VENDEDORA.</p>
                    <p>2.5. O(a) COMPRADOR(a)resta cientificado(a) que o não pagamento de qualquer parcela dos contatos de compra e venda na sua respectiva data de vencimento definida e discriminada nos comprovantes de compra, ou a inclusão do seu CPF em cadastro de inadimplente por qualquer credor terceiro, são motivos suficientes para a imediata suspensão da concessão de crédito.</p>

                    <h5>3. DA FORMA E CONDIÇÕES DE PAGAMENTO</h5>
                    <p>3.1 No ato da aquisição das MERCADORIAS (a) COMPRADOR(A) receberá comprovantes de compra (carnê), representativo de sua dívida, onde constará os valores devidos à VENDEDORA as respectivas datas de vencimentos, o qual integrará o presente contrato para todos os efeitos.</p>
                    <p>3.2. O(a) COMPRADOR(a)se obriga a pagar a quantia indicada no contrato de venda e compra e MERCADORIAS de consumo conforme parcelamento com valores definidos e datas de vencimento discriminadas nos comprovantes de compra, portanto, o(a) COMPRADOR(a) efetuará o pagamento das parcelas com valores e datas de vencimento definidos e discriminados nos comprovantes de compra (carnê).</p>
                    <p>3.3. O limite máximo de parcelas, o qual é sempre baseado no valor mínimo de cada parcela, será estabelecido pela política de crédito da empresa trimestralmente e sempre será divulgado de forma ampla e irrestrita pela VENDEDORA em suas propagandas, banners, outdoors, redes e mídias sociais de internet, e ainda, na própria sede da loja em cartazes de publicidade.</p>
                    <p>3.4. Dessa forma, o(a) COMPRADOR(A) resta cientificado que o valor mínimo da prestação poderá ser revisado, para mais ou para menos, cabendo a ele(a) observar o valor mínimo da prestação, no moldo item acima, antes da realização de qualquer aquisição de MERCADORIAS.</p>
                    
                    <h5>4. DO LOCAL DE PAGAMENTO</h5>
                    <p>4.1. Para que possa se valer de todas as modalidades de pagamento disponíveis (PIX, espécie, cartões de débito e crédito), (a) COMPRADOR(a) deverá efetuar os pagamentos das parcelas discriminadas nos comprovantes de compra na própria loja VENDEDORA em que foi realizada a aquisição dos bens os bens, cujo endereço está descrito no carnê de pagamentos. O (a) COMPRADOR(a) poderá efetuar o pagamento em loja VENDEDORA diversa da que foi realizada a aquisição dos MERCADORIAS, contudo, nessa hipótese não será possível a realização de pagamentos mediante o uso de cartões de crédito ou débito. Na hipótese de pagamento das mensalidades com cartão de crédito/débito serão acrescidas as taxas de administração das operadoras de cartão.</p>

                    <h5>5. DO VENCIMENTO ANTECIPADO</h5>
                    <p>5.1. O não pagamento de qualquer parcela na sua respectiva data de vencimento definida e discriminada nos comprovantes de compra por prazo superior a 30 (trinta) dias, conforme disposto no art. 394 do Código Civil, ocasionará, imediatamente, sem necessidade de qualquer notificação ou interpelação prévia, o vencimento antecipado de todas as parcelas vincendas à época do inadimplemento e a imediata execução do(s) contrato(s) de compra e venda a ser(em) firmado(s) com base no crédito concedido por meio deste instrumento.</p>

                    <h5>6. DA MULTA E DOS ENCARGOS DE MORA POR INADIMPLEMENTO</h5>
                    <p>6.1. Em caso de atraso ou não pagamento das prestações pactuadas o Comprador estará sujeito ao pagamento da multa única de 2% indicada no art. § 1°do art. 52 do CDC, além de encargos moratórios mensais/pro rata dia incidentes sobre o valor inadimplido, os quais serão expressamente indicados no (s) contrato(s) de compra e venda a ser(em) firmado(s) (carnês) com base no crédito concedido no momento da aquisição.</p>

                    <h5>7. DA INSCRIÇÃO EM CADASTROS DE CONTROLE DE CRÉDITO</h5>
                    <p>7.1. Além das penalidades acima descritas, em caso de inadimplemento das obrigações pactuadas, persistindo o inadimplemento de qualquer parcela do carnê por mais de 15 (quinze) dias, confere a VENDEDORA o direito potestativo de inscrever o(a) COMPRADOR(A) em cadastros de inadimplentes (bureaus de crédito), tais como SPC, SERASA, etc.</p>

                    <h5>8. DO FORNECIMENTO E DA AUTORIZAÇÃO PARA TRATAMENTO DOS DADOS</h5>
                    <p>8.1. O(a) COMPRADOR(A), declara e assume inteira responsabilidade pelos dados fornecidos, confirmando a veracidade das informações prestadas, comprometendo-se a informar a Vendedora toda e qualquer alteração no seu endereço comercial e ou residencial.</p>
                    <p>8.2. Declaro meu expresso CONSENTIMENTO para que a VENDEDORA torne-se controladora dos dados por mim cedidos através deste documento, nos termos do artigo 5º, VI, da Lei Geral de Proteção de Dados (LGPD), com o fito de instrumentalizar a execução do contrato de crediário dos futuros contratos de venda e compra a crediário por mim firmados com a controladora, para que esta tenha informações suficientes para cumprir com suas obrigações legais, os dados necessários para cumprimento das obrigações legais, assim como para a proteção ao crédito (Art.7º, II, V, X).</p>
                    <p>8.3. Ainda se destaca que estou ciente de que a controladora faz uso da marca VENDEDORA, de propriedade da  COMETA ADMINISTRAÇÃO EMPRESARIAL , inscrita no CNPJ sob o registro  12.532.642/0001-10 . Assim sendo, declaro plena ciência e acordo que os dados aqui tratados poderão ser compartilhados e utilizados, em todo ou em parte, com pessoas físicas ou jurídicas, departamentos internos, setores e empresas vinculadas e/ou associadas a  COMETA ADMINISTRAÇÃO EMPRESARIAL  e as outras empresas cessionárias das marcas VENDEDORA.</p>
                    <p>8.4. A VENDEDORA declara e cientifica a(o) COMPRADOR(A), portanto, que no tratamento dos dados pessoais, sempre que necessário, ela poderá compartilhar os dados pessoais com outras empresas cessionárias da marca VENDEDORA (que se obrigam a manter idêntico nível de segurança e privacidade), com prestadores de serviços de análises antifraude, intermediação de pagamentos, cobrança terceirizada, empresas de confecção de material e envio de correspondência, gestão de campanhas de marketing, enriquecimento de base de dados e armazenamento em nuvem, bem como, os órgãos reguladores. A VENDEDORA declara e cientifica o(a) COMPRADOR(A) que não efetua a comercialização de dados pessoais.</p>
                    <p>8.5. O(a) COMPRADOR(A) se compromete a manter seus dados sempre atualizados, e por esse motivo se compromete a informar todas as alterações em seu endereço residencial e profissional e dados eletrônicos. O(a) COMPRADOR(A) declara ter sido cientificado que em caso de não comunicação de alteração dos seus dados pessoais, considerar-se-á válida a notificação enviada ao endereço indicado pelo comprador no ato da assinatura do presente contrato, para o fim do que dispõe o artigo 43 parágrafo segundo do Código de Defesa do Consumidor.</p>

                    <h5>9. DAS CONDIÇÕES GERAIS</h5>
                    <p>9.1. As partes procurarão sempre o comum acordo para resolverem as pendências, lacunas e omissões que emergirem deste contrato.</p>
                    <p>9.2. Para dirimir as controvérsias e pendencias oriundas da aplicação deste contrato, fica eleito o foro da comarca do domicílio do(a) COMPRADOR(A).</p>
                    <p>E por estarem assim justos e contratados, assinam o presente instrumento em 02 (duas) vias, para que produza os jurídicos e legais efeitos, na presença de suas testemunhas.</p>
                    
                    <p>Obs. O presente contrato está registrado no Cartório de Títulos e Documentos da Comarca de {cliente.local_assinatura}.</p>

                    <p className="data-local">{`${cliente.local_assinatura}, ${new Date().toLocaleDateString('pt-BR')}`}</p>
                </div>
                
                <div className="area-assinaturas">
                    {renderLinhaAssinatura('cliente', `Comprador(a): ${cliente.nome_comprador}`)}
                    {renderLinhaAssinatura('testemunha1', 'Testemunha 1', true)}
                    {renderLinhaAssinatura('vendedor', 'Vendedor(a)')}
                    {renderLinhaAssinatura('testemunha2', 'Testemunha 2', true)}
                </div>

                {anexoPreviews.length > 0 && (
                    <div className="area-anexos">
                        <h3>Documentos Anexados</h3>
                        <div className="galeria-anexos">
                            {anexoPreviews.map((src, index) => (
                                <img key={index} src={src} alt={`Anexo ${index + 1}`} className="imagem-anexo" />
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ContratoPage;