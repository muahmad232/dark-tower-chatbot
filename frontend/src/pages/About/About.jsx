import React from 'react';
import Header from '../../components/Header';
import Footer from '../../components/Footer';
import towerIcon from '../../assests/icon/dark-tower-icon.png';
import spoilerIcon from '../../assests/icon/spoiler-icon.png';
import sourcesIcon from '../../assests/icon/sources-icon.png';
import './About.css';

function About() {
  return (
    <div className="page about-page">
      <div className="background-overlay"></div>
      <Header />
      
      <main className="about-content">
        <div className="about-container">
          <h1 className="about-title">About KaGuide</h1>
          
          <section className="about-section">
            <h2><img src={towerIcon} alt="Tower" className="section-icon" /> What is KaGuide?</h2>
            <p>
              KaGuide is an AI-powered companion designed for readers of Stephen King's 
              epic Dark Tower series. Built with love for the material and respect for 
              the reader's journey, KaGuide provides answers to your questions while 
              protecting you from spoilers.
            </p>
          </section>

          <section className="about-section">
            <h2><img src={spoilerIcon} alt="Spoiler" className="section-icon" /> Spoiler Protection</h2>
            <p>
              One of the greatest joys of reading the Dark Tower series is discovering 
              its mysteries organically. KaGuide understands this. Simply set which book 
              you've read up to, and the AI will carefully craft responses that don't 
              reveal plot points, character fates, or twists from later books.
            </p>
            <p>
              For veteran readers who've completed the journey to the Tower, enable 
              "Spoiler Mode" to discuss everything freely.
            </p>
          </section>

          <section className="about-section">
            <h2><img src={sourcesIcon} alt="Books" className="section-icon" /> The Dark Tower Series</h2>
            <div className="book-list">
              <div className="book-item">
                <span className="book-number">I</span>
                <span className="book-title">The Gunslinger (1982)</span>
              </div>
              <div className="book-item">
                <span className="book-number">II</span>
                <span className="book-title">The Drawing of the Three (1987)</span>
              </div>
              <div className="book-item">
                <span className="book-number">III</span>
                <span className="book-title">The Waste Lands (1991)</span>
              </div>
              <div className="book-item">
                <span className="book-number">IV</span>
                <span className="book-title">Wizard and Glass (1997)</span>
              </div>
              <div className="book-item">
                <span className="book-number">V</span>
                <span className="book-title">Wolves of the Calla (2003)</span>
              </div>
              <div className="book-item">
                <span className="book-number">VI</span>
                <span className="book-title">Song of Susannah (2004)</span>
              </div>
              <div className="book-item">
                <span className="book-number">VII</span>
                <span className="book-title">The Dark Tower (2004)</span>
              </div>
              <div className="book-item">
                <span className="book-number">IV.5</span>
                <span className="book-title">The Wind Through the Keyhole (2012)</span>
              </div>
            </div>
          </section>

          <section className="about-section">
            <h2>⚙️ How It Works</h2>
            <p>
              KaGuide uses Retrieval-Augmented Generation (RAG) technology. When you 
              ask a question, it searches through comprehensive Dark Tower wiki data 
              to find relevant information, then uses AI to craft a helpful, 
              contextual response in the spirit of Mid-World.
            </p>
            <ul className="tech-list">
              <li><strong>Knowledge Base:</strong> Dark Tower Wiki data (characters, places, events, items)</li>
              <li><strong>AI Model:</strong> Groq-powered LLM for fast, quality responses</li>
              <li><strong>Search:</strong> FAISS vector similarity for relevant context retrieval</li>
              <li><strong>Frontend:</strong> React with custom Dark Tower theming</li>
            </ul>
          </section>

          <section className="about-section">
            <h2>📜 Disclaimer</h2>
            <p className="disclaimer">
              KaGuide is a fan project and is not affiliated with Stephen King, 
              his publishers, or any official Dark Tower media. All Dark Tower content 
              belongs to Stephen King. This tool is made with appreciation for his work 
              and to help fellow Constant Readers on their journey.
            </p>
          </section>

          <div className="about-footer">
            <p>"Ka is a wheel."</p>
            <span>May you find your way to the Tower.</span>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

export default About;
