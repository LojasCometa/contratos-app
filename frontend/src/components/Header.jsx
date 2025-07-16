import React from 'react';
import './Header.css';

const Header = ({ user, onLogout }) => {
    return (
        <header className="main-header">
            <div className="header-logo-container">
                <img src="https://lojascometa.com.br/i/logo_02_img_1@2x.png" alt="Logo Cometa" className="header-logo" />
            </div>
            <div className="header-user-info">
                <span>Usuário: <strong>{user.nome || 'Usuário'}</strong></span>
                <button onClick={onLogout} className="logout-button">Sair</button>
            </div>
        </header>
    );
};

export default Header;