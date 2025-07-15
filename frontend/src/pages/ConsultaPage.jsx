import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { consultarCliente } from "../services/api";
import "./ConsultaPage.css";

export default function ConsultaPage() {
  const navigate = useNavigate();
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [cliente, setCliente] = useState(() => {
    const saved = sessionStorage.getItem("clienteSelecionado");
    return saved ? JSON.parse(saved) : null;
  });
  const [anexosConfirmados, setAnexosConfirmados] = useState(false);

  useEffect(() => {
    if (cliente) {
      const anexosOk = sessionStorage.getItem(`anexosOk_${cliente.id}`) === "true";
      setAnexosConfirmados(anexosOk);
    } else {
      setAnexosConfirmados(false);
    }
  }, [cliente]);

  const handleConsultar = async () => {
    if (input.trim() === "") return;
    setLoading(true);
    setError("");
    setCliente(null);
    
    sessionStorage.removeItem("clienteSelecionado");
    Object.keys(sessionStorage).forEach(key => {
        if (key.startsWith("anexosOk_")) {
            sessionStorage.removeItem(key);
        }
    });

    try {
      const clienteData = await consultarCliente(input);
      const clienteCompleto = { ...clienteData, id: input };
      setCliente(clienteCompleto);
      sessionStorage.setItem("clienteSelecionado", JSON.stringify(clienteCompleto));
    } catch (err) {
      setError(err.message || "Cliente não encontrado.");
    } finally {
      setLoading(false);
    }
  };

  const irParaAnexos = () => {
    navigate("/anexos", { state: { cliente } });
  };

  const irParaContrato = () => {
    navigate("/contrato", { state: { cliente } });
  };

  return (
    <div className="container-consulta">
      <header className="header-consulta">
        <div className="logo-area">
          <img src="https://lojascometa.com.br/i/logo_02_img_1@2x.png" alt="Logo Cometa" />
        </div>
        
        {/* TÍTULO REMOVIDO CONFORME SOLICITADO */}

        <div className="consulta-box">
          <input
            type="text"
            placeholder="Digite o código do cliente"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button onClick={handleConsultar} disabled={loading}>
            {loading ? "Consultando..." : "Consultar"}
          </button>
        </div>
      </header>

      {error && <p className="error-message">{error}</p>}

      {cliente && (
        <div className="grid-resultado">
          <table>
            <tbody>
              <tr><td><strong>Nome:</strong></td><td>{cliente.nome_comprador}</td></tr>
              <tr><td><strong>CPF:</strong></td><td>{cliente.cpf}</td></tr>
              <tr><td><strong>Endereço:</strong></td><td>{`${cliente.endereco}, ${cliente.numero} - ${cliente.cidade}`}</td></tr>
              <tr><td><strong>Limite de Crédito:</strong></td><td>R$ {parseFloat(cliente.limite_credito).toFixed(2)}</td></tr>
            </tbody>
          </table>
          {/* DIV COM ESTILO PARA ADICIONAR ESPAÇAMENTO (PADDING) */}
          <div className="botoes-acao" style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
            <button onClick={irParaAnexos}>Enviar Anexos</button>
            <button
              style={{ backgroundColor: anexosConfirmados ? "red" : "grey" }}
              onClick={irParaContrato}
              disabled={!anexosConfirmados}
            >
              Gerar Contrato
            </button>
          </div>
          {!anexosConfirmados && <p className="aviso-anexos">É necessário enviar os anexos para poder gerar o contrato.</p>}
        </div>
      )}
    </div>
  );
}