import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import ConsultaPage from './pages/ConsultaPage';
import AnexosPage from './pages/AnexosPage';
import ContratoPage from './pages/ContratoPage';
import VisualizarContratosPage from './pages/VisualizarContratosPage';

// Importa o novo layout principal
import MainLayout from './layouts/MainLayout';

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const loggedInUser = sessionStorage.getItem('user');
    if (loggedInUser) {
      setUser(JSON.parse(loggedInUser));
    }
  }, []);

  const handleLoginSuccess = (userData) => {
    // A API de login retorna um objeto aninhado
    const userToStore = userData.user || userData;
    sessionStorage.setItem('user', JSON.stringify(userToStore));
    setUser(userToStore);
  };

  const handleLogout = () => {
    sessionStorage.removeItem('user');
    setUser(null);
  };

  // Se não houver usuário logado, mostra apenas a página de login
  if (!user) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  // Se o usuário estiver logado, renderiza as rotas dentro do layout principal
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainLayout user={user} onLogout={handleLogout} />}>
          {/* As páginas abaixo serão renderizadas dentro do MainLayout */}
          <Route index element={<ConsultaPage />} />
          <Route path="visualizar" element={<VisualizarContratosPage />} />
          <Route path="anexos" element={<AnexosPage />} />
          <Route path="contrato" element={<ContratoPage />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;