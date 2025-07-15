
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const ClientePage = () => {
  const navigate = useNavigate();
  const [cpfOuCodigo, setCpfOuCodigo] = useState('');
  const [cliente, setCliente] = useState(null);
  const [erro, setErro] = useState('');

  const consultarCliente = async () => {
    try {
      setErro('');
      const response = await axios.get(`http://localhost:5000/api/clientes/${cpfOuCodigo}`);
      setCliente(response.data);
    } catch (error) {
      setCliente(null);
      setErro('Cliente não encontrado.');
    }
  };

  const gerarContrato = () => {
    if (cliente) {
      navigate('/contrato', { state: { cliente } });
    }
  };

  return (
    <div style={{ padding: '40px', fontFamily: 'Arial' }}>
      <h1 style={{ color: '#c00' }}>Contratos Cometa</h1>
      <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
        <input
          type="text"
          placeholder="Digite CPF ou Código"
          value={cpfOuCodigo}
          onChange={(e) => setCpfOuCodigo(e.target.value)}
          style={{ padding: 8, fontSize: 16 }}
        />
        <button onClick={consultarCliente} style={{ padding: '8px 16px' }}>Consultar</button>
      </div>

      {erro && <p style={{ color: 'red' }}>{erro}</p>}

      {cliente && (
        <div style={{ marginTop: 20, border: '1px solid #ccc', padding: 20, borderRadius: 6 }}>
          <p><strong>Nome:</strong> {cliente.nome}</p>
          <p><strong>CPF:</strong> {cliente.cpf}</p>
          <p><strong>RG:</strong> {cliente.rg}</p>
          <p><strong>Endereço:</strong> {cliente.endereco}</p>
          <p><strong>Limite de Crédito:</strong> R$ {cliente.limite_credito}</p>
          <button onClick={gerarContrato} style={{ marginTop: 20, padding: '10px 20px' }}>
            Gerar Contrato
          </button>
        </div>
      )}
    </div>
  );
};

export default ClientePage;
