import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from '../components/Header';
import SideMenu from '../components/SideMenu';
import './MainLayout.css';

const MainLayout = ({ user, onLogout }) => {
    return (
        <div className="main-layout">
            <Header user={user} onLogout={onLogout} />
            <div className="layout-body">
                <SideMenu />
                <main className="layout-content">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};

export default MainLayout;
