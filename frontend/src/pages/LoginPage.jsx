import React, { useState } from 'react';
import { FaUser, FaLock, FaEye, FaEyeSlash } from 'react-icons/fa';
import './LoginPage.css';

// A função de login será importada do nosso serviço de API
import { login } from '../services/api';

const LoginPage = ({ onLoginSuccess }) => {
    const [user, setUser] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!user || !password) {
            setError('Usuário e senha são obrigatórios.');
            return;
        }
        setIsLoading(true);
        setError('');

        try {
            // Chama a nossa nova função de login no serviço de API
            const userData = await login(user, password);
            onLoginSuccess(userData); // Informa o App.jsx que o login foi bem-sucedido
        } catch (err) {
            setError(err.message || 'Falha na autenticação. Verifique suas credenciais.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="login-page-background">
            <div className="login-container-blur">
                <div className="login-branding-panel">
                    <img
                        src="https://lojascometa.com.br/i/logo_02_img_1@2x.png"
                        alt="Logo Lojas Cometa"
                        className="login-logo-main"
                    />
                    <h1>Bem-vindo!</h1>
                    <p>Sistema de Geração de Contratos.</p>
                </div>
                <div className="login-form-panel">
                    <h2>Acesse sua Conta</h2>
                    <form onSubmit={handleSubmit} className="login-form">
                        <div className="form-group">
                            <FaUser className="input-icon" />
                            <input
                                type="text"
                                id="user"
                                placeholder="Usuário"
                                value={user}
                                onChange={(e) => setUser(e.target.value)}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <FaLock className="input-icon" />
                            <input
                                type={showPassword ? 'text' : 'password'}
                                id="password"
                                placeholder="Senha"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                            <div className="password-toggle-icon" onClick={() => setShowPassword(!showPassword)}>
                                {showPassword ? <FaEyeSlash /> : <FaEye />}
                            </div>
                        </div>
                        {error && <p className="error-message">{error}</p>}
                        <button type="submit" className="login-button-main" disabled={isLoading}>
                            {isLoading ? 'Entrando...' : 'Login'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
