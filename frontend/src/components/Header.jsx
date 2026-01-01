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
    const isAuth = authAPI.isAuthenticated();
    const token = localStorage.getItem('access_token');
    console.log('Header: Checking auth, isAuthenticated:', isAuth, 'Token exists:', !!token);
    
    if (isAuth && token) {
      setLoading(true);
      try {
        console.log('Header: Fetching user data with token:', token.substring(0, 20) + '...');
        const userData = await authAPI.getCurrentUser();
        console.log('Header: User data fetched successfully:', userData);
        setUser(userData);
      } catch (error) {
        console.error('Header: Error fetching user:', error);
        console.error('Header: Error response:', error.response?.data);
        console.error('Header: Error status:', error.response?.status);
        // Перевіряємо, чи токен все ще існує
        const tokenAfterError = localStorage.getItem('access_token');
        console.log('Header: Token after error:', tokenAfterError?.substring(0, 20) + '...');
        console.log('Header: Request headers:', error.config?.headers);
        
        // Видаляємо токен тільки якщо це точно 401 помилка (невалідний токен)
        // Але не видаляємо одразу - можливо це тимчасова помилка
        if (error.response?.status === 401) {
          // Даємо ще один шанс - можливо проблема в мережі або сервері
          console.log('Header: 401 error, but keeping token for now');
          // Не видаляємо токен одразу - можливо проблема на бекенді
          // authAPI.logout();
        }
        setUser(null);
      } finally {
        setLoading(false);
      }
    } else {
      setUser(null);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, [location.pathname]);

  // Додаткова перевірка при монтуванні
  useEffect(() => {
    fetchUser();
  }, []);

  // Слухаємо зміни в localStorage (для синхронізації між вкладками)
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'access_token') {
        fetchUser();
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  // Слухаємо події оновлення автентифікації
  useEffect(() => {
    const handleAuthChange = () => {
      // Невелика затримка, щоб переконатися, що токен збережений
      setTimeout(() => {
        fetchUser();
      }, 50);
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
          <Link to="/courses" className="nav-link">
            Курси
          </Link>
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
                  {user.role === 'student' && (
                    <Link
                      to="/dashboard/student"
                      className="dropdown-item"
                      onClick={() => setShowDropdown(false)}
                    >
                      Мій кабінет
                    </Link>
                  )}
                  {user.role === 'teacher' && (
                    <Link
                      to="/dashboard/teacher"
                      className="dropdown-item"
                      onClick={() => setShowDropdown(false)}
                    >
                      Кабінет викладача
                    </Link>
                  )}
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

