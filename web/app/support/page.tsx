import Image from "next/image";

export default function SupportPage() {
  return (
    <div className="mx-auto flex max-w-xl flex-col items-center px-6 pb-16 text-center">
      <h1 className="font-display text-4xl font-semibold text-pink">Support us</h1>
      <p className="mt-4 text-muted">
        Lutong BahAI is a prototype from Baura Co. If you want to support the
        project, scan the poster below.
      </p>
      <div className="mt-8 overflow-hidden rounded-3xl bg-white p-4 shadow-sm">
        <Image
          src="/pic/qr.png"
          alt="Lutong BahAI support poster with QR code"
          width={720}
          height={900}
          className="h-auto w-full"
        />
      </div>
    </div>
  );
}
