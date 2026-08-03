import { useEffect, useState } from 'react';
import type { ApiResponse, HelloData } from '@app/shared';

export default function App() {
  const [result, setResult] = useState<ApiResponse<HelloData> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/project1/hello')
      .then((res) => res.json() as Promise<ApiResponse<HelloData>>)
      .then(setResult)
      .catch((err) => setError(String(err)));
  }, []);

  return (
    <main style={{ fontFamily: 'sans-serif', padding: 24 }}>
      <h1>Project 1</h1>
      <p>调用共用后端 GET /api/project1/hello 的结果：</p>
      {error && <pre style={{ color: 'red' }}>{error}</pre>}
      <pre>{result ? JSON.stringify(result, null, 2) : '加载中…'}</pre>
    </main>
  );
}
