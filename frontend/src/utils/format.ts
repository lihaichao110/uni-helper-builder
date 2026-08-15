import dayjs from 'dayjs'

export const formatDate = (value?: string) =>
  value ? dayjs(value).format('YYYY-MM-DD HH:mm:ss') : '—'

export const bytes = (value: number) =>
  value > 1024 * 1024 ? `${(value / 1024 / 1024).toFixed(2)} MB` : `${(value / 1024).toFixed(1)} KB`
