'use client';
import { useState, FormEvent } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';

export default function Home() {
  const [isLogin, setIsLogin] = useState(true);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, register } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      if (isLogin) {
        await login(email, password);
        toast.success('Login successful!');
      } else {
        await register(name, email, password);
        toast.success('Registration successful!');
      }
      router.push('/dashboard');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Something went wrong');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0A0A0B]" style={{ fontFamily: "'DM Sans', sans-serif" }}>
      <div className="bg-[#0F0F10] p-8 rounded-2xl border border-[#1C1C1E] w-96">
        <h1 className="text-2xl font-bold text-center mb-6" style={{ color: '#E8E3D5' }}>
          {isLogin ? 'Welcome Back' : 'Create Account'}
        </h1>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <input
              type="text"
              placeholder="Full Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-[#0A0A0B] border border-[#2E2E30] p-3 rounded-lg text-sm outline-none"
              style={{ color: '#E8E3D5' }}
              required
            />
          )}
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-[#0A0A0B] border border-[#2E2E30] p-3 rounded-lg text-sm outline-none"
            style={{ color: '#E8E3D5' }}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-[#0A0A0B] border border-[#2E2E30] p-3 rounded-lg text-sm outline-none"
            style={{ color: '#E8E3D5' }}
            required
          />
          <button
            type="submit"
            className="w-full py-3 rounded-lg text-sm font-medium transition-all"
            style={{ background: '#E8E3D5', color: '#0A0A0B' }}
          >
            {isLogin ? 'Login' : 'Register'}
          </button>
        </form>

        <p className="text-center mt-4 text-sm" style={{ color: '#6B6760' }}>
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="hover:underline"
            style={{ color: '#E8E3D5' }}
          >
            {isLogin ? 'Register' : 'Login'}
          </button>
        </p>
      </div>
    </div>
  );
}