import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../design-system/components';

export function LoginPage() {
  const { login, user, isLoading } = useAuth();
  const navigate = useNavigate();

  // Se já estiver autenticado (mock user em dev), redirecionar para home
  useEffect(() => {
    if (!isLoading && user) {
      navigate('/', { replace: true });
    }
  }, [user, isLoading, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          {/* Logo */}
          <div className="text-center mb-6">
            <img
              src="/logo.png"
              alt="PrevLab Logo"
              className="h-8 mx-auto mb-3"
            />
            <h1 className="text-2xl font-bold text-gray-900 mb-1">
              PrevLab
            </h1>
            <p className="text-sm text-gray-600">
              Plataforma de Simulação Atuarial
            </p>
          </div>

          {/* Divider */}
          <div className="border-t border-gray-200 my-6" />

          {/* Login Info */}
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Bem-vindo!
            </h2>
            <p className="text-gray-600 text-sm">
              Faça login com sua conta Google para acessar o simulador atuarial.
            </p>
          </div>

          {/* Google Login Button */}
          <Button
            onClick={login}
            className="w-full flex items-center justify-center gap-3 bg-white hover:bg-gray-50 text-gray-700 border-2 border-gray-300 font-medium py-3 px-4 rounded-lg transition-all shadow-sm hover:shadow-md"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            <span>Continuar com Google</span>
          </Button>

          {/* Info adicional */}
          <div className="mt-6 text-center text-xs text-gray-500">
            <p>
              Ao fazer login, você concorda com nossos{' '}
              <a href="#" className="text-blue-600 hover:underline">
                Termos de Uso
              </a>{' '}
              e{' '}
              <a href="#" className="text-blue-600 hover:underline">
                Política de Privacidade
              </a>
            </p>
          </div>
        </div>

        {/* Features */}
        <div className="mt-8 grid grid-cols-3 gap-4 text-center">
          <div className="bg-white rounded-lg p-4 shadow">
            <div className="text-2xl mb-2">📊</div>
            <p className="text-xs text-gray-600">Simulações Precisas</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow">
            <div className="text-2xl mb-2">🔒</div>
            <p className="text-xs text-gray-600">Dados Seguros</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow">
            <div className="text-2xl mb-2">⚡</div>
            <p className="text-xs text-gray-600">Resultados Rápidos</p>
          </div>
        </div>
      </div>
    </div>
  );
}
