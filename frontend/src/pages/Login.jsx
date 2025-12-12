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
      await authAPI.login(formData.email, formData.password);
      setMessage('Успішно ввійшли! Перенаправляємо...');
      // Сповіщаємо про зміну автентифікації
      window.dispatchEvent(new Event('auth-changed'));
      // Затримка для показу повідомлення
      setTimeout(() => {
        navigate('/', { replace: true });
      }, 1500);
    } catch (err) {
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Помилка входу. Перевірте email та пароль.');
      }
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
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

