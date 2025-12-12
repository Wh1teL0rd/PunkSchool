import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { authAPI } from '../api/auth';
import './Header.css';

function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchUser = async () => {
    setLoading(true);
    if (authAPI.isAuthenticated()) {
      try {
        const userData = await authAPI.getCurrentUser();
        setUser(userData);
      } catch (error) {
        authAPI.logout();
        setUser(null);
      }
    } else {
      setUser(null);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchUser();
  }, [location.pathname]);

  // Слухаємо події оновлення автентифікації
  useEffect(() => {
    const handleAuthChange = () => {
      fetchUser();
    };

    window.addEventListener('auth-changed', handleAuthChange);
    return () => {
      window.removeEventListener('auth-changed', handleAuthChange);
    };
  }, []);

  const handleLogout = () => {
    authAPI.logout();
    setUser(null);
    setShowDropdown(false);
    // Сповіщаємо про зміну автентифікації
    window.dispatchEvent(new Event('auth-changed'));
    navigate('/', { replace: true });
  };

  if (loading) {
    return (
      <header className="header">
        <div className="header-container">
          <Link to="/" className="logo">
            🎸 PunkSchool
          </Link>
          <nav className="nav">Завантаження...</nav>
        </div>
      </header>
    );
  }

  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="logo">
          🎸 PunkSchool
        </Link>
        <nav className="nav">
          {user ? (
            <div className="user-menu">
              <button
                className="user-button"
                onClick={() => setShowDropdown(!showDropdown)}
                onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
              >
                <span className="user-name">{user.full_name}</span>
                <span className="dropdown-arrow">▼</span>
              </button>
              {showDropdown && (
                <div className="dropdown-menu">
                  <div className="dropdown-item user-info-item">
                    <strong>{user.full_name}</strong>
                    <span className="user-email">{user.email}</span>
                    <span className="user-role">
                      {user.role === 'student' ? 'Студент' : 
                       user.role === 'teacher' ? 'Викладач' : 
                       'Адміністратор'}
                    </span>
                  </div>
                  <div className="dropdown-divider"></div>
                  <button
                    className="dropdown-item logout-item"
                    onClick={handleLogout}
                  >
                    Вийти з акаунту
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="auth-links">
              <Link to="/login" className="nav-link">
                Увійти
              </Link>
              <Link to="/register" className="nav-link nav-link-primary">
                Зареєструватися
              </Link>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Header;

