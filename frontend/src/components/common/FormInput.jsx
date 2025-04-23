import React, { forwardRef } from 'react';
import PropTypes from 'prop-types';

const FormInput = forwardRef(({
  id,
  label,
  type = 'text',
  placeholder,
  value,
  onChange,
  error,
  helperText,
  disabled = false,
  required = false,
  className = '',
  inputClassName = '',
  leftIcon,
  rightIcon,
  onLeftIconClick,
  onRightIconClick,
  size = 'medium',
  variant = 'default',
  ...props
}, ref) => {
  // Size classes
  const sizeClasses = {
    small: 'py-1.5 px-3 text-sm',
    medium: 'py-2 px-4',
    large: 'py-3 px-4 text-lg',
  };

  // Variant classes
  const variantClasses = {
    default: 'bg-white border border-gray-300 focus:border-primary-500 focus:ring focus:ring-primary-200',
    filled: 'bg-gray-100 border border-transparent focus:bg-white focus:border-primary-500',
    outlined: 'bg-transparent border border-gray-300 focus:border-primary-500 focus:ring focus:ring-primary-200',
  };

  // State classes
  const stateClasses = error
    ? 'border-red-500 focus:border-red-500 focus:ring-red-200'
    : disabled
      ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
      : '';

  // Icon positioning
  const hasLeftIcon = !!leftIcon;
  const hasRightIcon = !!rightIcon;
  const paddingLeftClass = hasLeftIcon ? 'pl-10' : '';
  const paddingRightClass = hasRightIcon ? 'pr-10' : '';

  return (
    <div className={`mb-4 ${className}`}>
      {label && (
        <label htmlFor={id} className="block text-gray-700 font-medium mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      <div className="relative">
        {hasLeftIcon && (
          <div 
            className={`absolute inset-y-0 left-0 flex items-center pl-3 ${onLeftIconClick ? 'cursor-pointer' : ''}`}
            onClick={onLeftIconClick}
          >
            {leftIcon}
          </div>
        )}
        
        <input
          ref={ref}
          id={id}
          type={type}
          value={value}
          onChange={onChange}
          disabled={disabled}
          placeholder={placeholder}
          required={required}
          className={`
            w-full rounded-lg focus:outline-none transition-colors
            ${sizeClasses[size] || sizeClasses.medium}
            ${variantClasses[variant] || variantClasses.default}
            ${stateClasses}
            ${paddingLeftClass}
            ${paddingRightClass}
            ${inputClassName}
          `}
          {...props}
        />
        
        {hasRightIcon && (
          <div 
            className={`absolute inset-y-0 right-0 flex items-center pr-3 ${onRightIconClick ? 'cursor-pointer' : ''}`}
            onClick={onRightIconClick}
          >
            {rightIcon}
          </div>
        )}
      </div>
      
      {(error || helperText) && (
        <div className={`mt-1 text-sm ${error ? 'text-red-500' : 'text-gray-500'}`}>
          {error || helperText}
        </div>
      )}
    </div>
  );
});

FormInput.displayName = 'FormInput';

FormInput.propTypes = {
  id: PropTypes.string.isRequired,
  label: PropTypes.string,
  type: PropTypes.string,
  placeholder: PropTypes.string,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onChange: PropTypes.func,
  error: PropTypes.string,
  helperText: PropTypes.string,
  disabled: PropTypes.bool,
  required: PropTypes.bool,
  className: PropTypes.string,
  inputClassName: PropTypes.string,
  leftIcon: PropTypes.node,
  rightIcon: PropTypes.node,
  onLeftIconClick: PropTypes.func,
  onRightIconClick: PropTypes.func,
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  variant: PropTypes.oneOf(['default', 'filled', 'outlined']),
};

export default FormInput;