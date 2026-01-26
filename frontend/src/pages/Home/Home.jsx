import React from 'react';
import { Link } from 'react-router-dom';
import Header from '../../components/Header';
import Footer from '../../components/Footer';
import towerIcon from '../../assests/icon/dark-tower-icon.png';
import spoilerIcon from '../../assests/icon/spoiler-icon.png';
import sourcesIcon from '../../assests/icon/sources-icon.png';
import './Home.css';

function Home() {
  return (
    <div className="page home-page">
      <div className="background-overlay"></div>
      <Header />
      
      <main className="home-content">
        <div className="hero-section">
          {/* Ka Wheel - spinning medieval wheel */}
          <div className="ka-wheel-container">
            <div className="ka-wheel">
              {/* Wheel spokes */}
              <div className="wheel-spoke"></div>
              <div className="wheel-spoke"></div>
              <div className="wheel-spoke"></div>
              <div className="wheel-spoke"></div>
              <div className="wheel-spoke"></div>
              <div className="wheel-spoke"></div>
              <div className="wheel-spoke"></div>
              <div className="wheel-spoke"></div>
              {/* Decorative elements */}
              <div className="wheel-outer-ring"></div>
              <div className="wheel-inner-ring"></div>
              <div className="wheel-studs">
                <span></span><span></span><span></span><span></span>
                <span></span><span></span><span></span><span></span>
              </div>
            </div>
            <div className="ka-text">Ka</div>
          </div>
          
          <h1 className="hero-title">KaGuide</h1>
          <p className="hero-subtitle">Your Guide Through The Dark Tower Universe</p>
          
          <p className="hero-description">
            "All things serve the Beam." <br/>
            Whether you're a first-time traveler on the Path of the Beam or a 
            seasoned gunslinger revisiting Mid-World, KaGuide is here to assist 
            your journey — without spoiling what lies ahead.
          </p>

          <div className="hero-features">
            <div className="feature-card">
              <img src={spoilerIcon} alt="Spoiler Protection" className="feature-icon" />
              <h3>Spoiler Protection</h3>
              <p>Set your reading progress and receive answers that respect your journey</p>
            </div>
            <div className="feature-card">
              <img src={sourcesIcon} alt="Deep Knowledge" className="feature-icon" />
              <h3>Deep Knowledge</h3>
              <p>Powered by comprehensive Dark Tower wiki data for accurate answers</p>
            </div>
            <div className="feature-card">
              <img src={towerIcon} alt="Immersive Experience" className="feature-icon" />
              <h3>Immersive Experience</h3>
              <p>Designed with the spirit of Mid-World to enhance your adventure</p>
            </div>
          </div>

          <Link to="/chat" className="cta-button">
            <span>Begin Your Journey</span>
            <span className="cta-arrow">→</span>
          </Link>

          <p className="hero-quote">
            "Go then, there are other worlds than these."
          </p>
        </div>
      </main>

      <Footer />
    </div>
  );
}

export default Home;
