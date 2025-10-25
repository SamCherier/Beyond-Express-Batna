import React from 'react';

const BeyondExpressLogo = ({ size = 'md', className = '' }) => {
  const sizes = {
    xs: 'w-8 h-8',
    sm: 'w-12 h-12',
    md: 'w-20 h-20',
    lg: 'w-32 h-32',
    xl: 'w-48 h-48'
  };

  return (
    <div className={`${sizes[size]} ${className}`} data-testid="beyond-express-logo">
      <img 
        src="/images/beyond-express-logo.jpg" 
        alt="Beyond Express Logo" 
        className="w-full h-full object-contain"
      />
    </div>
  );
};

export default BeyondExpressLogo;
