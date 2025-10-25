import React from 'react';
import './BeyondExpressLogo.css';

const BeyondExpressLogo = ({ size = 'md', className = '', variant = 'default' }) => {
  const sizes = {
    xs: 'w-8 h-8',
    sm: 'w-12 h-12',
    md: 'w-20 h-20',
    lg: 'w-32 h-32',
    xl: 'w-48 h-48'
  };

  const animationClasses = {
    default: 'beyond-logo-animated',
    header: 'beyond-logo-animated beyond-logo-header',
    hero: 'beyond-logo-animated beyond-logo-hero'
  };

  return (
    <div className={`beyond-logo-container ${sizes[size]} ${className}`} data-testid="beyond-express-logo">
      <img 
        src="/images/beyond-express-logo.jpg" 
        alt="Beyond Express Logo" 
        className={`w-full h-full object-contain ${animationClasses[variant]}`}
      />
    </div>
  );
};

export default BeyondExpressLogo;
