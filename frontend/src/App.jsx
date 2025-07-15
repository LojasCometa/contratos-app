import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ConsultaPage from './pages/ConsultaPage';
import AnexosPage from './pages/AnexosPage';
import ContratoPage from './pages/ContratoPage';
import VisualizarContratosPage from './pages/VisualizarContratosPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<ConsultaPage />} />
        <Route path="/anexos" element={<AnexosPage />} />
        <Route path="/contrato" element={<ContratoPage />} />
        <Route path="/visualizar" element={<VisualizarContratosPage />} />
      </Routes>
    </Router>
  );
}

export default App;
