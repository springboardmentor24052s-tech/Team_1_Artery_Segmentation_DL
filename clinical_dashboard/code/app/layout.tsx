import type { Metadata } from 'next';
import './globals.css'; // Global styles

export const metadata: Metadata = {
  title: 'StenoVision - Artery Segmentation & Stenosis Detection',
  description: 'Academic medical imaging research project for coronary artery segmentation and stenosis detection.',
  icons: {
    icon: '/assets/aistudio/image_e2e52dea.png',
  },
  openGraph: {
    title: 'StenoVision - Artery Segmentation & Stenosis Detection',
    description: 'Academic medical imaging research project for coronary artery segmentation and stenosis detection.',
    type: 'website',
    images: ['/assets/aistudio/image_e2e52dea.png'],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'StenoVision - Artery Segmentation & Stenosis Detection',
    description: 'Academic medical imaging research project for coronary artery segmentation and stenosis detection.',
    images: ['/assets/aistudio/image_e2e52dea.png'],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body suppressHydrationWarning className="bg-slate-50 text-slate-900 font-sans antialiased selection:bg-[#A91121] selection:text-white">
        {children}
      </body>
    </html>
  );
}

