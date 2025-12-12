import { Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import './Home.css';

function Home() {
  return (
    <div className="home-page">
      <Header />
      
      <main className="home-main">
        {/* Hero Section */}
        <section className="hero-section">
          <div className="hero-content">
            <h1 className="hero-title">🎸 PunkSchool</h1>
            <p className="hero-subtitle">Онлайн-школа музики нового покоління</p>
            <p className="hero-description">
              Навчайся музиці у найкращих викладачів України. Гітара, барабани, вокал, 
              клавішні та теорія музики - все в одному місці.
            </p>
            <div className="hero-buttons">
              <Link to="/register" className="btn btn-primary">
                Почати навчання
              </Link>
              <Link to="/courses" className="btn btn-secondary">
                Переглянути курси
              </Link>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="features-section">
          <div className="container">
            <h2 className="section-title">Чому обирають PunkSchool?</h2>
            <div className="features-grid">
              <div className="feature-card">
                <div className="feature-icon">🎯</div>
                <h3>Професійні викладачі</h3>
                <p>
                  Наші викладачі - це досвідчені музиканти з багаторічним досвідом 
                  викладання та виступів на сцені.
                </p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">📚</div>
                <h3>Структуровані курси</h3>
                <p>
                  Кожен курс розроблений за принципом від простого до складного, 
                  з чіткою структурою та практичними завданнями.
                </p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">🎥</div>
                <h3>Відео-уроки</h3>
                <p>
                  Високоякісні відео-уроки з можливістю перегляду в будь-який час 
                  та повторення складних моментів.
                </p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">🏆</div>
                <h3>Сертифікати</h3>
                <p>
                  Отримай сертифікат про завершення курсу, який підтверджує твої 
                  навички та знання.
                </p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">💬</div>
                <h3>Підтримка</h3>
                <p>
                  Отримуй зворотний зв'язок від викладачів та спілкуйся з іншими 
                  студентами на платформі.
                </p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">⚡</div>
                <h3>Гнучкий графік</h3>
                <p>
                  Навчайся у зручний для тебе час. Всі матеріали доступні 24/7, 
                  без прив'язки до розкладу.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Categories Section */}
        <section className="categories-section">
          <div className="container">
            <h2 className="section-title">Категорії курсів</h2>
            <div className="categories-grid">
              <div className="category-card">
                <div className="category-icon">🎸</div>
                <h3>Гітара</h3>
                <p>Від акустичної до електрогітари. Навчись грати свої улюблені пісні.</p>
              </div>
              <div className="category-card">
                <div className="category-icon">🥁</div>
                <h3>Барабани</h3>
                <p>Освої ритм та грув. Навчись грати на барабанах як професіонал.</p>
              </div>
              <div className="category-card">
                <div className="category-icon">🎤</div>
                <h3>Вокал</h3>
                <p>Розвини свій голос. Техніка дихання, діапазон та виразність.</p>
              </div>
              <div className="category-card">
                <div className="category-icon">🎹</div>
                <h3>Клавішні</h3>
                <p>Піаніно та синтезатор. Класика та сучасна музика.</p>
              </div>
              <div className="category-card">
                <div className="category-icon">📖</div>
                <h3>Теорія музики</h3>
                <p>Ноти, акорди, гармонія. Зрозумій музику зсередини.</p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="cta-section">
          <div className="container">
            <div className="cta-content">
              <h2>Готовий почати свою музичну подорож?</h2>
              <p>Приєднуйся до тисяч студентів, які вже навчаються в PunkSchool</p>
              <Link to="/register" className="btn btn-primary btn-large">
                Зареєструватися зараз
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

export default Home;
