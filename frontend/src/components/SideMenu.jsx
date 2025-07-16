import React from 'react';
import { NavLink } from 'react-router-dom';
import { FaFileSignature, FaSearch } from 'react-icons/fa';
import './SideMenu.css';

const SideMenu = () => {
    return (
        <aside className="side-menu">
            <nav>
                <ul>
                    <li>
                        <NavLink to="/" end>
                            <FaFileSignature />
                            <span>Gerar Contrato</span>
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/visualizar">
                            <FaSearch />
                            <span>Visualizar Contratos</span>
                        </NavLink>
                    </li>
                </ul>
            </nav>
        </aside>
    );
};

export default SideMenu;
