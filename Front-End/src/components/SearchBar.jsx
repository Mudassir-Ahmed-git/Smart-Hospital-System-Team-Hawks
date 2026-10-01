import { FaSearch } from 'react-icons/fa';

export default function SearchBar({ value, onChange, placeholder = 'Search hospitals or specialties' }) {
  return (
    <label className="relative block">
      <span className="sr-only">{placeholder}</span>
      <FaSearch aria-hidden className="absolute left-3 top-1/2 -translate-y-1/2 text-ink/50" />
      <input className="input pl-10" type="search" value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} />
    </label>
  );
}
