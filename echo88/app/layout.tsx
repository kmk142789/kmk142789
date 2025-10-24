import './globals.css'
import type { ReactNode } from 'react'

export const metadata = {
  title: 'Echo88 Vision',
  description: 'Visibility dashboard for Echo fragments and daily convergence logs.'
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
