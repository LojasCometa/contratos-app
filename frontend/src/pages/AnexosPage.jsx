import React, { useState, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "./AnexosPage.css"; 

export default function AnexosPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const cliente = location.state?.cliente;

    // O estado agora guarda os objetos de Arquivo (File) completos
    const [arquivos, setArquivos] = useState([]); 
    const [previews, setPreviews] = useState([]);

    const fileInputRef = useRef(null);
    const cameraInputRef = useRef(null);

    const handleFileChange = (e) => {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;

        // Atualiza o estado local com os novos arquivos
        setArquivos(prev => [...prev, ...files]);
        
        // Cria URLs temporárias apenas para a pré-visualização
        const newPreviews = files.map(file => URL.createObjectURL(file));
        setPreviews(prev => [...prev, ...newPreviews]);
    };

    const handleVoltar = () => {
        // Sinaliza que os anexos estão OK para a ConsultaPage
        if (arquivos.length > 0 && cliente) {
            sessionStorage.setItem(`anexosOk_${cliente.id}`, "true");
        }
        // Volta para a página anterior, passando o cliente e os arquivos via estado
        navigate(-1, { state: { cliente, anexos: arquivos } });
    };

    if (!cliente) {
        return (
            <div className="container-consulta">
                <h2>Erro: Cliente não selecionado.</h2>
                <p>Por favor, volte e consulte um cliente primeiro.</p>
                <button onClick={() => navigate("/")}>Voltar para Consulta</button>
            </div>
        );
    }

    return (
        <div className="container-consulta">
            <header className="header-consulta">
                <div className="logo-area">
                    <img src="https://lojascometa.com.br/i/logo_02_img_1@2x.png" alt="Logo Cometa" />
                </div>
                <div className="titulo">
                    <h1>Anexar Documentos</h1>
                    <p style={{fontSize: '16px', color: '#666'}}>Cliente: <strong>{cliente.nome_comprador}</strong></p>
                </div>
                <div className="consulta-box">
                    <button onClick={handleVoltar}>Voltar e Confirmar</button>
                </div>
            </header>

            <div className="grid-anexos">
                <h2>Adicionar Documentos</h2>
                <div className="botoes-anexo">
                    <button onClick={() => fileInputRef.current.click()}>Importar Imagem</button>
                    <button onClick={() => cameraInputRef.current.click()}>Tirar Foto</button>
                </div>

                <input type="file" multiple accept="image/*" ref={fileInputRef} onChange={handleFileChange} style={{ display: 'none' }} />
                <input type="file" accept="image/*" capture="environment" ref={cameraInputRef} onChange={handleFileChange} style={{ display: 'none' }} />

                <div className="preview-grid">
                    {previews.map((src, idx) => (
                        <div key={idx} className="preview-item">
                            <img src={src} alt={`anexo-${idx}`} />
                            <p>{arquivos[idx]?.name}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}