import React, { useState } from "react";
import { listarContratos } from "../services/api";

export default function VisualizarContratosPage() {
  const [cpf, setCpf] = useState("");
  const [contratos, setContratos] = useState([]);

  const buscar = async () => {
    const todos = await listarContratos();
    const filtrados = todos.filter((url) => url.includes(cpf));
    setContratos(filtrados);
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Visualizar Contratos</h2>
      <input
        type="text"
        placeholder="Digite o CPF ou código"
        value={cpf}
        onChange={(e) => setCpf(e.target.value)}
      />
      <button onClick={buscar}>Buscar</button>
      <ul>
        {contratos.map((url) => (
          <li key={url}>
            <a href={`http://localhost:8000${url}`} target="_blank" rel="noreferrer">
              {url.split("/").pop()}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
