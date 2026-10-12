import { ApiError } from './client';

/**
 * Turn an ApiError into { fieldErrors: {field: message}, message } for forms.
 * Handles the backend's VALIDATION_ERROR (pydantic loc list), CONFLICT
 * (details.field), and INVALID_REFERENCE (details.field) shapes.
 */
export function toFormErrors(err) {
  if (!(err instanceof ApiError)) {
    return { fieldErrors: {}, message: err?.message || 'Something went wrong.' };
  }

  const fieldErrors = {};
  let message = err.message;

  if (err.code === 'VALIDATION_ERROR' && Array.isArray(err.details?.errors)) {
    for (const e of err.details.errors) {
      // loc is like ["body", "field_name"]; take the last string segment.
      const loc = Array.isArray(e.loc) ? e.loc.filter(x => typeof x === 'string') : [];
      const field = loc[loc.length - 1];
      if (field && !fieldErrors[field]) fieldErrors[field] = e.msg || 'Invalid value';
    }
    message = 'Please fix the highlighted fields.';
  } else if ((err.code === 'CONFLICT' || err.code === 'INVALID_REFERENCE') && err.details?.field) {
    fieldErrors[err.details.field] = err.message;
  }

  if (err.requestId) message = `${message} (ref: ${err.requestId})`;
  return { fieldErrors, message };
}
