import { Link } from 'react-router-dom';
import './Footer.css';

function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-section">
          <h3 className="footer-logo">🎸 PunkSchool</h3>
          <p className="footer-description">
            Онлайн-школа музики для тих, хто хоче навчатися у найкращих викладачів.
            Гітара, барабани, вокал, клавішні та теорія музики.
          </p>
        </div>

        <div className="footer-section">
          <h4 className="footer-title">Навігація</h4>
          <ul className="footer-links">
            <li><Link to="/">Головна</Link></li>
            <li><Link to="/courses">Курси</Link></li>
            <li><Link to="/about">Про нас</Link></li>
            <li><Link to="/contact">Контакти</Link></li>
          </ul>
        </div>

        <div className="footer-section">
          <h4 className="footer-title">Категорії</h4>
          <ul className="footer-links">
            <li>Гітара</li>
            <li>Барабани</li>
            <li>Вокал</li>
            <li>Клавішні</li>
            <li>Теорія музики</li>
          </ul>
        </div>

        <div className="footer-section">
          <h4 className="footer-title">Контакти</h4>
          <ul className="footer-contact">
            <li>📧 info@punkschool.com</li>
            <li>📱 +380 (50) 111 22 33</li>
            <li>📍 Україна</li>
          </ul>
        </div>
      </div>

      <div className="footer-bottom">
        <p>&copy; 2025 PunkSchool by Oleh Zeilyk. Всі права захищені.</p>
      </div>
    </footer>
  );
}

export default Footer;

