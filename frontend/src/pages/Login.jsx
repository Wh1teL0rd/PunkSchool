import { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { authAPI } from '../api/auth';
import './Login.css';

function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check for message from navigation state
    if (location.state?.message) {
      setMessage(location.state.message);
    }
  }, [location]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (error) setError('');
    if (message) setMessage('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      // Спочатку перевіряємо доступність бекенду
      const isBackendAvailable = await authAPI.checkBackendHealth();
      if (!isBackendAvailable) {
        setError('Бекенд сервер недоступний. Перевірте, чи запущений сервер на http://localhost:8000');
        setLoading(false);
        return;
      }

      const response = await authAPI.login(formData.email, formData.password);
      console.log('Login: Login response:', response);
      console.log('Login: Token in localStorage:', localStorage.getItem('access_token')?.substring(0, 20) + '...');
      console.log('Login: isAuthenticated:', authAPI.isAuthenticated());
      setMessage('Успішно ввійшли! Перенаправляємо...');
      setLoading(false); // Скидаємо loading після успішного логіну
      // Затримка для показу повідомлення та збереження токену
      setTimeout(() => {
        // Перевіряємо, що токен все ще там
        const token = localStorage.getItem('access_token');
        console.log('Login: Before navigation, token exists:', !!token);
        navigate('/', { replace: true });
        // Сповіщаємо про зміну автентифікації після навігації
        setTimeout(() => {
          console.log('Login: Dispatching auth-changed event, token:', localStorage.getItem('access_token')?.substring(0, 20) + '...');
          window.dispatchEvent(new Event('auth-changed'));
        }, 300);
      }, 1500);
    } catch (err) {
      console.error('Login error:', err);
      // Відображаємо повідомлення про помилку
      const errorMessage = err.message || err.response?.data?.detail || 'Помилка входу. Перевірте email та пароль.';
      setError(errorMessage);
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <Link to="/" className="back-home-button" title="Повернутися на головну">
          ← На головну
        </Link>
        <div className="login-header">
          <h1>🎵 Вхід</h1>
          <p>Увійдіть до вашого облікового запису</p>
        </div>

        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}

        {message && (
          <div className="success-message" role="alert">
            {message}
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="example@email.com"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Пароль</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="Введіть пароль"
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="submit-button"
            disabled={loading}
          >
            {loading ? 'Вхід...' : 'Увійти'}
          </button>
        </form>

        <div className="login-footer">
          <p>
            Немає облікового запису?{' '}
            <Link to="/register" className="link">
              Зареєструватися
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;

