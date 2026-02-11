import React from 'react';
import './Navbar.css';

const Navbar = () => {
    return (
        <nav className="navbar">
            <div className="navbar-container">
                <div className="navbar-brand">
                    <div className="navbar-logo">📊</div>
                    <h1 className="navbar-title">LogAnalyser</h1>
                </div>
                <div className="navbar-actions">
                    {/* Future: Add user menu, settings, etc. */}
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
