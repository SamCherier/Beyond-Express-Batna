import React from 'react';
import './GlitchLogo.css';

const GlitchLogo = ({ className = '', size = 'large' }) => {
  const sizeClasses = {
    small: 'h-8',
    medium: 'h-12',
    large: 'h-16',
    xlarge: 'h-24'
  };

  return (
    <div className={`glitch-container ${className}`}>
      <div className="glitch-wrapper">
        {/* Main logo */}
        <div className={`glitch-logo ${sizeClasses[size]}`}>
          <span className="text-gradient font-bold tracking-wider glitch-text" data-text="BEYOND EXPRESS">
            BEYOND EXPRESS
          </span>
        </div>
        
        {/* Glitch layers */}
        <div className={`glitch-logo glitch-layer-1 ${sizeClasses[size]}`} aria-hidden="true">
          <span className="text-gradient font-bold tracking-wider glitch-text" data-text="BEYOND EXPRESS">
            BEYOND EXPRESS
          </span>
        </div>
        
        <div className={`glitch-logo glitch-layer-2 ${sizeClasses[size]}`} aria-hidden="true">
          <span className="text-gradient font-bold tracking-wider glitch-text" data-text="BEYOND EXPRESS">
            BEYOND EXPRESS
          </span>
        </div>
      </div>
      
      {/* Scan line effect */}
      <div className="scan-line"></div>
    </div>
  );
};

export default GlitchLogo;
