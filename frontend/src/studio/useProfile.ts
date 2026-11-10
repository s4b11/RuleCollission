import { useLoad } from '../lib/api'

export type Profile = {
  id: string; slug: string; pack_id: string; web_link: string; name: string; prompt: string; greeting: string
  stt_provider: string; tts_provider: string; voice: string; identifier_label: string; second_factor_label: string
  max_attempts: number; phone_number: string; default_goal: string; enabled_tools: string[]
}

export function useProfile() {
  const { data, reload } = useLoad<Profile[]>('/studio/profiles')
  return { profile: data?.[0] ?? null, reload }
}
