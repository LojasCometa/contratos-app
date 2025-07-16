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
    <div className="consulta-page-content">
        <div className="consulta-form-container">
            <h1>Gerar Novo Contrato</h1>
            <p>Insira o código do cliente para buscar os dados e iniciar a geração do contrato.</p>
            <div className="consulta-box">
                <input
                    type="text"
                    placeholder="Digite o código do cliente"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleConsultar()}
                />
                <button onClick={handleConsultar} disabled={loading}>
                    {loading ? "Consultando..." : "Consultar"}
                </button>
            </div>
        </div>

      {error && <div className="error-message">{error}</div>}

      {cliente && (
        <div className="grid-resultado">
          <h2>Dados do Cliente</h2>
          <table>
            <tbody>
              <tr><td><strong>Nome:</strong></td><td>{cliente.nome_comprador}</td></tr>
              <tr><td><strong>CPF:</strong></td><td>{cliente.cpf}</td></tr>
              <tr><td><strong>Endereço:</strong></td><td>{`${cliente.endereco}, ${cliente.numero} - ${cliente.cidade}`}</td></tr>
              <tr><td><strong>Limite de Crédito:</strong></td><td>R$ {parseFloat(cliente.limite_credito).toFixed(2)}</td></tr>
            </tbody>
          </table>
          <div className="botoes-acao">
            <button onClick={irParaAnexos} className="anexos-btn">
                Anexar Documentos
            </button>
            <button
              className="contrato-btn"
              onClick={irParaContrato}
              disabled={!anexosConfirmados}
            >
              Gerar Contrato
            </button>
          </div>
          {!anexosConfirmados && <p className="aviso-anexos">É necessário anexar os documentos para habilitar a geração do contrato.</p>}
        </div>
      )}
    </div>
  );
}
