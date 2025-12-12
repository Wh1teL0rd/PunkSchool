import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../api/auth';
import './Register.css';

function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    bio: '',
    role: 'student',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Validate form
      if (!formData.email || !formData.password || !formData.full_name) {
        setError('Будь ласка, заповніть всі обов\'язкові поля');
        setLoading(false);
        return;
      }

      if (formData.password.length < 6) {
        setError('Пароль повинен містити мінімум 6 символів');
        setLoading(false);
        return;
      }

      // Register user
      await authAPI.register(
        {
          email: formData.email,
          password: formData.password,
          full_name: formData.full_name,
          bio: formData.bio || null,
        },
        formData.role
      );

      // After successful registration, login automatically
      try {
        await authAPI.login(formData.email, formData.password);
        navigate('/');
        // Сповіщаємо про зміну автентифікації після навігації
        setTimeout(() => {
          window.dispatchEvent(new Event('auth-changed'));
        }, 100);
      } catch (loginError) {
        // If auto-login fails, redirect to login page
        navigate('/login', { 
          state: { message: 'Реєстрація успішна! Будь ласка, увійдіть.' } 
        });
      }
    } catch (err) {
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.message) {
        setError(err.message);
      } else {
        setError('Помилка реєстрації. Спробуйте ще раз.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-container">
      <div className="register-card">
        <div className="register-header">
          <h1>🎵 Реєстрація</h1>
          <p>Створіть обліковий запис для навчання музиці</p>
        </div>

        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="register-form">
          <div className="form-group">
            <label htmlFor="full_name">Повне ім'я *</label>
            <input
              type="text"
              id="full_name"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              required
              placeholder="Введіть ваше повне ім'я"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email *</label>
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
            <label htmlFor="password">Пароль *</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              minLength={6}
              placeholder="Мінімум 6 символів"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="role">Я хочу бути *</label>
            <select
              id="role"
              name="role"
              value={formData.role}
              onChange={handleChange}
              required
              disabled={loading}
            >
              <option value="student">Студент</option>
              <option value="teacher">Викладач</option>
            </select>
          </div>

          {formData.role === 'teacher' && (
            <div className="form-group">
              <label htmlFor="bio">Біографія (опціонально)</label>
              <textarea
                id="bio"
                name="bio"
                value={formData.bio}
                onChange={handleChange}
                placeholder="Розкажіть про себе та ваш досвід викладання..."
                rows={4}
                disabled={loading}
              />
            </div>
          )}

          <button
            type="submit"
            className="submit-button"
            disabled={loading}
          >
            {loading ? 'Реєстрація...' : 'Зареєструватися'}
          </button>
        </form>

        <div className="register-footer">
          <p>
            Вже маєте обліковий запис?{' '}
            <Link to="/login" className="link">
              Увійти
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Register;

