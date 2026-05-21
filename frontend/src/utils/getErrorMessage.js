/** Extract a user-friendly error message from an API/network error. */
export function getErrorMessage(err, fallback = 'Something went wrong') {
  if (err?.response?.data?.error) {
    return err.response.data.error
  }
  if (err?.response?.data?.message) {
    return err.response.data.message
  }
  if (err?.response?.status === 500) {
    return err.response?.data?.error || 'Server error (500). Start backend: cd backend → python run.py'
  }
  if (err?.code === 'ERR_NETWORK' || err?.message === 'Network Error') {
    return 'Cannot connect to server. Start backend: cd backend → python run.py'
  }
  if (err?.message) {
    return err.message
  }
  return fallback
}
