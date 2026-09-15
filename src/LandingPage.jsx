import React from 'react';
import './LandingPage.css'; 

// Import logo assets from the assets folder
import opLogo from './assets/Seal_of_the_Office_of_the_President_of_the_Philippines.webp';
import gritLogo from './assets/grit-seal-light.png';
import ombLogo from './assets/Ombudsman_of_the_Philippines.png';

export default function LandingPage() {
  return (
    <div className="landing-container">
      
      {/* HEADER / HERO SECTION */}
      <header className="hero-section">
        <div className="auth-nav">
          <button className="btn-login">Log In</button>
          <button className="btn-signup">Sign Up</button>
        </div>
        
        <h1 className="hero-title">IMP</h1>
        
        <div className="logos-container">
          <div className="logo-circle">
            <img src={opLogo} alt="Office of the President Seal" />
          </div>
          <div className="logo-circle">
            <img src={gritLogo} alt="GRIT Logo" />
          </div>
          <div className="logo-circle">
            <img src={ombLogo} alt="Office of the Ombudsman Seal" />
          </div>
        </div>
      </header>

      {/* SECTION 1: What is IMP? */}
      <section className="zoom-section">
        <div className="bg-layer bg-malacanang"></div>
        <div className="overlay"></div>
        <div className="section-content">
          <h2>What is IMP?</h2>
          <p>
            The Integrity Management Program (IMP) is the national corruption prevention 
            framework of the Philippine government. It aims to institutionalize systemic 
            safeguards and promote a culture of integrity across all public institutions.
          </p>
        </div>
      </section>

      {/* SECTION 2: History of IMP */}
      <section className="zoom-section">
        <div className="bg-layer bg-ombudsman"></div>
        <div className="overlay"></div>
        <div className="section-content">
          <h2>Brief History of IMP</h2>
          <p>
            Initiated through Executive Order No. 176, s. 2014, the IMP unified previous 
            anti-corruption initiatives. Co-implemented by the Office of the President and 
            the Office of the Ombudsman, it established a standardized approach to assessing 
            and mitigating institutional vulnerabilities.
          </p>
        </div>
      </section>

      {/* SECTION 3: Moving Forward */}
      <section className="zoom-section">
        <div className="bg-layer bg-ncpag"></div>
        <div className="overlay"></div>
        <div className="section-content">
          <h2>Moving Forward</h2>
          <p>
            As public administration evolves, the IMP-CRA Portal digitizes the compliance 
            and assessment process. We are paving the way for data-driven risk management 
            and transparent governance.
          </p>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="landing-footer">
        <p>&copy; {new Date().getFullYear()} IMP-CRA Portal. All rights reserved.</p>
        <p style={{ marginTop: '8px' }}>Designed for robust digital governance and public accountability.</p>
      </footer>

    </div>
  );
}