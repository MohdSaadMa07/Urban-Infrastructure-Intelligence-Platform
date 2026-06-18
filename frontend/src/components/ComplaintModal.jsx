import React, { useState, useRef } from 'react';
import { 
  AlertCircle, Droplet, Waves, Trash2, Lightbulb, 
  Car, ClipboardList, Megaphone, MapPin, CheckCircle, 
  Map as MapIcon, Image as ImageIcon, X
} from 'lucide-react';

const CATEGORIES = [
  { value: 'pothole',     label: 'Potholes',      icon: <AlertCircle size={20} /> },
  { value: 'water',       label: 'Water Supply',  icon: <Droplet size={20} /> },
  { value: 'drainage',    label: 'Drainage',      icon: <Waves size={20} /> },
  { value: 'garbage',     label: 'Garbage',       icon: <Trash2 size={20} /> },
  { value: 'streetlight', label: 'Street Lights', icon: <Lightbulb size={20} /> },
  { value: 'road',        label: 'Roads',         icon: <Car size={20} /> },
  { value: 'other',       label: 'Other',         icon: <ClipboardList size={20} /> },
];

const WARDS = [
  'A', 'B', 'C', 'D', 'E', 'F/N', 'F/S', 'G/N', 'G/S', 
  'H/E', 'H/W', 'K/E', 'K/W', 'L', 'M/E', 'M/W', 'N', 
  'P/N', 'P/S', 'R/C', 'R/N', 'R/S', 'S', 'T'
];

const INITIAL_FORM = {
  category: '',
  description: '',
  latitude: '',
  longitude: '',
  wardHint: '',
  wardNo: '', // explicit ward selection
};

const ComplaintModal = ({ onClose }) => {
  const [form, setForm] = useState(INITIAL_FORM);
  const [locStatus, setLocStatus] = useState('idle'); // idle | loading | found | error
  const [submitStatus, setSubmitStatus] = useState('idle'); // idle | loading | success | error
  const [errorMsg, setErrorMsg] = useState('');
  const [successData, setSuccessData] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const fileInputRef = useRef(null);

  const handleCategorySelect = (val) => {
    setForm(f => ({ ...f, category: val }));
  };

  const handleImageSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      setErrorMsg('Image must be under 5MB.');
      return;
    }
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  };

  const handleRemoveImage = () => {
    setImageFile(null);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleLocate = () => {
    if (!navigator.geolocation) {
      setLocStatus('error');
      setErrorMsg('Geolocation is not supported by your browser.');
      return;
    }
    setLocStatus('loading');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        // Identify ward from backend
        fetch(`/api/identify-ward/?lat=${latitude}&lng=${longitude}`)
          .then(r => r.json())
          .then(data => {
            setForm(f => ({
              ...f,
              latitude: latitude.toFixed(6),
              longitude: longitude.toFixed(6),
              wardHint: data.ward_name ? `Ward ${data.ward_name}` : 'Unknown ward',
              wardNo: '', // clear manual selection if auto-detected
            }));
            setLocStatus('found');
          })
          .catch(() => {
            setForm(f => ({
              ...f,
              latitude: latitude.toFixed(6),
              longitude: longitude.toFixed(6),
              wardHint: 'Ward will be auto-detected',
              wardNo: '',
            }));
            setLocStatus('found');
          });
      },
      () => {
        setLocStatus('error');
        setErrorMsg('Unable to retrieve your location. Please allow location access.');
      }
    );
  };

  const handleWardChange = (e) => {
    const value = e.target.value;
    setForm(f => ({
      ...f,
      wardNo: value,
      // If user manually selects a ward, we clear the auto-detected location
      latitude: '',
      longitude: '',
      wardHint: '',
    }));
    if (value) {
      setLocStatus('idle'); // Reset location status if manual ward selected
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!form.category) { setErrorMsg('Please select a complaint category.'); return; }
    if (!form.description.trim()) { setErrorMsg('Please enter a description.'); return; }
    if (!form.wardNo && (!form.latitude || !form.longitude)) { 
      setErrorMsg('Please use "Detect Location" or select a ward manually.'); 
      return; 
    }

    setSubmitStatus('loading');

    try {
      const payload = new FormData();
      payload.append('category', form.category);
      payload.append('description', form.description);

      if (form.wardNo) {
        payload.append('ward_name', form.wardNo);
      } else {
        payload.append('latitude', String(parseFloat(form.latitude)));
        payload.append('longitude', String(parseFloat(form.longitude)));
      }

      if (imageFile) {
        payload.append('image', imageFile);
      }

      const res = await fetch('/api/complaints/submit/', {
        method: 'POST',
        body: payload,
      });
      const data = await res.json();
      if (res.ok) {
        setSuccessData(data);
        setSubmitStatus('success');
      } else {
        setErrorMsg(data.error || 'Submission failed. Please try again.');
        setSubmitStatus('error');
      }
    } catch {
      setErrorMsg('Network error. Please check your connection.');
      setSubmitStatus('error');
    }
  };

  const handleReset = () => {
    setForm(INITIAL_FORM);
    setLocStatus('idle');
    setSubmitStatus('idle');
    setErrorMsg('');
    setSuccessData(null);
    handleRemoveImage();
  };

  return (
    <>
      <div className="modal-overlay" onClick={onClose} />
      <div className="complaint-modal" role="dialog" aria-modal="true" aria-label="Report a Civic Issue">
        <button className="modal-close" onClick={onClose} id="modal-close-btn">&times;</button>
        {/* Success State */}
        {submitStatus === 'success' ? (
          <div className="modal-success">
            <div className="modal-success-icon" style={{ color: '#22c55e', marginBottom: '0.5rem' }}>
              <CheckCircle size={48} />
            </div>
            <h2>Complaint Submitted</h2>
            <p>
              Your <strong>{successData?.category}</strong> complaint in{' '}
              <strong>Ward {successData?.ward_name}</strong> has been filed.
            </p>
            <p className="modal-success-id">Reference ID: #{successData?.id}</p>
            {successData?.image && (
              <img
                src={successData.image}
                alt=""
                style={{ width: '100%', maxHeight: 200, objectFit: 'cover', borderRadius: 8, marginTop: '0.5rem', border: '1px solid rgba(99,102,241,0.15)' }}
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            )}
            <div className="modal-success-actions">
              <button className="btn-modal-primary" onClick={handleReset} id="submit-another-btn">
                Submit Another
              </button>
              <button className="btn-modal-ghost" onClick={onClose} id="close-after-success-btn">
                Close
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} noValidate>
            {/* Header */}
            <div className="modal-header">
              <div className="modal-badge" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <Megaphone size={14} /> Report an Issue
              </div>
              <h2 className="modal-title">Submit a Civic Complaint</h2>
              <p className="modal-subtitle">
                Your complaint will be geo-tagged and assigned to the correct ward automatically.
              </p>
            </div>

            {/* Category */}
            <div className="modal-section">
              <label className="modal-label">Category *</label>
              <div className="category-grid">
                {CATEGORIES.map(cat => (
                  <button
                    key={cat.value}
                    type="button"
                    id={`cat-${cat.value}`}
                    className={`category-btn ${form.category === cat.value ? 'category-btn-active' : ''}`}
                    onClick={() => handleCategorySelect(cat.value)}
                  >
                    <span className="cat-icon">{cat.icon}</span>
                    <span className="cat-label">{cat.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Description */}
            <div className="modal-section">
              <label className="modal-label" htmlFor="complaint-description">Description *</label>
              <textarea
                id="complaint-description"
                className="modal-textarea"
                placeholder="Describe the issue in detail -- location landmarks, severity, how long it's been present..."
                rows={4}
                value={form.description}
                onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              />
            </div>

            {/* Image Upload */}
            <div className="modal-section">
              <label className="modal-label">Photo (optional)</label>
              <div
                style={{
                  display: 'flex', alignItems: 'center', gap: '0.75rem',
                  background: 'rgba(15,23,42,0.6)', border: '1px dashed rgba(99,102,241,0.3)',
                  borderRadius: 10, padding: '0.75rem 1rem', cursor: 'pointer',
                  transition: 'border-color 0.2s',
                }}
                onClick={() => fileInputRef.current?.click()}
                onMouseEnter={e => e.currentTarget.style.borderColor = 'rgba(99,102,241,0.6)'}
                onMouseLeave={e => e.currentTarget.style.borderColor = 'rgba(99,102,241,0.3)'}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  style={{ display: 'none' }}
                  onChange={handleImageSelect}
                />
                {imagePreview ? (
                  <>
                    <div style={{ position: 'relative', width: 56, height: 56, flexShrink: 0 }}>
                      <img
                        src={imagePreview}
                        alt="Preview"
                        style={{ width: 56, height: 56, objectFit: 'cover', borderRadius: 8, border: '1px solid rgba(99,102,241,0.2)' }}
                      />
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); handleRemoveImage(); }}
                        style={{
                          position: 'absolute', top: -6, right: -6,
                          width: 20, height: 20, borderRadius: '50%', border: 'none',
                          background: '#ef4444', color: '#fff', cursor: 'pointer',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: 12,
                        }}
                      >
                        <X size={12} />
                      </button>
                    </div>
                    <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>{imageFile.name}</span>
                  </>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', width: '100%', justifyContent: 'center', padding: '0.25rem 0' }}>
                    <ImageIcon size={20} color="#818cf8" />
                    <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>Tap to add a photo of the issue</span>
                  </div>
                )}
              </div>
            </div>

            {/* Location / Ward Selection */}
            <div className="modal-section">
              <label className="modal-label">Location / Ward *</label>
              <div style={{ display: 'flex', gap: '0.5rem', flexDirection: 'column' }}>
                <button
                  type="button"
                  id="detect-location-btn"
                  className={`btn-locate ${locStatus === 'loading' ? 'btn-locate-loading' : ''}`}
                  onClick={handleLocate}
                  disabled={locStatus === 'loading'}
                  style={{ justifyContent: 'center' }}
                >
                  {locStatus === 'loading' && <span className="locate-spinner" />}
                  {locStatus === 'idle'    && <><MapPin size={16} /> Detect My Location</>}
                  {locStatus === 'loading' && 'Detecting...'}
                  {locStatus === 'found'   && <><MapPin size={16} /> {form.wardHint}</>}
                  {locStatus === 'error'   && <><MapPin size={16} /> Retry Location</>}
                </button>

                <div style={{ textAlign: 'center', color: '#64748b', fontSize: '0.75rem', margin: '0.2rem 0' }}>
                  OR
                </div>

                <div style={{ position: 'relative' }}>
                  <MapIcon size={16} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#818cf8' }} />
                  <select
                    className="modal-textarea"
                    style={{ paddingLeft: '2.5rem', cursor: 'pointer', appearance: 'none' }}
                    value={form.wardNo}
                    onChange={handleWardChange}
                  >
                    <option value="">Select a Ward Manually...</option>
                    {WARDS.map(w => (
                      <option key={w} value={w}>Ward {w}</option>
                    ))}
                  </select>
                </div>
              </div>

              {locStatus === 'found' && (
                <p className="locate-coords" style={{ textAlign: 'center' }}>
                  {form.latitude}, {form.longitude}
                </p>
              )}
            </div>

            {/* Error */}
            {errorMsg && (
              <div className="modal-error" role="alert">{errorMsg}</div>
            )}

            {/* Submit */}
            <button
              type="submit"
              id="complaint-submit-btn"
              className="btn-modal-primary"
              disabled={submitStatus === 'loading'}
            >
              {submitStatus === 'loading' ? 'Submitting...' : 'Submit Complaint'}
            </button>
          </form>
        )}
      </div>
    </>
  );
};

export default ComplaintModal;
