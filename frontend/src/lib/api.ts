import { useCallback, useEffect, useState } from 'react'

export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export function getToken() {
  return localStorage.getItem('token') ?? ''
}

export function setToken(token: string) {
  if (token) localStorage.setItem('token', token)
  else localStorage.removeItem('token')
}

type Options = { method?: string; body?: unknown; form?: FormData }

export async function api<T = any>(path: string, options: Options = {}): Promise<T> {
  const headers: Record<string, string> = { Authorization: `Bearer ${getToken()}` }
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  const response = await fetch(API_URL + path, {
    method: options.method ?? (options.body !== undefined || options.form ? 'POST' : 'GET'),
    headers,
    body: options.form ?? (options.body !== undefined ? JSON.stringify(options.body) : undefined),
  })
  if (response.status === 401 && getToken()) {
    setToken('')
    window.location.href = '/login'
  }
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Something went wrong')
  return data
}

export function useLoad<T = any>(path: string | null, refreshSeconds = 0) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState('')

  const reload = useCallback(() => {
    if (!path) return Promise.resolve()
    return api<T>(path)
      .then((result) => {
        setData(result)
        setError('')
      })
      .catch((e) => setError(e.message))
  }, [path])

  useEffect(() => {
    reload()
    if (!refreshSeconds) return
    const timer = setInterval(reload, refreshSeconds * 1000)
    return () => clearInterval(timer)
  }, [reload, refreshSeconds])

  return { data, error, reload, loading: data === null && !error }
}
