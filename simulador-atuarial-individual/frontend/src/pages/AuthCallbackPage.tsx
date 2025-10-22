import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { saveAuthToken } from '../contexts/AuthContext';
import { LoadingSpinner } from '../design-system/components';

export function AuthCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const token = searchParams.get('token');

    if (token) {
      // Salvar token no localStorage
      saveAuthToken(token);

      // Redirecionar para o dashboard
      // Pequeno delay para garantir que o token foi salvo
      setTimeout(() => {
        navigate('/', { replace: true });
      }, 100);
    } else {
      // Se não há token, redirecionar para login
      navigate('/login', { replace: true });
    }
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <LoadingSpinner size="lg" />
        <p className="mt-4 text-gray-600">Finalizando autenticação...</p>
      </div>
    </div>
  );
}
