/** "3 gün önce" türü göreli zaman (TR). */
export function timeAgo(iso: string): string {
  const d = new Date(iso)
  const s = Math.floor((Date.now() - d.getTime()) / 1000)
  const units: [number, string][] = [
    [60, 'saniye'],
    [3600, 'dakika'],
    [86400, 'saat'],
    [2592000, 'gün'],
    [31536000, 'ay'],
  ]
  if (s < 60) return 'az önce'
  for (let i = 1; i < units.length; i++) {
    const [limit, label] = units[i]
    if (s < limit) {
      const value = Math.floor(s / units[i - 1][0])
      return `${value} ${label} önce`
    }
  }
  return `${Math.floor(s / 31536000)} yıl önce`
}
