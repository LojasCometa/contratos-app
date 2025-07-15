const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export async function consultarCliente(clienteId) {
    const response = await fetch(`${API_URL}/clientes/${clienteId}`);
    if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Cliente não encontrado');
    }
    return response.json();
}

export async function gerarContrato(formData) {
    const response = await fetch(`${API_URL}/gerar-contrato`, {
        method: "POST",
        body: formData,
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Falha ao gerar o contrato no servidor.');
    }
    return response.json();
}

export async function listarContratos() {
  const response = await fetch(`${API_URL}/contratos`);
    if (!response.ok) {
        throw new Error('Falha ao buscar a lista de contratos.');
    }
  return response.json();
}