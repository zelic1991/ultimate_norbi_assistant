/*
 * react_component.tsx – Minimale React-Komponente mit TypeScript.
 *
 * Dieses Template zeigt, wie ein funktionales React-Component geschrieben wird.
 * TailwindCSS und weitere Bibliotheken können bei Bedarf ergänzt werden.
 */
import React from 'react';

interface ExampleProps {
  title: string;
}

const ExampleComponent: React.FC<ExampleProps> = ({ title }) => {
  return (
    <div className="p-4 bg-white shadow rounded">
      <h1 className="text-xl font-semibold mb-2">{title}</h1>
      <p className="text-gray-700">Dies ist eine Beispielkomponente.</p>
    </div>
  );
};

export default ExampleComponent;
