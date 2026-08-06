import React, { useState } from 'react';
import '../styles/Header.css';

function Header() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="header">
      <div className="header-container">
        <div className="logo">
          <h2>📊 Portfolio Manager</h2>
        </div>

        <nav className="navbar">
          <ul className="nav-menu">
            <li><a href="/dashboard" className="nav-link">Dashboard</a></li>
            <li><a href="/portfolio" className="nav-link">Portfolio</a></li>
            <li><a href="/insights" className="nav-link">Insights</a></li>
            <li><a href="/recommendations" className="nav-link">Recommendations</a></li>
            <li className="nav-divider"></li>
            <li><a href="/profile" className="nav-link">Profile</a></li>
            <li><a href="/logout" className="nav-link logout">Logout</a></li>
          </ul>
        </nav>

        <button
          className="menu-toggle"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          ☰
        </button>
      </div>
    </header>
  );
}

export default Header;
