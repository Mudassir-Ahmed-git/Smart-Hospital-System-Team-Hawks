export default function LoadingSpinner({ label = 'Loading' }) {
  return (
    <div role="status" className="flex items-center justify-center gap-3 p-10 text-teal">
      <span className="h-6 w-6 animate-spin rounded-full border-4 border-teal-soft border-t-teal" />
      <span className="font-bold">{label}</span>
    </div>
  );
}
