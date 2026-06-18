import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Hexagon, UserPlus, User, Lock, Mail, Phone, AlertCircle, ChevronDown, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const MUMBAI_WARDS = [
  'A', 'B', 'C', 'D', 'E', 'F/N', 'F/S', 'G/N', 'G/S',
  'H/E', 'H/W', 'K/E', 'K/W', 'L', 'M/E', 'M/W', 'N',
  'P/N', 'P/S', 'R/C', 'R/N', 'R/S', 'S', 'T',
];

const Signup = () => {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    password2: '',
    role: 'citizen',
    ward_name: '',
    phone: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const { username, email, password, password2, role, ward_name, phone } = form;

    if (!username.trim() || !password || !password2) {
      setError('Please fill in all required fields.');
      return;
    }
    if (password !== password2) {
      setError('Passwords do not match.');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    setLoading(true);
    try {
      const data = await register({
        username: username.trim(),
        email: email.trim() || undefined,
        password,
        password2,
        role,
        ward_name: ward_name || undefined,
        phone,
      });
      const userRole = data?.user?.profile?.role;
      if (userRole === 'councillor') {
        navigate('/councillor-portal', { replace: true });
      } else if (userRole === 'admin') {
        navigate('/admin-portal', { replace: true });
      } else {
        navigate('/', { replace: true });
      }
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    }
    setLoading(false);
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <Link to="/" className="auth-logo">
              <Hexagon size={32} color="#818cf8" />
              <span>UrbanIQ</span>
            </Link>
            <h1 className="auth-title">Create your account</h1>
            <p className="auth-subtitle">Join UrbanIQ to track civic issues in Mumbai</p>
          </div>

          {error && (
            <div className="auth-error">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="auth-form">
            {/* Role Selection */}
            <div className="auth-field">
              <label className="auth-label">I am a</label>
              <div className="auth-role-grid">
                {[
                  { value: 'citizen', label: 'Citizen', desc: 'Report & track issues' },
                  { value: 'councillor', label: 'Ward Councillor', desc: 'Manage ward complaints' },
                ].map(opt => (
                  <button
                    key={opt.value}
                    type="button"
                    className={`auth-role-btn ${form.role === opt.value ? 'auth-role-active' : ''}`}
                    onClick={() => setForm({ ...form, role: opt.value, ward_name: opt.value === 'citizen' ? '' : form.ward_name })}
                  >
                    <strong>{opt.label}</strong>
                    <span>{opt.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="auth-field">
              <label className="auth-label">
                <User size={14} /> Username <span className="auth-required">*</span>
              </label>
              <input
                type="text"
                name="username"
                placeholder="Choose a username"
                value={form.username}
                onChange={handleChange}
                className="auth-input"
                autoComplete="username"
              />
            </div>

            <div className="auth-field">
              <label className="auth-label">
                <Mail size={14} /> Email
              </label>
              <input
                type="email"
                name="email"
                placeholder="your@email.com (optional)"
                value={form.email}
                onChange={handleChange}
                className="auth-input"
                autoComplete="email"
              />
            </div>

            <div className="auth-field">
              <label className="auth-label">
                <Phone size={14} /> Phone
              </label>
              <input
                type="text"
                name="phone"
                placeholder="Phone number (optional)"
                value={form.phone}
                onChange={handleChange}
                className="auth-input"
              />
            </div>

            <div className="auth-field">
              <label className="auth-label">
                <Lock size={14} /> Password <span className="auth-required">*</span>
              </label>
              <div className="auth-input-wrapper">
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  placeholder="At least 6 characters"
                  value={form.password}
                  onChange={handleChange}
                  className="auth-input"
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="auth-toggle-pw"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div className="auth-field">
              <label className="auth-label">
                <Lock size={14} /> Confirm Password <span className="auth-required">*</span>
              </label>
              <input
                type="password"
                name="password2"
                placeholder="Repeat your password"
                value={form.password2}
                onChange={handleChange}
                className="auth-input"
                autoComplete="new-password"
              />
            </div>

            {/* Ward selector for councillors */}
            {form.role === 'councillor' && (
              <div className="auth-field">
                <label className="auth-label">Ward <span className="auth-required">*</span></label>
                <div className="auth-select-wrapper">
                  <select
                    name="ward_name"
                    value={form.ward_name}
                    onChange={handleChange}
                    className="auth-select"
                  >
                    <option value="">Select your ward...</option>
                    {MUMBAI_WARDS.map(w => (
                      <option key={w} value={w}>Ward {w}</option>
                    ))}
                  </select>
                  <ChevronDown size={16} className="auth-select-arrow" />
                </div>
              </div>
            )}

            <button type="submit" className="auth-submit" disabled={loading}>
              {loading ? <span className="auth-spinner" /> : <UserPlus size={18} />}
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <div className="auth-footer">
            <p>
              Already have an account?{' '}
              <Link to="/login" className="auth-link">Sign in</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Signup;
