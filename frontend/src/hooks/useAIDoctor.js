import { useState, useCallback } from 'react';

/**
 * useAIDoctor Hook
 * 
 * Provides AI-powered error handling with automatic interception
 * and smart retry functionality.
 */
export const useAIDoctor = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentError, setCurrentError] = useState(null);
  const [retryCallback, setRetryCallback] = useState(null);

  /**
   * Intercept an error and show the AI Doctor modal
   */
  const interceptError = useCallback((error, onRetry = null) => {
    setCurrentError(error);
    setRetryCallback(() => onRetry);
    setIsOpen(true);
  }, []);

  /**
   * Close the modal
   */
  const closeModal = useCallback(() => {
    setIsOpen(false);
    setCurrentError(null);
    setRetryCallback(null);
  }, []);

  /**
   * Execute retry callback
   */
  const handleRetry = useCallback(() => {
    if (retryCallback) {
      retryCallback();
    }
    closeModal();
  }, [retryCallback, closeModal]);

  /**
   * Wrap an async function with AI Doctor error handling
   */
  const withAIDoctor = useCallback((asyncFn, options = {}) => {
    return async (...args) => {
      try {
        return await asyncFn(...args);
      } catch (error) {
        console.error('AI Doctor intercepted error:', error);
        
        // Store the retry function
        const retry = () => asyncFn(...args);
        
        interceptError(error, retry);
        
        // If silent mode, don't throw
        if (options.silent) {
          return null;
        }
        
        throw error;
      }
    };
  }, [interceptError]);

  return {
    isOpen,
    currentError,
    interceptError,
    closeModal,
    handleRetry,
    withAIDoctor,
    // Convenience method for the modal props
    modalProps: {
      isOpen,
      error: currentError,
      onClose: closeModal,
      onRetry: handleRetry
    }
  };
};

export default useAIDoctor;
