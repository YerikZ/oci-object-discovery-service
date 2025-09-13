import React, { useState } from "react";

export default function SearchBar() {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [value, setValue] = useState(null);

  async function handleInput(e) {
    const q = e.target.value;
    setQuery(q);

    if (q.length < 1) {
      setSuggestions([]);
      return;
    }

    const res = await fetch(`/api/ui/search?q=${q}`);
    const data = await res.json();
    setSuggestions(data.keys || []);
  }

  async function selectKey(k) {
    const res = await fetch(`/api/ui/value/${k}`);
    const data = await res.json();
    setValue(data.value);
    setSuggestions([]);
    setQuery(k);
  }

  return (
    <div className="search-bar">
      <input
        type="text"
        placeholder="Search keys..."
        value={query}
        onChange={handleInput}
      />
      {suggestions.length > 0 && (
        <ul className="suggestions">
          {suggestions.map((k) => (
            <li key={k} onClick={() => selectKey(k)}>
              {k}
            </li>
          ))}
        </ul>
      )}
      {value && (
        <div className="value-box">
          <pre>{JSON.stringify(value, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
